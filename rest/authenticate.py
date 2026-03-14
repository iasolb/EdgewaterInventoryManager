"""
Authentication module for Edgewater Inventory Management System

Login flow:
    - Email + password correct + active → through to role-gated pages
    - Email exists but password wrong → offer password reset option
    - Password reset → user sets new password, account set to pending,
      original role preserved, admin must reactivate
    - New account → pending employee by default, admin must activate

Account statuses (T_Users.Active):
    0 = Pending  (new account or password reset, awaiting admin activation)
    1 = Active   (full access per role)
    2 = Denied   (admin rejected, blocked from login, email locked)

No non-active users get past edgewater.py.
"""

import bcrypt
import streamlit as st
import logging
from datetime import datetime

from database import get_db_session
from models import Users, Passwords
from sqlalchemy import func

logger = logging.getLogger(__name__)

# ================================================================
# ROLE CONSTANTS
# ================================================================

ROLE_EMPLOYEE = 1
ROLE_ADMIN = 2
ROLE_SUPERADMIN = 3

ROLE_MAP = {
    "employee": ROLE_EMPLOYEE,
    "admin": ROLE_ADMIN,
    "superadmin": ROLE_SUPERADMIN,
}

ROLE_LABELS = {
    ROLE_EMPLOYEE: "Farm Worker",
    ROLE_ADMIN: "Editor",
    ROLE_SUPERADMIN: "Super Admin",
}

# ================================================================
# ACCOUNT STATUS CONSTANTS
# ================================================================

STATUS_PENDING = 0
STATUS_ACTIVE = 1
STATUS_DENIED = 2

STATUS_LABELS = {
    STATUS_PENDING: "Pending",
    STATUS_ACTIVE: "Active",
    STATUS_DENIED: "Denied",
}


