"""Profile management (PRD FR-005). Email/role/verification are read-only."""
from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from components import auth_gate
from models.schemas import ProfileUpdate
from services import auth, users

user = auth_gate.require_auth()
profile = users.get_profile(user["user_id"])

st.title("👤 My profile")

col, _ = st.columns([1, 1])
with col:
    st.text_input("Email (read-only)", value=profile["email"], disabled=True)
    st.text_input("Role (read-only)", value=profile["role"], disabled=True)
    st.text_input(
        "Verification (read-only)",
        value="Verified" if profile["is_verified"] else "Unverified",
        disabled=True,
    )
    st.divider()
    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=profile["full_name"])
        phone = st.text_input("Phone", value=profile["phone"] or "")
        saved = st.form_submit_button("Save changes", width="stretch")

    if saved:
        try:
            payload = ProfileUpdate(full_name=full_name, phone=phone or None)
            users.update_profile(user["user_id"], payload)
            # Keep the session snapshot in sync (cart preserved).
            auth_gate.update_user(auth.get_user(user["user_id"]))
            st.success("Profile updated.")
            st.rerun()
        except ValidationError as e:
            st.error(e.errors()[0]["msg"])
