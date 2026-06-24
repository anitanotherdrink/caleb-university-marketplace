"""Administration service (PRD FR-014): users, categories, oversight."""
from __future__ import annotations

from sqlalchemy import func, select

from models.db_models import Category, Order, Product, User
from models.schemas import CategoryIn
from services import telemetry
from services.db import session_scope
from services.errors import Forbidden, InUse, NotFound


def _require_admin(actor: dict) -> None:
    if actor.get("role") != "admin":
        telemetry.emit("authz_denied", route="admin", reason="not_admin")
        raise Forbidden("Admins only.")


# --- Users -----------------------------------------------------------------
def list_users(actor: dict) -> list[dict]:
    _require_admin(actor)
    with session_scope() as s:
        rows = s.scalars(select(User).order_by(User.created_at.desc())).all()
        return [
            {
                "user_id": u.user_id,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "is_verified": u.is_verified,
                "is_active": u.is_active,
            }
            for u in rows
        ]


def set_verified(actor: dict, user_id: int, verified: bool) -> None:
    _require_admin(actor)
    with session_scope() as s:
        u = s.get(User, user_id)
        if not u:
            raise NotFound("User not found.")
        u.is_verified = verified
    telemetry.emit("admin_user_verified" if verified else "admin_user_unverified",
                   user_id=user_id)


def set_active(actor: dict, user_id: int, active: bool) -> None:
    _require_admin(actor)
    with session_scope() as s:
        u = s.get(User, user_id)
        if not u:
            raise NotFound("User not found.")
        if u.role == "admin" and not active:
            raise Forbidden("Cannot deactivate an admin account.")
        u.is_active = active
    if not active:
        telemetry.emit("admin_user_deactivated", user_id=user_id)


# --- Categories ------------------------------------------------------------
def create_category(actor: dict, payload: CategoryIn) -> None:
    _require_admin(actor)
    with session_scope() as s:
        if s.scalar(select(Category).where(Category.name == payload.name.strip())):
            raise InUse("A category with that name already exists.")
        s.add(Category(name=payload.name.strip(), description=payload.description))
    telemetry.emit("admin_category_changed", op="create")


def update_category(actor: dict, category_id: int, payload: CategoryIn) -> None:
    _require_admin(actor)
    with session_scope() as s:
        c = s.get(Category, category_id)
        if not c:
            raise NotFound("Category not found.")
        c.name = payload.name.strip()
        c.description = payload.description
    telemetry.emit("admin_category_changed", op="update")


def delete_category(actor: dict, category_id: int) -> None:
    _require_admin(actor)
    with session_scope() as s:
        c = s.get(Category, category_id)
        if not c:
            raise NotFound("Category not found.")
        in_use = s.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category_id, Product.is_deleted.is_(False))
        )
        if in_use:
            raise InUse(
                f"{in_use} listing(s) still use this category. Reassign them first."
            )
        s.delete(c)
    telemetry.emit("admin_category_changed", op="delete")


# --- Oversight -------------------------------------------------------------
def all_orders(actor: dict) -> list[dict]:
    _require_admin(actor)
    from services.orders import _order_dict

    with session_scope() as s:
        orders = s.scalars(select(Order).order_by(Order.created_at.desc())).all()
        return [_order_dict(o) for o in orders]


def metrics(actor: dict) -> dict:
    _require_admin(actor)
    with session_scope() as s:
        users = s.scalar(select(func.count()).select_from(User)) or 0
        verified = s.scalar(
            select(func.count()).select_from(User).where(User.is_verified.is_(True))
        ) or 0
        listings = s.scalar(
            select(func.count()).select_from(Product).where(Product.is_deleted.is_(False))
        ) or 0
        orders = s.scalar(select(func.count()).select_from(Order)) or 0
        return {
            "users": users,
            "verified": verified,
            "listings": listings,
            "orders": orders,
        }
