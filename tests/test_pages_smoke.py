"""Headless render smoke tests for every Streamlit page (PRD §9.9 E2E intent).

Uses Streamlit's AppTest to execute each page script in-process with a realistic
authenticated session, asserting no uncaught exception is raised on render. This
catches page-level bugs (bad st.* calls, NameErrors, template errors) that the
service-layer unit tests cannot see.
"""
from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from models.schemas import Condition, OrderItemIn, ProductCreate, UserCreate
from services import auth, catalog, orders, security
from tests.test_catalog import PNG_BYTES


def _student_session():
    uid = auth.register(
        UserCreate(full_name="Page Tester", email="tester@calebuniversity.edu.ng",
                   password="Str0ng#Pass1")
    )
    auth.dev_autoverify("tester@calebuniversity.edu.ng")
    user = auth.get_user(uid)
    cat = catalog.list_categories()[0]["category_id"]
    pid = catalog.create_listing(
        uid,
        ProductCreate(title="Test Lamp", price="2500.00", condition=Condition.used,
                      quantity=3, category_id=cat),
        PNG_BYTES,
    )
    return user, security.issue_session(uid), pid


def _admin_session():
    from services.db import session_scope
    from models.db_models import User
    from sqlalchemy import select

    with session_scope() as s:
        admin = s.scalar(select(User).where(User.role == "admin"))
        snap = {
            "user_id": admin.user_id, "full_name": admin.full_name,
            "email": admin.email, "phone": admin.phone, "role": "admin",
            "is_verified": True,
        }
    return snap, security.issue_session(snap["user_id"])


def _run(path: str, session_state: dict) -> AppTest:
    at = AppTest.from_file(path, default_timeout=15)
    for k, v in session_state.items():
        at.session_state[k] = v
    at.run()
    return at


STUDENT_PAGES = [
    "pages/browse.py",
    "pages/product_detail.py",
    "pages/cart.py",
    "pages/my_listings.py",
    "pages/listing_editor.py",
    "pages/my_orders.py",
    "pages/profile.py",
]


@pytest.mark.parametrize("page", STUDENT_PAGES)
def test_student_page_renders(page):
    user, token, pid = _student_session()
    state = {
        "auth_user": user,
        "auth_session_token": token,
        "cart_items": [
            {"product_id": pid, "title": "Test Lamp", "price": "2500.00",
             "quantity": 1, "max": 3}
        ],
        "viewing_product_id": pid,
        "editing_listing_id": pid,
    }
    at = _run(page, state)
    assert not at.exception, f"{page} raised: {at.exception}"


ADMIN_PAGES = [
    "pages/admin_users.py",
    "pages/admin_categories.py",
    "pages/admin_orders.py",
]


@pytest.mark.parametrize("page", ADMIN_PAGES)
def test_admin_page_renders(page):
    # Seed some content so oversight tables have rows.
    user, token, pid = _student_session()
    orders.place(user["user_id"], [OrderItemIn(product_id=pid, quantity=1)])
    admin_user, admin_token = _admin_session()
    at = _run(page, {"auth_user": admin_user, "auth_session_token": admin_token})
    assert not at.exception, f"{page} raised: {at.exception}"


PUBLIC_PAGES = ["pages/login.py", "pages/register.py", "pages/verify.py"]


@pytest.mark.parametrize("page", PUBLIC_PAGES)
def test_public_page_renders(page):
    at = _run(page, {})
    assert not at.exception, f"{page} raised: {at.exception}"
