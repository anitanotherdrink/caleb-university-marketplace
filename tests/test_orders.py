"""Order placement + status lifecycle tests (PRD FR-011, FR-012)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from models.schemas import Condition, OrderItemIn, ProductCreate, UserCreate
from services import auth, catalog, orders
from services.errors import EmptyCart, Forbidden, IllegalTransition, Unavailable
from tests.test_catalog import PNG_BYTES


def _setup():
    seller = auth.register(
        UserCreate(full_name="Sel", email="seller@calebuniversity.edu.ng",
                   password="Str0ng#Pass1")
    )
    buyer = auth.register(
        UserCreate(full_name="Buy", email="buyer@calebuniversity.edu.ng",
                   password="Str0ng#Pass1")
    )
    cat = catalog.list_categories()[0]["category_id"]
    pid = catalog.create_listing(
        seller,
        ProductCreate(title="Used textbook", price="3500.00", condition=Condition.used,
                      quantity=2, category_id=cat),
        PNG_BYTES,
    )
    return seller, buyer, pid


def test_place_order_snapshots_price():
    seller, buyer, pid = _setup()
    result = orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    assert result["total"] == Decimal("3500.00")
    buyer_orders = orders.list_buyer_orders(buyer)
    assert buyer_orders[0]["status"] == "pending"
    assert buyer_orders[0]["items"][0]["price"] == Decimal("3500.00")


def test_price_snapshot_survives_listing_edit():
    seller, buyer, pid = _setup()
    orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    cat = catalog.list_categories()[0]["category_id"]
    catalog.update_listing(
        pid, {"user_id": seller, "role": "student"},
        ProductCreate(title="Used textbook", price="9999.00", condition=Condition.used,
                      quantity=5, category_id=cat),
    )
    assert orders.list_buyer_orders(buyer)[0]["items"][0]["price"] == Decimal("3500.00")


def test_empty_cart_rejected():
    with pytest.raises(EmptyCart):
        orders.place(1, [])


def test_quantity_above_availability_blocked():
    seller, buyer, pid = _setup()
    with pytest.raises(Unavailable):
        orders.place(buyer, [OrderItemIn(product_id=pid, quantity=99)])


def test_legal_transition_pending_to_confirmed_to_completed():
    seller, buyer, pid = _setup()
    o = orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    actor = {"user_id": seller, "role": "student"}
    orders.set_status(o["order_id"], "confirmed", actor)
    orders.set_status(o["order_id"], "completed", actor)
    assert orders.list_buyer_orders(buyer)[0]["status"] == "completed"


def test_illegal_transition_rejected():
    seller, buyer, pid = _setup()
    o = orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    actor = {"user_id": seller, "role": "student"}
    with pytest.raises(IllegalTransition):
        orders.set_status(o["order_id"], "completed", actor)  # skips confirmed


def test_non_seller_cannot_change_status():
    seller, buyer, pid = _setup()
    o = orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    with pytest.raises(Forbidden):
        orders.set_status(o["order_id"], "confirmed", {"user_id": buyer, "role": "student"})


def test_buyer_sees_only_own_orders():
    seller, buyer, pid = _setup()
    orders.place(buyer, [OrderItemIn(product_id=pid, quantity=1)])
    other = auth.register(
        UserCreate(full_name="Other", email="other@calebuniversity.edu.ng",
                   password="Str0ng#Pass1")
    )
    assert orders.list_buyer_orders(other) == []
