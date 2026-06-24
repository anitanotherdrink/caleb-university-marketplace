"""Admin: verify / manage users + platform metrics (PRD FR-014)."""
from __future__ import annotations

import streamlit as st

from components import auth_gate
from services import admin
from services.errors import Forbidden, NotFound

user = auth_gate.require_auth(admin=True)

st.title("👥 User administration")

m = admin.metrics(user)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Users", m["users"])
c2.metric("Verified", m["verified"])
c3.metric("Listings", m["listings"])
c4.metric("Orders", m["orders"])
st.divider()

users_list = admin.list_users(user)
for u in users_list:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        c1.markdown(f"**{u['full_name']}**")
        c1.caption(u["email"])
        c2.caption(
            f"Role: {u['role']} · "
            f"{'✅ verified' if u['is_verified'] else '⏳ unverified'} · "
            f"{'active' if u['is_active'] else 'deactivated'}"
        )
        if u["role"] == "admin":
            c3.caption("—")
            c4.caption("—")
            continue
        try:
            if u["is_verified"]:
                if c3.button("Unverify", key=f"unv_{u['user_id']}"):
                    admin.set_verified(user, u["user_id"], False)
                    st.rerun()
            else:
                if c3.button("Verify", key=f"ver_{u['user_id']}"):
                    admin.set_verified(user, u["user_id"], True)
                    st.success(f"{u['full_name']} verified.")
                    st.rerun()
            if u["is_active"]:
                if c4.button("Deactivate", key=f"deact_{u['user_id']}"):
                    admin.set_active(user, u["user_id"], False)
                    st.rerun()
            else:
                if c4.button("Reactivate", key=f"react_{u['user_id']}"):
                    admin.set_active(user, u["user_id"], True)
                    st.rerun()
        except (Forbidden, NotFound) as e:
            st.error(str(e))
