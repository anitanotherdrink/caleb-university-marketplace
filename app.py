"""Caleb University Student Marketplace — Streamlit entry point.

Router + auth gate + theming (PRD §5, §9.1, §9.8). Realizes the thesis
three-tier model: this file and pages/ are the presentation tier, services/ is
the application tier, models/ + the SQL database are the data tier.
"""
from __future__ import annotations

import streamlit as st

from components import auth_gate, theme
from services.db import init_db

st.set_page_config(
    page_title="Caleb University Marketplace",
    page_icon="🎓",
    layout="wide",
)


@st.cache_resource
def _bootstrap() -> bool:
    """Create tables and seed starter data once per process (PRD §9.4)."""
    init_db(seed=True)
    return True


_bootstrap()


def _sidebar_account() -> None:
    user = auth_gate.current_user()
    with st.sidebar:
        st.markdown("### 🎓 Caleb Marketplace")
        if user:
            initials = "".join(p[0] for p in user["full_name"].split()[:2]).upper()
            role_label = "Administrator" if user["role"] == "admin" else "Student"
            st.markdown(
                f"""
                <div style='display:flex;gap:10px;align-items:center;
                    background:rgba(255,255,255,.10);padding:10px 12px;
                    border-radius:12px;margin-bottom:10px'>
                  <div style='width:40px;height:40px;border-radius:50%;
                      background:#f59e0b;color:#1e1b4b;font-weight:800;
                      display:flex;align-items:center;justify-content:center'>
                      {initials or "U"}</div>
                  <div style='line-height:1.2'>
                      <div style='font-weight:700'>{user['full_name']}</div>
                      <div style='font-size:.74rem;opacity:.8'>{role_label}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(user["email"])
            st.divider()
            if st.button("🚪 Log out", width="stretch"):
                from services import telemetry

                telemetry.emit("logout", user_id=user["user_id"])
                auth_gate.clear_session()
                st.rerun()


def main() -> None:
    theme.inject_global_styles()
    authenticated = auth_gate.is_authenticated()
    user = auth_gate.current_user()
    verified = bool(user and user.get("is_verified"))
    is_admin = bool(user and user.get("role") == "admin")

    # Page registry ---------------------------------------------------------
    login = st.Page("pages/login.py", title="Log in", icon="🔑")
    register = st.Page("pages/register.py", title="Register", icon="📝")
    verify = st.Page("pages/verify.py", title="Verify email", icon="✉️")

    browse = st.Page("pages/browse.py", title="Browse", icon="🛍️", default=True)
    product = st.Page("pages/product_detail.py", title="Product", icon="🔍")
    cart = st.Page("pages/cart.py", title="Cart", icon="🛒")
    my_listings = st.Page("pages/my_listings.py", title="My Listings", icon="📦")
    editor = st.Page("pages/listing_editor.py", title="Listing Editor", icon="✏️")
    my_orders = st.Page("pages/my_orders.py", title="My Orders", icon="🧾")
    profile = st.Page("pages/profile.py", title="Profile", icon="👤")

    admin_users = st.Page("pages/admin_users.py", title="Users", icon="👥")
    admin_categories = st.Page("pages/admin_categories.py", title="Categories", icon="🏷️")
    admin_orders = st.Page("pages/admin_orders.py", title="Orders", icon="📊")

    # Routing ---------------------------------------------------------------
    if not authenticated:
        pages = (
            [verify, login, register]
            if "token" in st.query_params
            else [login, register, verify]
        )
        nav = st.navigation(pages, position="hidden")
    elif not verified:
        # Pinned to verification until the institutional email is confirmed.
        nav = st.navigation([verify], position="hidden")
        _sidebar_account()
    else:
        sections: dict[str, list] = {
            "Marketplace": [browse, product, cart, my_orders],
            "Selling": [my_listings, editor],
            "Account": [profile],
        }
        if is_admin:
            sections["Admin"] = [admin_users, admin_categories, admin_orders]
        nav = st.navigation(sections)
        _sidebar_account()
        theme.topbar()

    try:
        nav.run()
    except Exception:  # global error boundary (PRD §9.8)
        st.error("Something went wrong. Please retry.")
        st.exception  # noqa: B018  (kept minimal; details go to server logs)


main()
