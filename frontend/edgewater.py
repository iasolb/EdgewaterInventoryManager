"""
Edgewater Inventory Management System - Landing Page
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-14-2026 - Auth gate, self-registration, password reset, role-gated nav
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))
from rest.api import EdgewaterAPI
from rest.authenticate import Authenticate, ROLE_EMPLOYEE, ROLE_ADMIN, ROLE_SUPERADMIN

api = EdgewaterAPI()
auth = Authenticate()

st.set_page_config(
    page_title="Edgewater Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from edgewater_theme import apply_theme

apply_theme()
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        button[kind="header"] { display: none !important; }
        .stSidebar { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
# ================================================================
# SESSION STATE for login page flow
# ================================================================
if "login_show_reset" not in st.session_state:
    st.session_state.login_show_reset = False
if "login_reset_email" not in st.session_state:
    st.session_state.login_reset_email = ""


# ================================================================
# NOT AUTHENTICATED — Login / Register
# ================================================================

if not auth.is_authenticated():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("### Edgewater Database Manager")
        st.markdown("---")

        login_tab, register_tab = st.tabs(["🔑 Log In", "📝 Create Account"])

        # ---- Login ----
        with login_tab:

            # Normal login form
            if not st.session_state.login_show_reset:
                with st.form("login_form"):
                    email = st.text_input(
                        "Email",
                        placeholder="your.email@example.com",
                        key="login_email",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="login_password",
                    )
                    submitted = st.form_submit_button(
                        "Log In", type="primary", use_container_width=True
                    )

                    if submitted:
                        success, message, hint = auth.login(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        elif hint == "bad_password":
                            st.error(message)
                            if auth.email_exists(email):
                                st.session_state.login_show_reset = True
                                st.session_state.login_reset_email = email
                                st.rerun()
                        elif hint == "inactive":
                            st.warning(message)
                        elif hint == "denied":
                            st.error(message)
                        else:
                            st.error(message)

            # Password reset form (shown after bad password on known email)
            else:
                reset_email = st.session_state.login_reset_email
                st.markdown(f"#### 🔄 Reset Password")
                st.warning(
                    f"Reset password for **{reset_email}**? "
                    "This will deactivate your account until an administrator reactivates it. "
                    "Your permissions will be preserved."
                )

                with st.form("reset_form"):
                    new_pw = st.text_input(
                        "New Password",
                        type="password",
                        placeholder="At least 8 characters",
                        key="reset_new_pw",
                    )
                    confirm_pw = st.text_input(
                        "Confirm New Password",
                        type="password",
                        key="reset_confirm_pw",
                    )

                    reset_col1, reset_col2 = st.columns(2)
                    with reset_col1:
                        reset_submitted = st.form_submit_button(
                            "Reset Password", type="primary", use_container_width=True
                        )
                    with reset_col2:
                        cancel_submitted = st.form_submit_button(
                            "Cancel", use_container_width=True
                        )

                    if reset_submitted:
                        if new_pw != confirm_pw:
                            st.error("Passwords don't match.")
                        else:
                            success, message = auth.reset_password(reset_email, new_pw)
                            if success:
                                st.success(message)
                                st.session_state.login_show_reset = False
                                st.session_state.login_reset_email = ""
                            else:
                                st.error(message)

                    if cancel_submitted:
                        st.session_state.login_show_reset = False
                        st.session_state.login_reset_email = ""
                        st.rerun()

        # ---- Self-Registration ----
        with register_tab:
            st.caption(
                "Create an account to get started. Your account will need to be "
                "activated by an administrator before you can access the system."
            )
            with st.form("register_form"):
                reg_email = st.text_input(
                    "Email",
                    placeholder="your.email@example.com",
                    key="reg_email",
                )
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                    key="reg_password",
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm",
                )
                reg_submitted = st.form_submit_button(
                    "Create Account", type="primary", use_container_width=True
                )
                if reg_submitted:
                    if reg_password != reg_confirm:
                        st.error("Passwords don't match.")
                    else:
                        success, message = auth.register(reg_email, reg_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

    st.stop()


# ================================================================
# AUTHENTICATED + ACTIVE — role-gated navigation
# ================================================================

user = auth.get_user()
role_int = user["role_int"]

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown("### Edgewater Database Manager")

info_col1, info_col2, info_col3 = st.columns([2, 2, 1])
with info_col1:
    st.markdown(f"Logged in as **{user['role']}** ({user['email']})")
with info_col3:
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()
        st.rerun()

st.markdown("---")

# Employee workflows (level 1+)
st.markdown("#### 🌿 Workflows")
emp_cols = st.columns(4)

with emp_cols[0]:
    if st.button("🌱 Employee Plantings", use_container_width=True):
        st.switch_page("pages/employee_plantings.py")
with emp_cols[1]:
    if st.button("📋 Employee Pitch", use_container_width=True):
        st.switch_page("pages/employee_pitch.py")
with emp_cols[2]:
    if st.button("🏷️ Label Generator", use_container_width=True):
        st.switch_page("pages/label_generator.py")
with emp_cols[3]:
    pass

# Admin workflows (level 2+)
if role_int >= ROLE_ADMIN:
    st.markdown("#### 📊 Management")
    admin_cols = st.columns(4)

    with admin_cols[0]:
        if st.button("📦 Inventory Manager", use_container_width=True):
            st.switch_page("pages/inventory_manager.py")
    with admin_cols[1]:
        if st.button("🌱 Plantings Tracker", use_container_width=True):
            st.switch_page("pages/plantings.py")
    with admin_cols[2]:
        if st.button("📦 Order Tracker", use_container_width=True):
            st.switch_page("pages/order_tracking.py")
    with admin_cols[3]:
        if st.button("🔧 Admin Tables", use_container_width=True):
            st.switch_page("pages/admin_landing.py")

# Superadmin only (level 3)
if role_int >= ROLE_SUPERADMIN:
    st.markdown("#### 🔐 Administration")
    super_cols = st.columns(4)

    with super_cols[0]:
        if st.button("👤 User Management", use_container_width=True):
            st.switch_page("pages/users.py")
    with super_cols[1]:
        pass
    with super_cols[2]:
        pass
    with super_cols[3]:
        pass

st.markdown("---")
st.caption("Edgewater Database + UI Migrated & Built by Ian Solberg")
