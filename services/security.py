"""Password hashing and signed session tokens (PRD §11.2).

Passwords are hashed with Argon2id and never stored or logged in plaintext
(PRD M5, §3.3.2(i)). Session tokens are HMAC-signed and carry the user id plus
issue/last-activity timestamps for idle + absolute timeout enforcement.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import config

_ph = PasswordHasher()


# --- Passwords -------------------------------------------------------------
def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _ph.check_needs_rehash(hashed)
    except Exception:
        return False


# --- Verification tokens (PRD FR-002) -------------------------------------
def generate_token() -> str:
    """Opaque token with >=128 bits of entropy."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# --- Signed session tokens (PRD FR-004) -----------------------------------
def _sign(payload_b64: str) -> str:
    sig = hmac.new(
        config.SESSION_SIGNING_KEY.encode(), payload_b64.encode(), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(sig).decode()


def issue_session(user_id: int) -> str:
    now = int(time.time())
    payload = {"uid": user_id, "iat": now, "last": now}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{payload_b64}.{_sign(payload_b64)}"


def _parse(token: str) -> dict | None:
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(payload_b64)):
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception:
        return None


def validate_session(token: str) -> int | None:
    """Return user_id if the token is valid and unexpired, else None."""
    data = _parse(token)
    if not data:
        return None
    now = int(time.time())
    if now - data["iat"] > config.SESSION_ABSOLUTE_TIMEOUT_H * 3600:
        return None
    if now - data["last"] > config.SESSION_IDLE_TIMEOUT_MIN * 60:
        return None
    return int(data["uid"])


def refresh_session(token: str) -> str | None:
    """Slide the idle window forward; returns a new token or None if invalid."""
    data = _parse(token)
    if not data:
        return None
    now = int(time.time())
    if now - data["iat"] > config.SESSION_ABSOLUTE_TIMEOUT_H * 3600:
        return None
    data["last"] = now
    payload_b64 = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    return f"{payload_b64}.{_sign(payload_b64)}"
