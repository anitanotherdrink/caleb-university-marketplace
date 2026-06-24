"""Login screen with marketing hero (PRD FR-003, §6.1)."""
from __future__ import annotations

import streamlit as st

import config
from components import auth_gate
from services import auth
from services.errors import BadCredentials, NotVerified, RateLimited

hero, form = st.columns([1.1, 1], gap="large")

with hero:
    st.markdown(
        """
        <div class="cm-hero">
            <div style="font-size:2rem">🎓</div>
            <h1>The trusted marketplace for Caleb students</h1>
            <p>Buy and sell textbooks, gadgets, fashion and hostel essentials with
            people you can trust — verified members of your own campus.</p>
            <div class="cm-feat"><div class="ic">🔒</div><div class="tx">
                <b>Verified students only</b>
                <span>Access is limited to confirmed @%s emails.</span></div></div>
            <div class="cm-feat"><div class="ic">🛍️</div><div class="tx">
                <b>Find anything, fast</b>
                <span>Search and filter by category, keyword and price.</span></div></div>
            <div class="cm-feat"><div class="ic">🤝</div><div class="tx">
                <b>Safe, in-person trade</b>
                <span>No personal contacts exposed. Pay on campus, in person.</span></div></div>
        </div>
        """
        % config.INSTITUTION_DOMAIN,
        unsafe_allow_html=True,
    )

with form:
    st.markdown("### Welcome back 👋")
    st.caption(f"Log in with your @{config.INSTITUTION_DOMAIN} account.")
    with st.form("login_form"):
        email = st.text_input("Institutional email",
                              placeholder=f"you@{config.INSTITUTION_DOMAIN}")
        password = st.text_input("Password", type="password",
                                 placeholder="Your password")
        submitted = st.form_submit_button("Log in", width="stretch",
                                          type="primary")

    if submitted:
        try:
            result = auth.login(email, password)
            auth_gate.start_session(result["token"], result["user"])
            st.success("Welcome back!")
            st.rerun()
        except NotVerified as e:
            st.warning(str(e))
            if st.button("Resend verification email"):
                auth.resend_verification(email)
                st.info("If the account exists, a new link has been sent.")
        except (BadCredentials, RateLimited) as e:
            st.error(str(e))

    st.divider()
    st.caption("New to the marketplace?")
    if st.button("Create an account", width="stretch"):
        st.switch_page("pages/register.py")
