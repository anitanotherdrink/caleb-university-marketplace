"""Reusable presentation helpers (PRD §9.2 components/).

Keeps formatting, status chips and listing cards in one place so screens stay
thin and consistent (maintainability NFR, PRD §3.3.2(vi))."""
from __future__ import annotations

from decimal import Decimal

import streamlit as st

import config
from services import catalog

_STATUS_COLORS = {
    "pending": ("#92610a", "#fff4d6"),
    "confirmed": ("#0a5cad", "#dceaff"),
    "completed": ("#0f7a32", "#d9f5e1"),
    "cancelled": ("#9a1c1c", "#fbdcdc"),
    "available": ("#0f7a32", "#d9f5e1"),
    "sold": ("#555", "#e6e6e6"),
}


def money(value) -> str:
    try:
        return f"{config.CURRENCY_SYMBOL}{Decimal(str(value)):,.2f}"
    except Exception:
        return f"{config.CURRENCY_SYMBOL}{value}"


def status_chip(status: str) -> None:
    fg, bg = _STATUS_COLORS.get(status, ("#333", "#eee"))
    # Text label included so meaning never relies on colour alone (PRD §6.3).
    st.markdown(
        f"<span style='background:{bg};color:{fg};padding:2px 10px;"
        f"border-radius:12px;font-size:0.8rem;font-weight:600'>"
        f"{status.upper()}</span>",
        unsafe_allow_html=True,
    )


_GRADIENTS = [
    ("#4f46e5", "#7c3aed"), ("#0ea5e9", "#2563eb"), ("#059669", "#10b981"),
    ("#f59e0b", "#f97316"), ("#db2777", "#9333ea"), ("#0891b2", "#0d9488"),
]


def _placeholder(title: str, height: int = 170) -> str:
    g = _GRADIENTS[hash(title) % len(_GRADIENTS)]
    label = (title or "Item").strip()[:48]
    return (
        f"<div class='cm-thumb' style='height:{height}px;"
        f"background:linear-gradient(135deg,{g[0]},{g[1]})'>{label}</div>"
    )


def listing_image(product: dict, width: int | None = None) -> None:
    path = catalog.image_abs_path(product.get("image_path"))
    if path:
        st.image(path, width="stretch" if width is None else width)
    else:
        st.markdown(_placeholder(product.get("title", "")), unsafe_allow_html=True)


def listing_card(product: dict, on_open) -> None:
    """Render a polished product tile with an Open action."""
    with st.container(border=True):
        listing_image(product)
        st.markdown(
            f"<div style='font-weight:700;font-size:1rem;margin-top:6px;"
            f"min-height:2.6em;line-height:1.3'>{product['title']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='cm-price'>{money(product['price'])}</div>",
            unsafe_allow_html=True,
        )
        cond_cls = "accent" if product["condition"] == "new" else ""
        st.markdown(
            f"<span class='cm-pill {cond_cls}'>{product['condition'].capitalize()}</span>"
            f"<span class='cm-pill'>{product['category_name']}</span>",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("View details", key=f"open_{product['product_id']}",
                     width="stretch", type="primary"):
            on_open(product["product_id"])
