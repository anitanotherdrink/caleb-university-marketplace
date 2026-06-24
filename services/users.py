"""Profile management (PRD FR-005). Email/role/verification are read-only."""
from __future__ import annotations

from sqlalchemy import select

from models.db_models import User
from models.schemas import ProfileUpdate
from services import telemetry
from services.db import session_scope
from services.errors import NotFound


def update_profile(user_id: int, payload: ProfileUpdate) -> dict:
    with session_scope() as s:
        user = s.get(User, user_id)
        if not user:
            raise NotFound("User not found.")
        user.full_name = payload.full_name.strip()
        user.phone = payload.phone
        snapshot = {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_verified": user.is_verified,
        }
    telemetry.emit("profile_updated", fields=["full_name", "phone"])
    return snapshot


def get_profile(user_id: int) -> dict:
    with session_scope() as s:
        user = s.scalar(select(User).where(User.user_id == user_id))
        if not user:
            raise NotFound("User not found.")
        telemetry.emit("profile_viewed")
        return {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_verified": user.is_verified,
        }