class Authenticate:

    # ================================================================
    # LOGIN
    # ================================================================

    def login(self, email: str, password: str) -> tuple[bool, str, str]:
        """
        Validate email + password.
        Returns (success, message, hint).
        hint is one of: "ok", "bad_password", "no_user", "inactive", "error"
        """
        email = email.strip().lower()

        if not email or not password:
            return False, "Email and password are required.", "error"

        try:
            with get_db_session() as session:
                user = (
                    session.query(Users)
                    .filter(func.lower(Users.Email) == email)
                    .first()
                )

                if user is None:
                    return False, "Invalid email or password.", "no_user"

                pw_record = (
                    session.query(Passwords)
                    .filter(Passwords.UserID == user.UserID)
                    .first()
                )

                if pw_record is None:
                    return (
                        False,
                        "Account not configured. Contact an administrator.",
                        "error",
                    )

                # Verify password
                if not self._verify_password(password, pw_record.PasswordHash):
                    return False, "Invalid email or password.", "bad_password"

                # Check account status
                if user.Active == STATUS_DENIED:
                    return (
                        False,
                        "Your account request has been denied. Contact an administrator.",
                        "denied",
                    )

                if user.Active == STATUS_PENDING:
                    return (
                        False,
                        "Your account is not yet active. Please contact an administrator.",
                        "inactive",
                    )

                # Success
                pw_record.LastLogin = datetime.now()
                pw_record.UpdatedAt = datetime.now()
                session.commit()

                permission_level = (user.PermissionLevel or "employee").lower()
                role_int = ROLE_MAP.get(permission_level, ROLE_EMPLOYEE)

                st.session_state["auth_user"] = {
                    "user_id": user.UserID,
                    "email": user.Email,
                    "role": user.Role or "User",
                    "permission_level": permission_level,
                    "role_int": role_int,
                    "logged_in_at": datetime.now(),
                }
                st.session_state["auth_authenticated"] = True

                return True, f"Welcome, {user.Role or user.Email}!", "ok"

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, "An error occurred during login.", "error"

    def logout(self):
        st.session_state.pop("auth_user", None)
        st.session_state.pop("auth_authenticated", None)

    # ================================================================
    # SELF-REGISTRATION
    # ================================================================

    def register(self, email: str, password: str) -> tuple[bool, str]:
        """
        Create a new account. Defaults to inactive employee.
        Admin must activate before user can log in.
        """
        email = email.strip().lower()

        if not email or not password:
            return False, "Email and password are required."
        if len(password) < 8:
            return False, "Password must be at least 8 characters."

        try:
            with get_db_session() as session:
                existing = (
                    session.query(Users)
                    .filter(func.lower(Users.Email) == email)
                    .first()
                )
                if existing:
                    return False, "An account with this email already exists."

                new_user = Users(
                    Role="Farm Worker",
                    PermissionLevel="employee",
                    Email=email,
                    Active=0,
                    CreatedAt=datetime.now(),
                    UpdatedAt=datetime.now(),
                )
                session.add(new_user)
                session.flush()

                new_pw = Passwords(
                    UserID=new_user.UserID,
                    PasswordHash=self._hash_password(password),
                    LastPasswordChange=datetime.now(),
                    FailedLoginAttempts=0,
                    CreatedAt=datetime.now(),
                    UpdatedAt=datetime.now(),
                )
                session.add(new_pw)
                session.commit()

                return True, (
                    "Account created! An administrator must activate your "
                    "account before you can log in."
                )

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, f"Error creating account: {e}"

    # ================================================================
    # PASSWORD RESET (self-service, deactivates account)
    # ================================================================

    def reset_password(self, email: str, new_password: str) -> tuple[bool, str]:
        """
        User resets their own password. This deactivates the account
        (requires admin reactivation) but preserves their original role.
        """
        email = email.strip().lower()

        if not email or not new_password:
            return False, "Email and new password are required."
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters."

        try:
            with get_db_session() as session:
                user = (
                    session.query(Users)
                    .filter(func.lower(Users.Email) == email)
                    .first()
                )
                if user is None:
                    # Don't reveal whether email exists
                    return False, "If that email exists, the password has been reset."

                pw_record = (
                    session.query(Passwords)
                    .filter(Passwords.UserID == user.UserID)
                    .first()
                )
                if pw_record is None:
                    return False, "Account not configured. Contact an administrator."

                # Update password
                pw_record.PasswordHash = self._hash_password(new_password)
                pw_record.LastPasswordChange = datetime.now()
                pw_record.UpdatedAt = datetime.now()

                # Deactivate — preserves Role and PermissionLevel
                user.Active = 0
                user.UpdatedAt = datetime.now()

                session.commit()

                return True, (
                    "Password has been reset. Your account has been deactivated "
                    "and will need to be reactivated by an administrator."
                )

        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return False, "An error occurred. Please try again."

    # ================================================================
    # ADMIN: USER MANAGEMENT HELPERS
    # ================================================================

    def activate_user(self, user_id: int) -> tuple[bool, str]:
        """Admin activates a user account (sets Active=1)."""
        try:
            with get_db_session() as session:
                user = session.query(Users).filter(Users.UserID == user_id).first()
                if user is None:
                    return False, "User not found."
                user.Active = STATUS_ACTIVE
                user.UpdatedAt = datetime.now()
                session.commit()
                return True, f"User {user.Email} activated."
        except Exception as e:
            logger.error(f"Activate user error: {e}")
            return False, f"Error: {e}"

    def deactivate_user(self, user_id: int) -> tuple[bool, str]:
        """Admin deactivates a user (sets Active=0, back to pending)."""
        try:
            with get_db_session() as session:
                user = session.query(Users).filter(Users.UserID == user_id).first()
                if user is None:
                    return False, "User not found."
                user.Active = STATUS_PENDING
                user.UpdatedAt = datetime.now()
                session.commit()
                return True, f"User {user.Email} deactivated."
        except Exception as e:
            logger.error(f"Deactivate user error: {e}")
            return False, f"Error: {e}"

    def deny_user(self, user_id: int) -> tuple[bool, str]:
        """Admin denies a user (sets Active=2). Email is locked, removed from queue."""
        try:
            with get_db_session() as session:
                user = session.query(Users).filter(Users.UserID == user_id).first()
                if user is None:
                    return False, "User not found."
                user.Active = STATUS_DENIED
                user.UpdatedAt = datetime.now()
                session.commit()
                return True, f"User {user.Email} denied."
        except Exception as e:
            logger.error(f"Deny user error: {e}")
            return False, f"Error: {e}"

    def delete_user(self, user_id: int) -> tuple[bool, str]:
        """Permanently delete a user and their password record."""
        try:
            with get_db_session() as session:
                user = session.query(Users).filter(Users.UserID == user_id).first()
                if user is None:
                    return False, "User not found."
                email = user.Email
                # Delete password record first
                session.query(Passwords).filter(Passwords.UserID == user_id).delete()
                session.delete(user)
                session.commit()
                return True, f"User {email} permanently deleted."
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            return False, f"Error: {e}"

    def get_pending_users(self) -> list[dict]:
        """Get all pending users (Active=0)."""
        return self._get_users_by_status(STATUS_PENDING)

    def get_denied_users(self) -> list[dict]:
        """Get all denied users (Active=2)."""
        return self._get_users_by_status(STATUS_DENIED)

    def get_active_users(self) -> list[dict]:
        """Get all active users (Active=1)."""
        return self._get_users_by_status(STATUS_ACTIVE)

    def get_all_users(self) -> list[dict]:
        """Get all users for user management page."""
        try:
            with get_db_session() as session:
                users = session.query(Users).all()
                return [self._user_to_dict(u) for u in users]
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            return []

    def _get_users_by_status(self, status: int) -> list[dict]:
        """Get users filtered by Active status."""
        try:
            with get_db_session() as session:
                users = session.query(Users).filter(Users.Active == status).all()
                return [self._user_to_dict(u) for u in users]
        except Exception as e:
            logger.error(f"Get users by status error: {e}")
            return []

    @staticmethod
    def _user_to_dict(u) -> dict:
        return {
            "user_id": u.UserID,
            "email": u.Email,
            "role": u.Role,
            "permission_level": u.PermissionLevel,
            "status": STATUS_LABELS.get(u.Active, "Unknown"),
            "active": u.Active,
            "created_at": u.CreatedAt,
        }

    def update_user_role(
        self, user_id: int, role: str, permission_level: str
    ) -> tuple[bool, str]:
        """Admin updates a user's role."""
        if permission_level not in ROLE_MAP:
            return False, f"Invalid permission level. Use: {list(ROLE_MAP.keys())}"
        try:
            with get_db_session() as session:
                user = session.query(Users).filter(Users.UserID == user_id).first()
                if user is None:
                    return False, "User not found."
                user.Role = role
                user.PermissionLevel = permission_level
                user.UpdatedAt = datetime.now()
                session.commit()
                return (
                    True,
                    f"User {user.Email} updated to {role} ({permission_level}).",
                )
        except Exception as e:
            logger.error(f"Update user role error: {e}")
            return False, f"Error: {e}"

    def create_user(
        self,
        email: str,
        password: str,
        role: str,
        permission_level: str,
        active: bool = True,
    ) -> tuple[bool, str]:
        """Admin-created user with specific role, optionally active immediately."""
        email = email.strip().lower()
        if not email or not password:
            return False, "Email and password are required."
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        if permission_level not in ROLE_MAP:
            return False, f"Invalid permission level. Use: {list(ROLE_MAP.keys())}"

        try:
            with get_db_session() as session:
                existing = (
                    session.query(Users)
                    .filter(func.lower(Users.Email) == email)
                    .first()
                )
                if existing:
                    return False, "A user with this email already exists."

                new_user = Users(
                    Role=role,
                    PermissionLevel=permission_level,
                    Email=email,
                    Active=1 if active else 0,
                    CreatedAt=datetime.now(),
                    UpdatedAt=datetime.now(),
                )
                session.add(new_user)
                session.flush()

                new_pw = Passwords(
                    UserID=new_user.UserID,
                    PasswordHash=self._hash_password(password),
                    LastPasswordChange=datetime.now(),
                    FailedLoginAttempts=0,
                    CreatedAt=datetime.now(),
                    UpdatedAt=datetime.now(),
                )
                session.add(new_pw)
                session.commit()
                return True, f"User {email} created."

        except Exception as e:
            logger.error(f"Create user error: {e}")
            return False, f"Error: {e}"

    # ================================================================
    # SESSION CHECKS
    # ================================================================

    def is_authenticated(self) -> bool:
        return st.session_state.get("auth_authenticated", False)

    def get_user(self) -> dict | None:
        if not self.is_authenticated():
            return None
        return st.session_state.get("auth_user")

    def get_role_int(self) -> int:
        user = self.get_user()
        return user["role_int"] if user else 0

    def has_role(self, min_level: int) -> bool:
        return self.get_role_int() >= min_level

    # ================================================================
    # PAGE GATES
    # ================================================================

    def require_auth(self):
        """Must be logged in. Redirects to login if not."""
        if not self.is_authenticated():
            st.warning("Please log in to access this page.")
            if st.button("← Go to Login"):
                st.switch_page("edgewater.py")
            st.stop()

    def require_role(self, min_level: int):
        """Must be logged in AND have sufficient role."""
        self.require_auth()
        if not self.has_role(min_level):
            role_name = ROLE_LABELS.get(min_level, f"Level {min_level}")
            st.error(
                f"Access denied. This page requires {role_name} permissions or higher."
            )
            if st.button("← Back to Home"):
                st.switch_page("edgewater.py")
            st.stop()

    def show_user_info_sidebar(self):
        """Render user info + logout in sidebar."""
        if not self.is_authenticated():
            return
        user = self.get_user()
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**{user['role']}**")
            st.caption(user["email"])
            if st.button("🚪 Logout", use_container_width=True):
                self.logout()
                st.switch_page("edgewater.py")

    # ================================================================
    # HELPERS: email existence check (used by login page UI)
    # ================================================================

    def email_exists(self, email: str) -> bool:
        """Check if an email is registered. Used by UI to show reset option."""
        try:
            with get_db_session() as session:
                return (
                    session.query(Users)
                    .filter(func.lower(Users.Email) == email.strip().lower())
                    .first()
                    is not None
                )
        except Exception:
            return False

    # ================================================================
    # PRIVATE
    # ================================================================

    @staticmethod
    def _hash_password(plain_password: str) -> str:
        return bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(rounds=10),
        ).decode("utf-8")

    @staticmethod
    def _verify_password(plain_password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed.encode("utf-8"),
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
