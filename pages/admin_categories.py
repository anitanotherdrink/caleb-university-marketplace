"""Admin: manage categories (PRD FR-014)."""
from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from components import auth_gate
from models.schemas import CategoryIn
from services import admin, catalog
from services.errors import InUse, NotFound

user = auth_gate.require_auth(admin=True)

st.title("🏷️ Categories")

with st.expander("➕ Add a category"):
    with st.form("new_cat"):
        name = st.text_input("Name", max_chars=60)
        desc = st.text_input("Description (optional)", max_chars=255)
        if st.form_submit_button("Create"):
            try:
                admin.create_category(user, CategoryIn(name=name, description=desc or None))
                st.success("Category created.")
                st.rerun()
            except ValidationError as e:
                st.error(e.errors()[0]["msg"])
            except InUse as e:
                st.error(str(e))

st.divider()
for c in catalog.list_categories():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        new_name = col1.text_input("Name", value=c["name"], key=f"cn_{c['category_id']}")
        new_desc = col2.text_input(
            "Description", value=c["description"] or "", key=f"cd_{c['category_id']}"
        )
        with col3:
            if st.button("Save", key=f"save_{c['category_id']}"):
                try:
                    admin.update_category(
                        user, c["category_id"],
                        CategoryIn(name=new_name, description=new_desc or None),
                    )
                    st.success("Updated.")
                    st.rerun()
                except (ValidationError, InUse, NotFound) as e:
                    msg = e.errors()[0]["msg"] if isinstance(e, ValidationError) else str(e)
                    st.error(msg)
            if st.button("Delete", key=f"delcat_{c['category_id']}"):
                try:
                    admin.delete_category(user, c["category_id"])
                    st.success("Deleted.")
                    st.rerun()
                except (InUse, NotFound) as e:
                    st.error(str(e))
