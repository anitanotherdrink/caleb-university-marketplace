"""Cart + simulated checkout (PRD FR-011)."""
from __future__ import annotations

from decimal import Decimal

import streamlit as st

from components import auth_gate
from components.ui import money
from models.schemas import OrderItemIn
from services import orders
from services.errors import EmptyCart, Unavailable

user = auth_gate.require_auth()

st.title("🛒 Your cart")

cart = st.session_state.setdefault("cart_items", [])

if "last_order" in st.session_state:
    order = st.session_state.pop("last_order")
    st.success(f"Order #{order['order_id']} placed — status: PENDING")
    for line in order["lines"]:
        st.write(f"- {line}")
    st.info(
        "ⓘ Payment is settled **in person on campus**. No money was transferred "
        "by the platform."
    )
    if st.button("🧾 View my orders", key="goto_orders"):
        st.switch_page("pages/my_orders.py")
    st.divider()

if not cart:
    st.info("Your cart is empty. Browse the marketplace to add items.")
    if st.button("Go to browse"):
        st.switch_page("pages/browse.py")
    st.stop()

total = Decimal("0")
for idx, item in enumerate(list(cart)):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.markdown(f"**{item['title']}**")
        new_qty = c2.number_input(
            "Qty",
            min_value=1,
            max_value=item["max"],
            value=item["quantity"],
            key=f"qty_{idx}",
        )
        item["quantity"] = int(new_qty)
        line_total = Decimal(str(item["price"])) * item["quantity"]
        total += line_total
        c3.markdown(money(line_total))
        if c4.button("✕", key=f"rm_{idx}"):
            cart.pop(idx)
            st.rerun()

st.markdown(f"## Total: {money(total)}")
st.caption("Payment happens in person on campus — checkout only records the order.")

if st.button("Place order (simulated checkout)", type="primary",
             width="stretch"):
    try:
        items = [OrderItemIn(product_id=c["product_id"], quantity=c["quantity"])
                 for c in cart]
        result = orders.place(user["user_id"], items)
        lines = [f"{c['quantity']} × \"{c['title']}\"  {money(Decimal(str(c['price'])) * c['quantity'])}"
                 for c in cart]
        st.session_state["last_order"] = {"order_id": result["order_id"], "lines": lines}
        st.session_state["cart_items"] = []
        st.rerun()
    except (Unavailable, EmptyCart) as e:
        st.error(str(e))
