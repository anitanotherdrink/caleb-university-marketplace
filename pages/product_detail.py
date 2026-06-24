"""Product detail + add to cart (PRD §6.1 Product Detail)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from components.ui import listing_image, money, status_chip
from services import catalog, telemetry
from services.errors import NotFound

user = auth_gate.require_auth()

product_id = st.session_state.get("viewing_product_id")
if not product_id:
    st.info("Pick an item from Browse to see its details.")
    if st.button("← Back to browse"):
        st.switch_page("pages/browse.py")
    st.stop()

try:
    product = catalog.get_product(product_id)
except NotFound:
    st.error("This listing is no longer available.")
    st.stop()

if st.button("← Back to browse"):
    st.switch_page("pages/browse.py")

left, right = st.columns([1, 1])
with left:
    listing_image(product)
with right:
    st.title(product["title"])
    st.markdown(f"## {money(product['price'])}")
    status_chip(product["status"])
    st.write("")
    st.markdown(f"**Condition:** {product['condition'].capitalize()}")
    st.markdown(f"**Category:** {product['category_name']}")
    st.markdown(f"**Available:** {product['quantity']}")
    st.markdown(f"**Seller:** {product['seller_name']}")
    if product["description"]:
        st.markdown("**Description**")
        st.write(product["description"])

    st.divider()
    own = product["seller_id"] == user["user_id"]
    if own:
        st.info("This is your own listing.")
    elif product["status"] != "available" or product["quantity"] < 1:
        st.warning("This item is no longer available.")
    else:
        qty = st.number_input(
            "Quantity", min_value=1, max_value=int(product["quantity"]), value=1
        )
        if st.button("🛒 Add to cart", width="stretch"):
            cart = st.session_state.setdefault("cart_items", [])
            existing = next(
                (c for c in cart if c["product_id"] == product_id), None
            )
            if existing:
                existing["quantity"] = min(
                    existing["quantity"] + int(qty), int(product["quantity"])
                )
            else:
                cart.append(
                    {
                        "product_id": product_id,
                        "title": product["title"],
                        "price": product["price"],
                        "quantity": int(qty),
                        "max": int(product["quantity"]),
                    }
                )
            telemetry.emit("cart_item_added", product_id=product_id, qty=int(qty))
            st.success("Added to cart.")
            if st.button("🛒 Go to cart", key="goto_cart"):
                st.switch_page("pages/cart.py")
