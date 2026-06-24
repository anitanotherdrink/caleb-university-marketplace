"""Interaction tests: drive page button/form handlers via AppTest to catch bugs
in the on-click logic that render-only smoke tests miss."""
from __future__ import annotations

from streamlit.testing.v1 import AppTest

from models.schemas import Condition, OrderItemIn, ProductCreate, UserCreate
from services import auth, catalog, orders, security
from tests.test_catalog import PNG_BYTES


def _verified_student(email="buyer@calebuniversity.edu.ng"):
    uid = auth.register(UserCreate(full_name="Buy Er", email=email,
                                   password="Str0ng#Pass1"))
    auth.dev_autoverify(email)
    return uid, auth.get_user(uid), security.issue_session(uid)


def _seed_listing(seller_id):
    cat = catalog.list_categories()[0]["category_id"]
    return catalog.create_listing(
        seller_id,
        ProductCreate(title="Test Lamp", price="2500.00", condition=Condition.used,
                      quantity=3, category_id=cat),
        PNG_BYTES,
    )


def test_login_form_creates_session():
    auth.register(UserCreate(full_name="Log In", email="login@calebuniversity.edu.ng",
                             password="Str0ng#Pass1"))
    auth.dev_autoverify("login@calebuniversity.edu.ng")
    at = AppTest.from_file("pages/login.py", default_timeout=15).run()
    at.text_input[0].set_value("login@calebuniversity.edu.ng")
    at.text_input[1].set_value("Str0ng#Pass1")
    at.button[0].click().run()
    assert not at.exception
    assert "auth_user" in at.session_state


def test_browse_apply_filters():
    uid, user, token = _verified_student("br@calebuniversity.edu.ng")
    _seed_listing(uid)
    at = AppTest.from_file("pages/browse.py", default_timeout=15)
    at.session_state["auth_user"] = user
    at.session_state["auth_session_token"] = token
    at.run()
    at.text_input[0].set_value("Lamp")
    # Click the "Apply filters" form submit button.
    at.button[0].click().run()
    assert not at.exception


def test_cart_place_order():
    uid, user, token = _verified_student("cart@calebuniversity.edu.ng")
    seller, *_ = _verified_student("seller2@calebuniversity.edu.ng")
    pid = _seed_listing(seller)
    at = AppTest.from_file("pages/cart.py", default_timeout=15)
    at.session_state["auth_user"] = user
    at.session_state["auth_session_token"] = token
    at.session_state["cart_items"] = [
        {"product_id": pid, "title": "Test Lamp", "price": "2500.00",
         "quantity": 1, "max": 3}
    ]
    at.run()
    # The primary "Place order" button.
    place_btn = [b for b in at.button if "Place order" in b.label][0]
    place_btn.click().run()
    assert not at.exception
    assert orders.list_buyer_orders(uid), "order should have been created"


def test_seller_confirms_order():
    seller, seller_user, seller_token = _verified_student("s3@calebuniversity.edu.ng")
    buyer, *_ = _verified_student("b3@calebuniversity.edu.ng")
    pid = _seed_listing(seller)
    orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    at = AppTest.from_file("pages/my_orders.py", default_timeout=15)
    at.session_state["auth_user"] = seller_user
    at.session_state["auth_session_token"] = seller_token
    at.run()
    confirm = [b for b in at.button if b.label == "Confirmed"]
    assert confirm, "seller should see a Confirmed action"
    confirm[0].click().run()
    assert not at.exception
    assert orders.list_seller_orders(seller)[0]["status"] == "confirmed"


def test_admin_verifies_user():
    pending = auth.register(UserCreate(full_name="Pend Ing",
                                       email="pending@calebuniversity.edu.ng",
                                       password="Str0ng#Pass1"))
    from services.db import session_scope
    from models.db_models import User
    from sqlalchemy import select

    with session_scope() as s:
        admin = s.scalar(select(User).where(User.role == "admin"))
        admin_snap = {"user_id": admin.user_id, "full_name": admin.full_name,
                      "email": admin.email, "phone": None, "role": "admin",
                      "is_verified": True}
    at = AppTest.from_file("pages/admin_users.py", default_timeout=15)
    at.session_state["auth_user"] = admin_snap
    at.session_state["auth_session_token"] = security.issue_session(admin.user_id)
    at.run()
    verify_btns = [b for b in at.button if b.label == "Verify"]
    assert verify_btns, "admin should see a Verify action for the pending user"
    verify_btns[0].click().run()
    assert not at.exception
    assert auth.get_user(pending)["is_verified"] is True
