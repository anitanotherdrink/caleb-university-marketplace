"""Create / edit a listing with image upload (PRD FR-006, FR-007, FR-009)."""
from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from components import auth_gate
from components.ui import listing_image
from models.schemas import Condition, ProductCreate
from services import catalog
from services.errors import Forbidden, ImageRejected, NotFound

user = auth_gate.require_auth()

editing_id = st.session_state.get("editing_listing_id")
existing = None
if editing_id:
    try:
        existing = catalog.get_product(editing_id)
        if existing["seller_id"] != user["user_id"] and user["role"] != "admin":
            st.error("You can only edit your own listings.")
            st.stop()
    except NotFound:
        st.error("Listing not found.")
        st.stop()

st.title("✏️ Edit listing" if existing else "➕ New listing")

categories = catalog.list_categories()
if not categories:
    st.warning("No categories exist yet. Ask an admin to create one.")
    st.stop()
cat_ids = [c["category_id"] for c in categories]
cat_names = {c["category_id"]: c["name"] for c in categories}

with st.form("listing_form"):
    title = st.text_input("Title", value=existing["title"] if existing else "",
                          max_chars=120)
    description = st.text_area(
        "Description", value=existing["description"] if existing else ""
    )
    c1, c2 = st.columns(2)
    price = c1.number_input(
        "Price (₦)", min_value=0.01, step=50.0,
        value=float(existing["price"]) if existing else 0.01,
    )
    qty = c2.number_input(
        "Quantity", min_value=1, step=1,
        value=int(existing["quantity"]) if existing else 1,
    )
    c3, c4 = st.columns(2)
    condition = c3.selectbox(
        "Condition", ["new", "used"],
        index=(["new", "used"].index(existing["condition"]) if existing else 0),
    )
    default_cat_idx = (
        cat_ids.index(existing["category_id"])
        if existing and existing["category_id"] in cat_ids
        else 0
    )
    category_id = c4.selectbox(
        "Category", options=cat_ids, format_func=lambda k: cat_names[k],
        index=default_cat_idx,
    )

    status = None
    if existing:
        status = st.selectbox(
            "Status", ["available", "sold"],
            index=["available", "sold"].index(existing["status"]),
        )

    if existing and existing.get("image_path"):
        st.caption("Current image:")
        listing_image(existing, width=160)
    image_file = st.file_uploader(
        "Image" + (" (leave empty to keep current)" if existing else ""),
        type=["jpg", "jpeg", "png", "webp"],
    )

    submitted = st.form_submit_button(
        "Save changes" if existing else "Publish listing", width="stretch"
    )

if submitted:
    try:
        payload = ProductCreate(
            title=title,
            description=description or None,
            price=price,
            condition=Condition(condition),
            quantity=int(qty),
            category_id=int(category_id),
        )
        image_bytes = image_file.getvalue() if image_file else None
        if existing:
            catalog.update_listing(
                editing_id, user, payload, status=status, image_bytes=image_bytes
            )
            st.success("Listing updated.")
        else:
            if not image_bytes:
                st.error("Please add at least one image.")
                st.stop()
            catalog.create_listing(user["user_id"], payload, image_bytes)
            st.success("Listing published and now visible in Browse.")
        st.session_state.pop("editing_listing_id", None)
        if st.button("📦 Back to my listings", key="back_listings"):
            st.switch_page("pages/my_listings.py")
    except ValidationError as e:
        st.error(e.errors()[0]["msg"])
    except (ImageRejected, Forbidden, NotFound) as e:
        st.error(str(e))
