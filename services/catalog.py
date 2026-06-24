"""Catalog service: categories, listings CRUD, discovery, images
(PRD FR-006..010)."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from sqlalchemy import or_, select

import config
from models.db_models import Category, Product
from models.schemas import ProductCreate
from services import telemetry
from services.db import session_scope
from services.errors import Forbidden, ImageRejected, NotFound


# --- Categories ------------------------------------------------------------
def list_categories() -> list[dict]:
    with session_scope() as s:
        rows = s.scalars(select(Category).order_by(Category.name)).all()
        return [
            {"category_id": c.category_id, "name": c.name, "description": c.description}
            for c in rows
        ]


# --- Image handling (PRD FR-009) ------------------------------------------
def _sniff_mime(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(data: bytes) -> str:
    """Return the sniffed MIME or raise ImageRejected. Content-sniffs the bytes
    so a spoofed extension cannot smuggle a non-image (PRD FR-009.3)."""
    if len(data) > config.MAX_IMAGE_BYTES:
        telemetry.emit("image_rejected", reason="too_large", bytes=len(data))
        raise ImageRejected("That image is too large (max 5 MB).")
    mime = _sniff_mime(data)
    if mime not in config.ALLOWED_IMAGE_MIME:
        telemetry.emit("image_rejected", reason="bad_mime")
        raise ImageRejected("Only JPEG, PNG or WebP images are allowed.")
    return mime


_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _store_image(product_id: int, data: bytes, mime: str) -> str:
    folder = config.MEDIA_ROOT / str(product_id)
    folder.mkdir(parents=True, exist_ok=True)
    rel = Path(str(product_id)) / f"image{_EXT[mime]}"
    (config.MEDIA_ROOT / rel).write_bytes(data)
    telemetry.emit("image_uploaded", bytes=len(data), mime=mime)
    return str(rel)


def image_abs_path(rel: str | None) -> str | None:
    if not rel:
        return None
    p = config.MEDIA_ROOT / rel
    return str(p) if p.exists() else None


# --- Listings CRUD ---------------------------------------------------------
def create_listing(seller_id: int, payload: ProductCreate, image_bytes: bytes) -> int:
    mime = validate_image(image_bytes)  # validate before any write
    with session_scope() as s:
        if not s.get(Category, payload.category_id):
            raise NotFound("Selected category does not exist.")
        product = Product(
            seller_id=seller_id,
            category_id=payload.category_id,
            title=payload.title.strip(),
            description=payload.description,
            price=payload.price,
            condition=payload.condition.value,
            quantity=payload.quantity,
            status="available",
        )
        s.add(product)
        s.flush()
        product.image_path = _store_image(product.product_id, image_bytes, mime)
        pid = product.product_id
    telemetry.emit(
        "listing_created",
        category_id=payload.category_id,
        condition=payload.condition.value,
    )
    return pid


def update_listing(
    product_id: int,
    actor: dict,
    payload: ProductCreate,
    status: str | None = None,
    image_bytes: bytes | None = None,
) -> None:
    mime = validate_image(image_bytes) if image_bytes else None
    with session_scope() as s:
        product = s.get(Product, product_id)
        if not product or product.is_deleted:
            raise NotFound("Listing not found.")
        if actor["role"] != "admin" and product.seller_id != actor["user_id"]:
            telemetry.emit("listing_edit_forbidden", product_id=product_id)
            raise Forbidden("You can only edit your own listings.")
        old_status = product.status
        product.title = payload.title.strip()
        product.description = payload.description
        product.price = payload.price
        product.condition = payload.condition.value
        product.quantity = payload.quantity
        product.category_id = payload.category_id
        if status in {"available", "sold"}:
            product.status = status
        if image_bytes and mime:
            product.image_path = _store_image(product_id, image_bytes, mime)
    if status and status != old_status:
        telemetry.emit(
            "listing_status_changed", from_=old_status, to=status, product_id=product_id
        )
    telemetry.emit("listing_updated", product_id=product_id)


def delete_listing(product_id: int, actor: dict) -> None:
    """Soft-delete to preserve historical order references (PRD FR-008)."""
    with session_scope() as s:
        product = s.get(Product, product_id)
        if not product or product.is_deleted:
            raise NotFound("Listing not found.")
        if actor["role"] != "admin" and product.seller_id != actor["user_id"]:
            telemetry.emit("listing_delete_forbidden", product_id=product_id)
            raise Forbidden("You can only delete your own listings.")
        product.is_deleted = True
        product.status = "sold"
    telemetry.emit(
        "listing_deleted", mode="soft", moderated=(actor["role"] == "admin")
    )


# --- Discovery (PRD FR-010) ------------------------------------------------
def _to_dict(p: Product) -> dict:
    return {
        "product_id": p.product_id,
        "seller_id": p.seller_id,
        "seller_name": p.seller.full_name if p.seller else "",
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else "",
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "condition": p.condition,
        "quantity": p.quantity,
        "status": p.status,
        "image_path": p.image_path,
        "created_at": p.created_at,
    }


def search(
    keyword: str | None = None,
    category_id: int | None = None,
    price_min: Decimal | float | None = None,
    price_max: Decimal | float | None = None,
    include_sold: bool = False,
) -> list[dict]:
    with session_scope() as s:
        q = select(Product).where(Product.is_deleted.is_(False))
        if not include_sold:
            q = q.where(Product.status == "available")
        if keyword:
            like = f"%{keyword.strip()}%"
            q = q.where(or_(Product.title.ilike(like), Product.description.ilike(like)))
        if category_id:
            q = q.where(Product.category_id == category_id)
        if price_min is not None:
            q = q.where(Product.price >= Decimal(str(price_min)))
        if price_max is not None:
            q = q.where(Product.price <= Decimal(str(price_max)))
        q = q.order_by(Product.created_at.desc())
        results = [_to_dict(p) for p in s.scalars(q).all()]
    telemetry.emit(
        "search_performed",
        keyword_len=len(keyword or ""),
        category_id=category_id,
        price_min=price_min,
        price_max=price_max,
        result_count=len(results),
    )
    return results


def get_product(product_id: int) -> dict:
    with session_scope() as s:
        p = s.get(Product, product_id)
        if not p or p.is_deleted:
            raise NotFound("Listing not found.")
        telemetry.emit("listing_viewed", product_id=product_id)
        return _to_dict(p)


def list_seller_products(seller_id: int) -> list[dict]:
    with session_scope() as s:
        q = (
            select(Product)
            .where(Product.seller_id == seller_id, Product.is_deleted.is_(False))
            .order_by(Product.created_at.desc())
        )
        return [_to_dict(p) for p in s.scalars(q).all()]
