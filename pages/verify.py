"""Email verification landing + resend (PRD FR-002)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from services import auth
from services.errors import TokenExpired, TokenInvalid

st.title("Verify your email")

token = st.query_params.get("token")

if token:
    try:
        auth.verify(token)
        st.success("✅ Your email is verified. You can now log in.")
        st.query_params.clear()
        if auth_gate.is_authenticated():
            # A logged-in-but-unverified user just verified — refresh their snapshot.
            user = auth_gate.current_user()
            if user:
                auth_gate.update_user(auth.get_user(user["user_id"]))
            st.rerun()
        else:
            st.page_link("pages/login.py", label="Go to login", icon="🔑")
    except TokenExpired:
        st.error("This verification link has expired.")
        _expired = True
    except TokenInvalid as e:
        st.error(str(e))
else:
    st.info(
        "📬 Check your inbox for the verification link we sent. If no mail "
        "server is configured in this environment, the link is printed in the "
        "app console."
    )

st.divider()
st.caption("Didn't get the email?")
resend_email = st.text_input("Your institutional email")
if st.button("Resend verification link"):
    if resend_email:
        auth.resend_verification(resend_email)
        st.info("If the account exists and is unverified, a new link has been sent.")
    else:
        st.warning("Enter your email first.")
