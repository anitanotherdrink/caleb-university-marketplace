"""Catalog/discovery/image tests (PRD FR-006..010)."""
from __future__ import annotations

import struct

import pytest

from models.schemas import Condition, ProductCreate
from services import catalog
from services.errors import Forbidden, ImageRejected

# Minimal valid 1x1 PNG.
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
    b"\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _seller_and_category():
    from models.schemas import UserCreate
    from services import auth

    uid = auth.register(
        UserCreate(full_name="Sel Ler", email="seller@calebuniversity.edu.ng",
                   password="Str0ng#Pass1")
    )
    cat_id = catalog.list_categories()[0]["category_id"]
    return uid, cat_id


def _payload(cat_id, price="3500.00", qty=1, title="Used Calculus textbook"):
    return ProductCreate(
        title=title, description="Good condition", price=price,
        condition=Condition.used, quantity=qty, category_id=cat_id,
    )


def test_create_and_discover_listing():
    seller, cat = _seller_and_category()
    pid = catalog.create_listing(seller, _payload(cat), PNG_BYTES)
    results = catalog.search()
    assert any(r["product_id"] == pid for r in results)


def test_image_rejected_when_too_large():
    seller, cat = _seller_and_category()
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)
    with pytest.raises(ImageRejected):
        catalog.create_listing(seller, _payload(cat), big)


def test_image_rejected_when_not_an_image():
    seller, cat = _seller_and_category()
    fake = b"this is not an image, just text bytes"
    with pytest.raises(ImageRejected):
        catalog.create_listing(seller, _payload(cat), fake)


def test_non_positive_price_rejected():
    _, cat = _seller_and_category()
    with pytest.raises(Exception):
        _payload(cat, price="0")


def test_filters_combine():
    seller, cat = _seller_and_category()
    catalog.create_listing(seller, _payload(cat, price="1000.00", title="Cheap pen"),
                           PNG_BYTES)
    catalog.create_listing(seller, _payload(cat, price="9000.00", title="Pricey lamp"),
                           PNG_BYTES)
    res = catalog.search(keyword="pen", category_id=cat, price_min=500, price_max=2000)
    titles = [r["title"] for r in res]
    assert "Cheap pen" in titles and "Pricey lamp" not in titles


def test_only_owner_can_edit():
    seller, cat = _seller_and_category()
    pid = catalog.create_listing(seller, _payload(cat), PNG_BYTES)
    intruder = {"user_id": seller + 999, "role": "student"}
    with pytest.raises(Forbidden):
        catalog.update_listing(pid, intruder, _payload(cat))


def test_soft_delete_hides_from_discovery():
    seller, cat = _seller_and_category()
    pid = catalog.create_listing(seller, _payload(cat), PNG_BYTES)
    catalog.delete_listing(pid, {"user_id": seller, "role": "student"})
    assert all(r["product_id"] != pid for r in catalog.search())
