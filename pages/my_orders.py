"""Order tracking: buyer view + seller status management (PRD FR-012)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from components.ui import money, status_chip
from services import orders
from services.errors import Forbidden, IllegalTransition
from services.orders import ALLOWED_TRANSITIONS

user = auth_gate.require_auth()

st.title("🧾 My orders")

buyer_tab, seller_tab = st.tabs(["As buyer", "As seller"])

with buyer_tab:
    my = orders.list_buyer_orders(user["user_id"])
    if not my:
        st.info("No orders yet.")
    for o in my:
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.markdown(f"**Order #{o['order_id']}**")
            h1.caption(o["created_at"].strftime("%d %b %Y, %H:%M"))
            with h2:
                status_chip(o["status"])
            for item in o["items"]:
                st.write(
                    f"- {item['quantity']} × {item['title']} — "
                    f"{money(item['price'] * item['quantity'])}"
                )
            st.markdown(f"**Total: {money(o['total'])}**")

with seller_tab:
    incoming = orders.list_seller_orders(user["user_id"])
    if not incoming:
        st.info("No orders on your listings yet.")
    for o in incoming:
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.markdown(f"**Order #{o['order_id']}** · buyer: {o['buyer_name']}")
            h1.caption(o["created_at"].strftime("%d %b %Y, %H:%M"))
            with h2:
                status_chip(o["status"])
            for item in o["items"]:
                st.write(
                    f"- {item['quantity']} × {item['title']} — "
                    f"{money(item['price'] * item['quantity'])}"
                )
            next_states = sorted(ALLOWED_TRANSITIONS.get(o["status"], set()))
            if next_states:
                cols = st.columns(len(next_states) + 1)
                cols[0].caption("Update status:")
                for i, target in enumerate(next_states):
                    if cols[i + 1].button(
                        target.capitalize(), key=f"st_{o['order_id']}_{target}"
                    ):
                        try:
                            orders.set_status(o["order_id"], target, user)
                            st.success(f"Order #{o['order_id']} → {target}.")
                            st.rerun()
                        except (Forbidden, IllegalTransition) as e:
                            st.error(str(e))
            else:
                st.caption(f"Order is {o['status']} (no further changes).")
