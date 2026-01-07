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
from models import Shipper as SHP
from payloads import ShipperPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Shippers Administration",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("shipper_cache", api.get_shipper_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the shipper cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("shipper_cache", api.get_shipper_full)
    st.success("✅ Data refreshed!")


def create_shipper_from_form(form_data: dict) -> Optional[dict]:
    """Create a new shipper"""
    try:
        result = api.table_add_shipper(
            Shipper=str(form_data["Shipper"]),
            AccountNumber=form_data.get("AccountNumber"),
            Phone=form_data.get("Phone"),
            ContactPerson=form_data.get("ContactPerson"),
            Address1=form_data.get("Address1"),
            Address2=form_data.get("Address2"),
            City=form_data.get("City"),
            State=form_data.get("State"),
            Zip=form_data.get("Zip"),
            ShipperComments=form_data.get("ShipperComments"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating shipper: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_shipper(shipper_id: int, updates: dict) -> bool:
    """Update a shipper"""
    try:
        allowed_fields = {
            "Shipper",
            "AccountNumber",
            "Phone",
            "ContactPerson",
            "Address1",
            "Address2",
            "City",
            "State",
            "Zip",
            "ShipperComments",
        }

        result = api.generic_update(
            model_class=SHP,
            id_column="ShipperID",
            id_value=shipper_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Shipper {shipper_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating shipper {shipper_id}: {e}")
        logger.error(f"Update failed for Shipper {shipper_id}: {e}")
        return False


def delete_shipper(shipper_id: int) -> bool:
    """Delete a shipper"""
    try:
        return api._delete(SHP, "ShipperID", shipper_id)
    except Exception as e:
        st.error(f"❌ Error deleting shipper {shipper_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🚚 Shippers Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Shipper", expanded=st.session_state.show_add_form):
    st.write("### Create New Shipper")

    with st.form("add_shipper_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_shipper = st.text_input("Shipper Name *", key="form_shipper")
            form_account = st.text_input("Account Number", key="form_account")
            form_phone = st.text_input("Phone", key="form_phone")
            form_contact = st.text_input("Contact Person", key="form_contact")

        with col2:
            form_address1 = st.text_input("Address Line 1", key="form_address1")
            form_address2 = st.text_input("Address Line 2", key="form_address2")
            form_city = st.text_input("City", key="form_city")

        with col3:
            form_state = st.text_input("State", key="form_state", max_chars=2)
            form_zip = st.text_input("ZIP", key="form_zip")
            form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Shipper", type="primary", use_container_width=True
        )

        if submitted:
            if not form_shipper:
                st.error("❌ Shipper name is required!")
            else:
                form_data = {
                    "Shipper": form_shipper,
                    "AccountNumber": form_account or None,
                    "Phone": form_phone or None,
                    "ContactPerson": form_contact or None,
                    "Address1": form_address1 or None,
                    "Address2": form_address2 or None,
                    "City": form_city or None,
                    "State": form_state or None,
                    "Zip": form_zip or None,
                    "ShipperComments": form_comments or None,
                }

                result = create_shipper_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Shipper '{form_shipper}' created! (ID: {result['ShipperID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Shippers",
    placeholder="Search by name, city, or contact...",
    key="search_term",
)

# Apply filters
filtered_df = api.shipper_cache.copy()

# Search filter
if search_term:
    mask = (
        filtered_df["Shipper"].fillna("").str.contains(search_term, case=False)
        | filtered_df["City"].fillna("").str.contains(search_term, case=False)
        | filtered_df["ContactPerson"].fillna("").str.contains(search_term, case=False)
    )
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Shippers ({len(filtered_df)} records)")

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
            file_name=f"shippers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "ShipperID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Shipper": st.column_config.TextColumn(
        "Shipper Name", width="medium", required=True
    ),
    "AccountNumber": st.column_config.TextColumn("Account #", width="small"),
    "Phone": st.column_config.TextColumn("Phone", width="small"),
    "ContactPerson": st.column_config.TextColumn("Contact", width="medium"),
    "Address1": st.column_config.TextColumn("Address 1", width="medium"),
    "Address2": st.column_config.TextColumn("Address 2", width="medium"),
    "City": st.column_config.TextColumn("City", width="small"),
    "State": st.column_config.TextColumn("State", width="small"),
    "Zip": st.column_config.TextColumn("ZIP", width="small"),
    "ShipperComments": st.column_config.TextColumn("Comments", width="large"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="shippers_editor",
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
                    shipper_id = edited_df.loc[idx, "ShipperID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "ShipperID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_shipper(shipper_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} shippers")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} shippers")

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

    st.write("**Delete Shippers**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Shipper IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_shipper(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} shippers")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total shippers: {len(api.shipper_cache)}"
)
