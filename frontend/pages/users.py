"""
User Management - Edgewater Inventory Management System
Activation queue, active user management, denied users
Superadmin only (ROLE_SUPERADMIN = 3)
Author: Ian Solberg
Date: 3-14-2026
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from rest.authenticate import (
    Authenticate,
    ROLE_SUPERADMIN,
    ROLE_MAP,
    ROLE_LABELS,
    STATUS_PENDING,
    STATUS_ACTIVE,
    STATUS_DENIED,
    STATUS_LABELS,
)

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="User Management",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== AUTH GATE =====
auth = Authenticate()
auth.require_role(ROLE_SUPERADMIN)
auth.show_user_info_sidebar()

# ===== HEADER =====
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("edgewater.py")
with header_col2:
    st.markdown("# 👤 User Management")

st.markdown("---")

# ===== TABS =====
tab_queue, tab_active, tab_denied, tab_create = st.tabs(
    ["⏳ Activation Queue", "✅ Active Users", "🚫 Denied Users", "➕ Create User"]
)


# ==================== TAB 1: ACTIVATION QUEUE ====================
with tab_queue:
    pending = auth.get_pending_users()

    if not pending:
        st.success("No pending accounts.")
    else:
        st.markdown(f"### {len(pending)} account(s) awaiting activation")

        for u in pending:
            with st.expander(
                f"⏳  **{u['email']}** — {u['role']} ({u['permission_level']}) — "
                f"Registered: {u['created_at'].strftime('%b %d, %Y %H:%M') if u['created_at'] else 'Unknown'}",
                expanded=False,
            ):
                st.markdown(f"- **Email:** {u['email']}")
                st.markdown(f"- **Requested Role:** {u['role']}")
                st.markdown(f"- **Permission Level:** {u['permission_level']}")

                # Role override before activating
                override_col1, override_col2 = st.columns(2)
                with override_col1:
                    new_role = st.selectbox(
                        "Set Role",
                        options=list(ROLE_LABELS.values()),
                        index=0,
                        key=f"role_{u['user_id']}",
                    )
                with override_col2:
                    # Map display label back to permission level string
                    role_to_perm = {v: k for k, v in ROLE_LABELS.items()}
                    perm_to_str = {v: k for k, v in ROLE_MAP.items()}
                    selected_perm_int = role_to_perm.get(new_role, 1)
                    selected_perm_str = perm_to_str.get(selected_perm_int, "employee")
                    st.markdown(f"**Permission Level:** `{selected_perm_str}`")

                action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

                with action_col1:
                    if st.button(
                        "✅ Activate",
                        key=f"activate_{u['user_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        # Update role if changed from default
                        if (
                            new_role != u["role"]
                            or selected_perm_str != u["permission_level"]
                        ):
                            auth.update_user_role(
                                u["user_id"], new_role, selected_perm_str
                            )
                        success, msg = auth.activate_user(u["user_id"])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                with action_col2:
                    if st.button(
                        "🚫 Deny",
                        key=f"deny_{u['user_id']}",
                        use_container_width=True,
                    ):
                        success, msg = auth.deny_user(u["user_id"])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)


# ==================== TAB 2: ACTIVE USERS ====================
with tab_active:
    active_users = auth.get_active_users()

    if not active_users:
        st.info("No active users.")
    else:
        st.markdown(f"### {len(active_users)} active user(s)")

        for u in active_users:
            role_label = ROLE_LABELS.get(
                ROLE_MAP.get(u["permission_level"], 1), "Farm Worker"
            )

            with st.expander(
                f"✅  **{u['email']}** — {u['role']} ({u['permission_level']})",
                expanded=False,
            ):
                st.markdown(f"- **User ID:** {u['user_id']}")
                st.markdown(f"- **Email:** {u['email']}")
                st.markdown(f"- **Role:** {u['role']}")
                st.markdown(f"- **Permission Level:** {u['permission_level']}")
                st.markdown(
                    f"- **Created:** {u['created_at'].strftime('%b %d, %Y') if u['created_at'] else 'Unknown'}"
                )

                st.markdown("---")
                st.markdown("#### Edit Role")

                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    role_options = list(ROLE_LABELS.values())
                    current_idx = (
                        role_options.index(role_label)
                        if role_label in role_options
                        else 0
                    )
                    edit_role = st.selectbox(
                        "Role",
                        options=role_options,
                        index=current_idx,
                        key=f"edit_role_{u['user_id']}",
                    )

                with edit_col2:
                    role_to_perm = {v: k for k, v in ROLE_LABELS.items()}
                    perm_to_str = {v: k for k, v in ROLE_MAP.items()}
                    edit_perm_int = role_to_perm.get(edit_role, 1)
                    edit_perm_str = perm_to_str.get(edit_perm_int, "employee")
                    st.markdown(f"**Permission Level:** `{edit_perm_str}`")

                action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

                with action_col1:
                    if edit_role != role_label:
                        if st.button(
                            "💾 Save Role",
                            key=f"save_role_{u['user_id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            success, msg = auth.update_user_role(
                                u["user_id"], edit_role, edit_perm_str
                            )
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                with action_col2:
                    # Don't let superadmin deactivate themselves
                    current_user = auth.get_user()
                    if u["user_id"] != current_user["user_id"]:
                        if st.button(
                            "⏸️ Deactivate",
                            key=f"deactivate_{u['user_id']}",
                            use_container_width=True,
                        ):
                            success, msg = auth.deactivate_user(u["user_id"])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.caption("(Cannot deactivate yourself)")


# ==================== TAB 3: DENIED USERS ====================
with tab_denied:
    denied_users = auth.get_denied_users()

    if not denied_users:
        st.success("No denied users.")
    else:
        st.markdown(f"### {len(denied_users)} denied user(s)")
        st.caption(
            "Denied users cannot log in or re-register with the same email. "
            "You can reverse the denial or permanently delete the account."
        )

        for u in denied_users:
            with st.expander(
                f"🚫  **{u['email']}** — denied",
                expanded=False,
            ):
                st.markdown(f"- **Email:** {u['email']}")
                st.markdown(f"- **Original Role:** {u['role']}")
                st.markdown(
                    f"- **Created:** {u['created_at'].strftime('%b %d, %Y') if u['created_at'] else 'Unknown'}"
                )

                action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

                with action_col1:
                    if st.button(
                        "↩️ Move to Queue",
                        key=f"unblock_{u['user_id']}",
                        use_container_width=True,
                    ):
                        # Set back to pending so they appear in activation queue
                        success, msg = auth.deactivate_user(u["user_id"])
                        if success:
                            st.success(f"Moved {u['email']} back to activation queue.")
                            st.rerun()
                        else:
                            st.error(msg)

                with action_col2:
                    with st.popover("🗑️ Delete Permanently"):
                        st.warning(
                            f"Permanently delete **{u['email']}**? "
                            "This cannot be undone."
                        )
                        if st.button(
                            "Yes, Delete",
                            key=f"delete_{u['user_id']}",
                            type="primary",
                        ):
                            success, msg = auth.delete_user(u["user_id"])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)


# ==================== TAB 4: CREATE USER (ADMIN-CREATED) ====================
with tab_create:
    st.markdown("### ➕ Create User")
    st.caption("Admin-created users can be set to any role and are active immediately.")

    with st.form("create_user_form", clear_on_submit=True):
        create_col1, create_col2 = st.columns(2)

        with create_col1:
            new_email = st.text_input(
                "Email *",
                placeholder="user@example.com",
                key="create_email",
            )
            new_password = st.text_input(
                "Password *",
                type="password",
                placeholder="At least 8 characters",
                key="create_password",
            )

        with create_col2:
            new_role = st.selectbox(
                "Role",
                options=list(ROLE_LABELS.values()),
                key="create_role",
            )
            role_to_perm = {v: k for k, v in ROLE_LABELS.items()}
            perm_to_str = {v: k for k, v in ROLE_MAP.items()}
            new_perm_int = role_to_perm.get(new_role, 1)
            new_perm_str = perm_to_str.get(new_perm_int, "employee")
            st.markdown(f"**Permission Level:** `{new_perm_str}`")

        submitted = st.form_submit_button(
            "✅ Create User", type="primary", use_container_width=True
        )

        if submitted:
            if not new_email or not new_password:
                st.error("Email and password are required.")
            else:
                success, msg = auth.create_user(
                    email=new_email,
                    password=new_password,
                    role=new_role,
                    permission_level=new_perm_str,
                    active=True,
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ===== FOOTER =====
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
