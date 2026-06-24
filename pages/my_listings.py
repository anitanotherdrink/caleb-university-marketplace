"""Seller inventory: view / edit / delete own listings (PRD FR-006..008)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from components.ui import money, status_chip
from services import catalog
from services.errors import Forbidden, NotFound

user = auth_gate.require_auth()

st.title("📦 My listings")

top1, top2 = st.columns([3, 1])
top1.caption("Items you are selling on the marketplace.")
if top2.button("➕ New listing", width="stretch"):
    st.session_state.pop("editing_listing_id", None)
    st.switch_page("pages/listing_editor.py")

products = catalog.list_seller_products(user["user_id"])

if not products:
    st.info("You haven't listed anything yet.")
    st.stop()

for p in products:
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
        c1.markdown(f"**{p['title']}**")
        c1.caption(f"{p['category_name']} · {p['condition']}")
        c2.markdown(money(p["price"]))
        c2.caption(f"Qty: {p['quantity']}")
        with c3:
            status_chip(p["status"])
        if c4.button("Edit", key=f"edit_{p['product_id']}"):
            st.session_state["editing_listing_id"] = p["product_id"]
            st.switch_page("pages/listing_editor.py")
        if c5.button("Delete", key=f"del_{p['product_id']}"):
            st.session_state[f"confirm_del_{p['product_id']}"] = True
        if st.session_state.get(f"confirm_del_{p['product_id']}"):
            st.warning(f"Delete '{p['title']}'? This removes it from the marketplace.")
            d1, d2 = st.columns(2)
            if d1.button("Yes, delete", key=f"yesdel_{p['product_id']}"):
                try:
                    catalog.delete_listing(p["product_id"], user)
                    st.session_state.pop(f"confirm_del_{p['product_id']}", None)
                    st.success("Listing deleted.")
                    st.rerun()
                except (Forbidden, NotFound) as e:
                    st.error(str(e))
            if d2.button("Cancel", key=f"nodel_{p['product_id']}"):
                st.session_state.pop(f"confirm_del_{p['product_id']}", None)
                st.rerun()
