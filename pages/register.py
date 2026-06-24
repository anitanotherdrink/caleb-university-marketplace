"""Registration screen (PRD FR-001)."""
from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

import config
from models.schemas import UserCreate
from services import auth
from services.errors import DuplicateEmail

hero, form = st.columns([1, 1.2], gap="large")

with hero:
    st.markdown(
        """
        <div class="cm-hero">
            <div style="font-size:2rem">📝</div>
            <h1>Join your campus marketplace</h1>
            <p>It takes a minute. Use your institutional email, verify it once, and
            start buying and selling with fellow Caleb University students.</p>
            <div class="cm-feat"><div class="ic">✅</div><div class="tx">
                <b>One-time verification</b>
                <span>Confirm your email and you're in for good.</span></div></div>
            <div class="cm-feat"><div class="ic">📦</div><div class="tx">
                <b>List in seconds</b>
                <span>Add a photo, price and category — done.</span></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with form:
    st.markdown("### Create your account")
    st.caption(f"Only @{config.INSTITUTION_DOMAIN} students can join.")
    with st.form("register_form"):
        full_name = st.text_input("Full name", placeholder="Ada Obi")
        email = st.text_input("Institutional email",
                             placeholder=f"you@{config.INSTITUTION_DOMAIN}")
        phone = st.text_input("Phone (optional)", placeholder="0801 234 5678")
        password = st.text_input("Password", type="password")
        st.caption(
            f"At least {config.PASSWORD_MIN_LENGTH} characters, mixing upper/lower "
            "case, digits and symbols."
        )
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Register", width="stretch",
                                          type="primary")

    if submitted:
        if password != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                payload = UserCreate(
                    full_name=full_name,
                    email=email,
                    password=password,
                    phone=phone or None,
                )
                auth.register(payload)
                st.session_state["pending_verify_email"] = payload.email
                st.success("🎉 Account created! One last step — verify your email.")
            except ValidationError as e:
                st.error(e.errors()[0]["msg"])
            except DuplicateEmail as e:
                st.error(str(e))

    pending = st.session_state.get("pending_verify_email")
    if pending:
        st.info(
            "Check your inbox for the verification link. If no mail server is "
            "configured here, use the shortcut below."
        )
        if not config.smtp_configured():
            if st.button("✅ Verify my email now (dev mode)",
                         width="stretch"):
                if auth.dev_autoverify(pending):
                    st.session_state.pop("pending_verify_email", None)
                    st.success("Email verified! You can log in now.")
                    if st.button("🔑 Go to login", key="goto_login"):
                        st.switch_page("pages/login.py")

    st.divider()
    if st.button("Already have an account? Log in"):
        st.switch_page("pages/login.py")
