"""Session + access control helpers (PRD §9.3, FR-013).

Every protected page calls ``require_auth`` so authentication, verification and
role are checked at the screen boundary — defence in depth on top of the
navigation-level gating in app.py."""
from __future__ import annotations

import streamlit as st

from services import security


def current_user() -> dict | None:
    return st.session_state.get("auth_user")


def is_authenticated() -> bool:
    """True if a valid, unexpired session token is present. Slides the idle
    window forward on each call (PRD FR-004)."""
    token = st.session_state.get("auth_session_token")
    user = st.session_state.get("auth_user")
    if not token or not user:
        return False
    if security.validate_session(token) is None:
        clear_session("expired")
        return False
    new_token = security.refresh_session(token)
    if new_token:
        st.session_state["auth_session_token"] = new_token
    return True


def start_session(token: str, user: dict) -> None:
    st.session_state["auth_session_token"] = token
    st.session_state["auth_user"] = user
    st.session_state["cart_items"] = []


def update_user(user: dict) -> None:
    """Refresh the cached user snapshot without disturbing the cart/session."""
    st.session_state["auth_user"] = user


def clear_session(reason: str = "logout") -> None:
    for key in ("auth_session_token", "auth_user", "cart_items",
                "active_filters", "editing_listing_id", "viewing_product_id"):
        st.session_state.pop(key, None)


def require_auth(verified: bool = True, admin: bool = False) -> dict:
    """Guard for protected pages. Stops rendering and shows a message if the
    caller is not permitted."""
    if not is_authenticated():
        st.warning("Please log in to continue.")
        st.stop()
    user = current_user()
    assert user is not None
    if verified and not user.get("is_verified"):
        st.warning("Verify your institutional email to access the marketplace.")
        st.stop()
    if admin and user.get("role") != "admin":
        st.error("Admins only.")
        st.stop()
    return user
