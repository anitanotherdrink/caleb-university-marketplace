"""Browse / search / filter (PRD FR-010). Default screen after login."""
from __future__ import annotations

import streamlit as st

from components import auth_gate, theme
from components.ui import listing_card
from services import catalog

user = auth_gate.require_auth()

theme.page_title(
    f"Welcome, {user['full_name'].split()[0]} 👋",
    "Discover items listed by verified Caleb University students.",
)

categories = catalog.list_categories()
cat_options = {0: "All categories"} | {c["category_id"]: c["name"] for c in categories}

with st.form("filters"):
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("Search", placeholder="textbook, phone, hostel fan…",
                            max_chars=120)
    category_id = c2.selectbox(
        "Category", options=list(cat_options), format_func=lambda k: cat_options[k]
    )
    c3, c4 = st.columns(2)
    price_min = c3.number_input("Min price (₦)", min_value=0.0, value=0.0, step=100.0)
    price_max = c4.number_input("Max price (₦)", min_value=0.0, value=0.0, step=100.0)
    fc1, fc2 = st.columns(2)
    apply_clicked = fc1.form_submit_button("Apply filters", width="stretch")
    clear_clicked = fc2.form_submit_button("Clear", width="stretch")

if clear_clicked:
    st.session_state.pop("active_filters", None)
    from services import telemetry

    telemetry.emit("filters_cleared")
    st.rerun()

if apply_clicked:
    if price_max and price_min > price_max:
        st.error("Minimum price cannot exceed maximum price.")
        st.stop()
    st.session_state["active_filters"] = {
        "keyword": keyword or None,
        "category_id": category_id or None,
        "price_min": price_min or None,
        "price_max": price_max or None,
    }

filters = st.session_state.get("active_filters", {})
results = catalog.search(
    keyword=filters.get("keyword"),
    category_id=filters.get("category_id"),
    price_min=filters.get("price_min"),
    price_max=filters.get("price_max"),
)

st.markdown(
    f"<span class='cm-pill accent'>{len(results)} item(s)</span>",
    unsafe_allow_html=True,
)
st.write("")


def _open(product_id: int) -> None:
    st.session_state["viewing_product_id"] = product_id
    st.switch_page("pages/product_detail.py")


# Pagination (PRD §6.1: 20/page).
PAGE_SIZE = 20
page = st.session_state.get("browse_page", 0)
total_pages = max(1, (len(results) + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(page, total_pages - 1)
window = results[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

if not results:
    st.info("No items match your filters.")
    if st.button("Clear filters"):
        st.session_state.pop("active_filters", None)
        st.rerun()
else:
    cols = st.columns(4)
    for i, product in enumerate(window):
        with cols[i % 4]:
            listing_card(product, _open)

    if total_pages > 1:
        st.divider()
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        if pcol1.button("← Prev", disabled=page == 0):
            st.session_state["browse_page"] = page - 1
            st.rerun()
        pcol2.markdown(
            f"<div style='text-align:center'>Page {page + 1} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
        if pcol3.button("Next →", disabled=page >= total_pages - 1):
            st.session_state["browse_page"] = page + 1
            st.rerun()
