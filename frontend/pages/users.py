import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))
from rest.api import EdgewaterAPI
from models import Users as USR
from payloads import UserPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Users Administration",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("user_cache", api.get_user_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the user cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("user_cache", api.get_user_full)
    st.success("✅ Data refreshed!")


def create_user_from_form(form_data: dict) -> Optional[dict]:
    """Create a new user"""
    try:
        result = api.table_add_user(
            Role=str(form_data["Role"]),
            PermissionLevel=form_data.get("PermissionLevel"),
            Email=form_data.get("Email"),
            Active=form_data.get("Active", True),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating user: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_user(user_id: int, updates: dict) -> bool:
    """Update a user"""
    try:
        allowed_fields = {"Role", "PermissionLevel", "Email", "Active"}

        result = api.generic_update(
            model_class=USR,
            id_column="UserID",
            id_value=user_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated User {user_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating user {user_id}: {e}")
        logger.error(f"Update failed for User {user_id}: {e}")
        return False


def delete_user(user_id: int) -> bool:
    """Delete a user"""
    try:
        return api._delete(USR, "UserID", user_id)
    except Exception as e:
        st.error(f"❌ Error deleting user {user_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("👥 Users Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New User", expanded=st.session_state.show_add_form):
    st.write("### Create New User")

    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            form_role = st.text_input("Role *", key="form_role")
            form_permission = st.text_input("Permission Level", key="form_permission")

        with col2:
            form_email = st.text_input("Email *", key="form_email")
            form_active = st.checkbox("Active", value=True, key="form_active")

        submitted = st.form_submit_button(
            "💾 Create User", type="primary", use_container_width=True
        )

        if submitted:
            if not form_role or not form_email:
                st.error("❌ Role and Email are required!")
            else:
                form_data = {
                    "Role": form_role,
                    "PermissionLevel": form_permission or None,
                    "Email": form_email,
                    "Active": form_active,
                }

                result = create_user_from_form(form_data)
                if result:
                    st.success(
                        f"✅ User '{form_email}' created! (ID: {result['UserID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    search_term = st.text_input(
        "Search Users",
        placeholder="Search by role or email...",
        key="search_term",
    )

with filter_col2:
    active_filter = st.selectbox(
        "Filter by Status",
        options=["All", "Active", "Inactive"],
        key="active_filter",
    )

# Apply filters
filtered_df = api.user_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["Role"].fillna("").str.contains(
        search_term, case=False
    ) | filtered_df["Email"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

# Active filter
if active_filter == "Active":
    filtered_df = filtered_df[filtered_df["Active"] == 1]
elif active_filter == "Inactive":
    filtered_df = filtered_df[filtered_df["Active"] == 0]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Users ({len(filtered_df)} records)")

# Action buttons
action_col1, action_col2 = st.columns([1, 5])

with action_col1:
    if st.button(
        "✏️ Edit Mode" if not st.session_state.edit_mode else "🔒 View Mode",
        use_container_width=True,
        type="primary" if not st.session_state.edit_mode else "secondary",
    ):
        st.session_state.edit_mode = not st.session_state.edit_mode
        st.rerun()

with action_col2:
    if st.button("📥 Export CSV", use_container_width=True):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "UserID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Role": st.column_config.TextColumn("Role", width="medium", required=True),
    "PermissionLevel": st.column_config.TextColumn("Permission Level", width="medium"),
    "Email": st.column_config.TextColumn("Email", width="medium", required=True),
    "Active": st.column_config.CheckboxColumn("Active", width="small"),
    "CreatedAt": st.column_config.DatetimeColumn("Created At", width="medium"),
    "UpdatedAt": st.column_config.DatetimeColumn("Updated At", width="medium"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="users_editor",
    )

    if not edited_df.equals(filtered_df):
        st.warning(f"⚠️ Unsaved changes detected!")

        save_col1, save_col2 = st.columns([1, 5])

        with save_col1:
            if st.button(
                "💾 Save All Changes", type="primary", use_container_width=True
            ):
                success_count = 0
                error_count = 0

                for idx in edited_df.index:
                    user_id = edited_df.loc[idx, "UserID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col not in ["UserID", "CreatedAt", "UpdatedAt"]:
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_user(user_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} users")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} users")

                refresh_cache()
                st.rerun()

        with save_col2:
            if st.button("🔄 Discard Changes", use_container_width=True):
                st.rerun()
else:
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
    )

# ==================== BULK OPERATIONS ====================
st.divider()
with st.expander("🔧 Bulk Operations"):
    st.write("### Bulk Actions")

    bulk_col1, bulk_col2 = st.columns(2)

    with bulk_col1:
        st.write("**Activate/Deactivate Users**")
        bulk_user_ids = st.text_input(
            "User IDs (comma-separated)", key="bulk_user_ids", placeholder="1,2,3"
        )
        activate_action = st.selectbox(
            "Action", options=["Activate", "Deactivate"], key="activate_action"
        )
        if st.button("Update Status", key="bulk_status_btn"):
            if bulk_user_ids:
                ids = [int(x.strip()) for x in bulk_user_ids.split(",")]
                active_value = 1 if activate_action == "Activate" else 0
                success = sum([update_user(id, {"Active": active_value}) for id in ids])
                st.success(f"✅ Updated status for {success}/{len(ids)} users")
                refresh_cache()
                st.rerun()

    with bulk_col2:
        st.write("**Delete Users**")
        st.warning("⚠️ Permanent action!")
        delete_ids = st.text_input(
            "User IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
        )
        confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
        if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
            if delete_ids:
                ids = [int(x.strip()) for x in delete_ids.split(",")]
                success = sum([delete_user(id) for id in ids])
                st.success(f"✅ Deleted {success}/{len(ids)} users")
                refresh_cache()
                st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total users: {len(api.user_cache)}"
)
