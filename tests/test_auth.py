"""Auth/registration/verification tests (PRD FR-001..004)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.schemas import UserCreate
from services import auth, security
from services.errors import BadCredentials, DuplicateEmail, NotVerified, RateLimited


def _valid_payload(email="ada.student@calebuniversity.edu.ng"):
    return UserCreate(
        full_name="Ada Student", email=email, password="Str0ng#Pass1", phone="08012345678"
    )


def test_institutional_domain_enforced():
    with pytest.raises(ValidationError):
        UserCreate(full_name="X", email="x@gmail.com", password="Str0ng#Pass1")


def test_weak_password_rejected():
    with pytest.raises(ValidationError):
        UserCreate(
            full_name="X", email="x@calebuniversity.edu.ng", password="alllowercase"
        )


def test_register_creates_unverified_user():
    uid = auth.register(_valid_payload())
    user = auth.get_user(uid)
    assert user["is_verified"] is False
    assert user["role"] == "student"


def test_duplicate_email_rejected():
    auth.register(_valid_payload())
    with pytest.raises(DuplicateEmail):
        auth.register(_valid_payload())


def test_login_blocked_until_verified():
    auth.register(_valid_payload())
    with pytest.raises(NotVerified):
        auth.login("ada.student@calebuniversity.edu.ng", "Str0ng#Pass1")


def test_full_verify_then_login_flow(monkeypatch):
    captured = {}

    def fake_send(to, token):
        captured["token"] = token
        return "url"

    monkeypatch.setattr(auth.email_service, "send_verification_email", fake_send)
    auth.register(_valid_payload())
    assert auth.verify(captured["token"]) is True
    result = auth.login("ada.student@calebuniversity.edu.ng", "Str0ng#Pass1")
    assert "token" in result
    assert security.validate_session(result["token"]) is not None


def test_bad_credentials_generic_error():
    with pytest.raises(BadCredentials):
        auth.login("nobody@calebuniversity.edu.ng", "whatever123!")


def test_login_rate_limited():
    for _ in range(5):
        with pytest.raises(BadCredentials):
            auth.login("ada.student@calebuniversity.edu.ng", "wrongpass1!")
    with pytest.raises(RateLimited):
        auth.login("ada.student@calebuniversity.edu.ng", "wrongpass1!")


def test_password_never_plaintext():
    uid = auth.register(_valid_payload())
    from services.db import session_scope
    from models.db_models import User

    with session_scope() as s:
        user = s.get(User, uid)
        assert user.password_hash != "Str0ng#Pass1"
        assert user.password_hash.startswith("$argon2")
