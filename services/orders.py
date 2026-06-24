"""Orders service: cart checkout + status lifecycle (PRD FR-011, FR-012)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from models.db_models import Order, OrderItem, Product
from models.schemas import OrderItemIn
from services import telemetry
from services.db import session_scope
from services.errors import EmptyCart, Forbidden, IllegalTransition, NotFound, Unavailable

# Legal status transitions (PRD FR-012). Terminal states map to empty sets.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def place(buyer_id: int, items: list[OrderItemIn]) -> dict:
    """Create one Order with snapshotted OrderItems. No funds move — payment is
    settled in person on campus (PRD FR-011, §2.2.5)."""
    if not items:
        raise EmptyCart("Your cart is empty.")
    telemetry.emit("checkout_started", item_count=len(items))
    with session_scope() as s:
        validated: list[tuple[Product, int]] = []
        total = Decimal("0")
        for it in items:
            p = s.get(Product, it.product_id)
            if not p or p.is_deleted or p.status != "available":
                telemetry.emit("checkout_blocked", reason="unavailable")
                raise Unavailable(
                    f"'{p.title if p else 'An item'}' is no longer available."
                )
            if it.quantity > p.quantity:
                telemetry.emit("checkout_blocked", reason="insufficient_quantity")
                raise Unavailable(f"Only {p.quantity} of '{p.title}' available.")
            validated.append((p, it.quantity))
            total += p.price * it.quantity

        order = Order(buyer_id=buyer_id, status="pending")
        s.add(order)
        s.flush()
        for p, qty in validated:
            s.add(
                OrderItem(
                    order_id=order.order_id,
                    product_id=p.product_id,
                    quantity=qty,
                    price=p.price,
                    title_snapshot=p.title,
                )
            )
            # Decrement availability; mark sold when depleted.
            p.quantity -= qty
            if p.quantity <= 0:
                p.status = "sold"
        order_id = order.order_id
    telemetry.emit(
        "order_placed", order_id=order_id, item_count=len(items), total=str(total)
    )
    return {"order_id": order_id, "total": total, "item_count": len(items)}


def set_status(order_id: int, new_status: str, actor: dict) -> None:
    """Seller (or admin) advances order status, enforcing the legal lifecycle."""
    with session_scope() as s:
        order = s.get(Order, order_id)
        if not order:
            raise NotFound("Order not found.")
        # Authorization: actor must own a listing in the order, or be admin.
        if actor["role"] != "admin":
            owns = any(
                item.product and item.product.seller_id == actor["user_id"]
                for item in order.items
            )
            if not owns:
                telemetry.emit("authz_denied", route="order_status", reason="not_seller")
                raise Forbidden("Only the seller can update this order.")
        if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
            telemetry.emit(
                "order_status_illegal", from_=order.status, to=new_status
            )
            raise IllegalTransition(
                f"Cannot move an order from {order.status} to {new_status}."
            )
        old = order.status
        order.status = new_status
        # On completion, depleted listings are already 'sold'; nothing more to do.
    telemetry.emit("order_status_changed", order_id=order_id, from_=old, to=new_status)


def _order_dict(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "buyer_id": order.buyer_id,
        "buyer_name": order.buyer.full_name if order.buyer else "",
        "status": order.status,
        "created_at": order.created_at,
        "items": [
            {
                "title": i.title_snapshot or (i.product.title if i.product else ""),
                "quantity": i.quantity,
                "price": i.price,
                "product_id": i.product_id,
                "seller_id": i.product.seller_id if i.product else None,
            }
            for i in order.items
        ],
        "total": sum((i.price * i.quantity for i in order.items), Decimal("0")),
    }


def list_buyer_orders(buyer_id: int) -> list[dict]:
    with session_scope() as s:
        q = (
            select(Order)
            .where(Order.buyer_id == buyer_id)
            .order_by(Order.created_at.desc())
        )
        out = [_order_dict(o) for o in s.scalars(q).all()]
    telemetry.emit("orders_viewed", role="buyer")
    return out


def list_seller_orders(seller_id: int) -> list[dict]:
    """Orders containing at least one of this seller's listings."""
    with session_scope() as s:
        orders = s.scalars(select(Order).order_by(Order.created_at.desc())).all()
        out = []
        for o in orders:
            if any(i.product and i.product.seller_id == seller_id for i in o.items):
                d = _order_dict(o)
                d["items"] = [
                    i for i in d["items"] if i["seller_id"] == seller_id
                ]
                out.append(d)
    telemetry.emit("orders_viewed", role="seller")
    return out
