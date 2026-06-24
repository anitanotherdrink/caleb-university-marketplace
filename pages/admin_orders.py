"""Admin: oversee all orders + moderate listings (PRD FR-014)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from components.ui import money, status_chip
from services import admin, catalog
from services.errors import Forbidden, NotFound

user = auth_gate.require_auth(admin=True)

st.title("📊 Oversight")

orders_tab, listings_tab = st.tabs(["All orders", "Listings moderation"])

with orders_tab:
    all_orders = admin.all_orders(user)
    if not all_orders:
        st.info("No orders placed yet.")
    for o in all_orders:
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.markdown(f"**Order #{o['order_id']}** · buyer: {o['buyer_name']}")
            h1.caption(o["created_at"].strftime("%d %b %Y, %H:%M"))
            with h2:
                status_chip(o["status"])
            for item in o["items"]:
                st.write(f"- {item['quantity']} × {item['title']} — "
                         f"{money(item['price'] * item['quantity'])}")
            st.markdown(f"**Total: {money(o['total'])}**")

with listings_tab:
    st.caption("Remove listings that violate platform rules.")
    products = catalog.search(include_sold=True)
    if not products:
        st.info("No active listings.")
    for p in products:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"**{p['title']}**")
            c1.caption(f"Seller: {p['seller_name']} · {p['category_name']}")
            c2.markdown(money(p["price"]))
            with c2:
                status_chip(p["status"])
            if c3.button("Remove", key=f"mod_{p['product_id']}"):
                try:
                    catalog.delete_listing(p["product_id"], user)
                    st.success("Listing removed.")
                    st.rerun()
                except (Forbidden, NotFound) as e:
                    st.error(str(e))
