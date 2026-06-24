"""Authentication & registration service (PRD FR-001..004)."""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from sqlalchemy import select

import config
from models.db_models import EmailVerificationToken, User
from models.schemas import UserCreate
from services import email as email_service
from services import security, telemetry
from services.db import session_scope
from services.errors import (
    BadCredentials,
    DuplicateEmail,
    NotFound,
    NotVerified,
    RateLimited,
    TokenExpired,
    TokenInvalid,
)

# In-memory login throttle (PRD FR-003). Per-process; adequate for this scale.
_failed: dict[str, list[float]] = {}


def _check_rate_limit(email: str) -> None:
    now = time.time()
    window = config.LOGIN_LOCKOUT_MIN * 60
    attempts = [t for t in _failed.get(email, []) if now - t < window]
    _failed[email] = attempts
    if len(attempts) >= config.LOGIN_MAX_ATTEMPTS:
        telemetry.emit("login_rate_limited", email=email)
        raise RateLimited(
            f"Too many attempts. Try again in {config.LOGIN_LOCKOUT_MIN} minutes."
        )


def _record_failure(email: str) -> None:
    _failed.setdefault(email, []).append(time.time())


def _clear_failures(email: str) -> None:
    _failed.pop(email, None)


# --- Registration / verification ------------------------------------------
def register(payload: UserCreate) -> int:
    """Create an unverified user and dispatch a verification email.

    Returns the new user_id. Raises DuplicateEmail on a taken address.
    (Pydantic has already enforced the institutional domain + password policy.)
    """
    telemetry.emit("registration_submitted", domain_valid=True)
    with session_scope() as s:
        existing = s.scalar(select(User).where(User.email == payload.email))
        if existing:
            telemetry.emit("registration_rejected", reason="duplicate_email")
            raise DuplicateEmail("This email is already registered.")
        user = User(
            full_name=payload.full_name.strip(),
            email=payload.email,
            password_hash=security.hash_password(payload.password),
            phone=payload.phone,
            role="student",
            is_verified=False,
        )
        s.add(user)
        s.flush()
        user_id = user.user_id
    _issue_and_send_token(user_id, payload.email)
    telemetry.emit("registration_succeeded")
    return user_id


def _issue_and_send_token(user_id: int, email: str) -> str:
    raw = security.generate_token()
    with session_scope() as s:
        # Invalidate prior unconsumed tokens (PRD §8.2 idempotency).
        for t in s.scalars(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.consumed_at.is_(None),
            )
        ):
            t.consumed_at = datetime.utcnow()
        s.add(
            EmailVerificationToken(
                user_id=user_id,
                token_hash=security.hash_token(raw),
                expires_at=datetime.utcnow() + timedelta(hours=config.TOKEN_TTL_HOURS),
            )
        )
    return email_service.send_verification_email(email, raw)


def resend_verification(email: str) -> str | None:
    email = email.lower()
    with session_scope() as s:
        user = s.scalar(select(User).where(User.email == email))
        if not user or user.is_verified:
            return None
        user_id = user.user_id
    telemetry.emit("verification_resent", email=email)
    return _issue_and_send_token(user_id, email)


def dev_autoverify(email: str) -> bool:
    """Dev-only convenience: verify an account without clicking the email link.

    Refuses when SMTP is configured (i.e. in any real deployment), so it cannot
    be used to bypass verification in production (PRD FR-002, §13.4 fallback)."""
    if config.smtp_configured():
        return False
    email = email.lower().strip()
    with session_scope() as s:
        user = s.scalar(select(User).where(User.email == email))
        if not user:
            return False
        user.is_verified = True
        for t in s.scalars(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.user_id,
                EmailVerificationToken.consumed_at.is_(None),
            )
        ):
            t.consumed_at = datetime.utcnow()
    telemetry.emit("verification_succeeded", mode="dev")
    return True


def verify(token: str) -> bool:
    """Consume a verification token and flip is_verified. Idempotent on
    already-verified accounts (PRD FR-002.3)."""
    token_hash = security.hash_token(token)
    with session_scope() as s:
        row = s.scalar(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        if not row:
            telemetry.emit("verification_failed", reason="invalid")
            raise TokenInvalid("This verification link is not valid.")
        user = s.get(User, row.user_id)
        if user and user.is_verified:
            return True  # idempotent success
        if row.consumed_at is not None:
            telemetry.emit("verification_failed", reason="consumed")
            raise TokenInvalid("This link has already been used.")
        if row.expires_at < datetime.utcnow():
            telemetry.emit("verification_token_expired")
            raise TokenExpired("This verification link has expired.")
        row.consumed_at = datetime.utcnow()
        if user:
            user.is_verified = True
    telemetry.emit("verification_succeeded")
    return True


# --- Login / logout --------------------------------------------------------
def login(email: str, password: str) -> dict:
    """Authenticate and return a session dict on success.

    Uses a generic failure message to avoid user enumeration (PRD FR-003).
    """
    email = (email or "").lower().strip()
    _check_rate_limit(email)
    with session_scope() as s:
        user = s.scalar(select(User).where(User.email == email))
        if not user or not user.is_active or not security.verify_password(
            password, user.password_hash
        ):
            _record_failure(email)
            telemetry.emit("login_failed", reason="bad_credentials")
            raise BadCredentials("Invalid email or password.")
        if not user.is_verified:
            telemetry.emit("login_failed", reason="not_verified")
            raise NotVerified("Please verify your institutional email first.")
        if security.needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)
        user.last_login = datetime.utcnow()
        session_token = security.issue_session(user.user_id)
        snapshot = _user_snapshot(user)
    _clear_failures(email)
    telemetry.emit("login_succeeded", user_id=snapshot["user_id"])
    return {"token": session_token, "user": snapshot}


def get_user(user_id: int) -> dict:
    with session_scope() as s:
        user = s.get(User, user_id)
        if not user:
            raise NotFound("User not found.")
        return _user_snapshot(user)


def _user_snapshot(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_verified": user.is_verified,
    }
