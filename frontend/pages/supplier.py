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
from models import Supplier as SUP
from payloads import SupplierPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Suppliers Administration",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("supplier_cache", api.get_supplier_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the supplier cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("supplier_cache", api.get_supplier_full)
    st.success("✅ Data refreshed!")


def create_supplier_from_form(form_data: dict) -> Optional[dict]:
    """Create a new supplier"""
    try:
        result = api.table_add_supplier(
            Supplier=str(form_data["Supplier"]),
            AccountNumber=form_data.get("AccountNumber"),
            Phone=form_data.get("Phone"),
            Fax=form_data.get("Fax"),
            WebSite=form_data.get("WebSite"),
            Email=form_data.get("Email"),
            ContactPerson=form_data.get("ContactPerson"),
            Address1=form_data.get("Address1"),
            Address2=form_data.get("Address2"),
            City=form_data.get("City"),
            State=form_data.get("State"),
            Zip=form_data.get("Zip"),
            SupplierComments=form_data.get("SupplierComments"),
            SupplierType=form_data.get("SupplierType"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating supplier: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_supplier(supplier_id: int, updates: dict) -> bool:
    """Update a supplier"""
    try:
        allowed_fields = {
            "Supplier",
            "AccountNumber",
            "Phone",
            "Fax",
            "WebSite",
            "Email",
            "ContactPerson",
            "Address1",
            "Address2",
            "City",
            "State",
            "Zip",
            "SupplierComments",
            "SupplierType",
        }

        result = api.generic_update(
            model_class=SUP,
            id_column="SupplierID",
            id_value=supplier_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Supplier {supplier_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating supplier {supplier_id}: {e}")
        logger.error(f"Update failed for Supplier {supplier_id}: {e}")
        return False


def delete_supplier(supplier_id: int) -> bool:
    """Delete a supplier"""
    try:
        return api._delete(SUP, "SupplierID", supplier_id)
    except Exception as e:
        st.error(f"❌ Error deleting supplier {supplier_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🏭 Suppliers Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Supplier", expanded=st.session_state.show_add_form):
    st.write("### Create New Supplier")

    with st.form("add_supplier_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_supplier = st.text_input("Supplier Name *", key="form_supplier")
            form_account = st.text_input("Account Number", key="form_account")
            form_supplier_type = st.text_input(
                "Supplier Type", key="form_supplier_type"
            )
            form_contact = st.text_input("Contact Person", key="form_contact")

        with col2:
            form_phone = st.text_input("Phone", key="form_phone")
            form_fax = st.text_input("Fax", key="form_fax")
            form_email = st.text_input("Email", key="form_email")
            form_website = st.text_input("Website", key="form_website")

        with col3:
            form_address1 = st.text_input("Address Line 1", key="form_address1")
            form_address2 = st.text_input("Address Line 2", key="form_address2")
            form_city = st.text_input("City", key="form_city")
            col_a, col_b = st.columns(2)
            with col_a:
                form_state = st.text_input("State", key="form_state", max_chars=2)
            with col_b:
                form_zip = st.text_input("ZIP", key="form_zip")

        form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Supplier", type="primary", use_container_width=True
        )

        if submitted:
            if not form_supplier:
                st.error("❌ Supplier name is required!")
            else:
                form_data = {
                    "Supplier": form_supplier,
                    "AccountNumber": form_account or None,
                    "Phone": form_phone or None,
                    "Fax": form_fax or None,
                    "WebSite": form_website or None,
                    "Email": form_email or None,
                    "ContactPerson": form_contact or None,
                    "Address1": form_address1 or None,
                    "Address2": form_address2 or None,
                    "City": form_city or None,
                    "State": form_state or None,
                    "Zip": form_zip or None,
                    "SupplierComments": form_comments or None,
                    "SupplierType": form_supplier_type or None,
                }

                result = create_supplier_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Supplier '{form_supplier}' created! (ID: {result['SupplierID']})"
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
        "Search Suppliers",
        placeholder="Search by name, city, or contact...",
        key="search_term",
    )

with filter_col2:
    type_filter = st.multiselect(
        "Filter by Type",
        options=api.supplier_cache["SupplierType"].dropna().unique().tolist(),
        key="type_filter",
    )

# Apply filters
filtered_df = api.supplier_cache.copy()

# Search filter
if search_term:
    mask = (
        filtered_df["Supplier"].fillna("").str.contains(search_term, case=False)
        | filtered_df["City"].fillna("").str.contains(search_term, case=False)
        | filtered_df["ContactPerson"].fillna("").str.contains(search_term, case=False)
    )
    filtered_df = filtered_df[mask]

# Type filter
if type_filter:
    filtered_df = filtered_df[filtered_df["SupplierType"].isin(type_filter)]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Suppliers ({len(filtered_df)} records)")

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
            file_name=f"suppliers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "SupplierID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Supplier": st.column_config.TextColumn(
        "Supplier Name", width="medium", required=True
    ),
    "SupplierType": st.column_config.TextColumn("Type", width="small"),
    "AccountNumber": st.column_config.TextColumn("Account #", width="small"),
    "Phone": st.column_config.TextColumn("Phone", width="small"),
    "Fax": st.column_config.TextColumn("Fax", width="small"),
    "Email": st.column_config.TextColumn("Email", width="medium"),
    "WebSite": st.column_config.TextColumn("Website", width="medium"),
    "ContactPerson": st.column_config.TextColumn("Contact", width="medium"),
    "Address1": st.column_config.TextColumn("Address 1", width="medium"),
    "Address2": st.column_config.TextColumn("Address 2", width="medium"),
    "City": st.column_config.TextColumn("City", width="small"),
    "State": st.column_config.TextColumn("State", width="small"),
    "Zip": st.column_config.TextColumn("ZIP", width="small"),
    "SupplierComments": st.column_config.TextColumn("Comments", width="large"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="suppliers_editor",
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
                    supplier_id = edited_df.loc[idx, "SupplierID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "SupplierID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_supplier(supplier_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} suppliers")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} suppliers")

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

    st.write("**Delete Suppliers**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Supplier IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_supplier(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} suppliers")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total suppliers: {len(api.supplier_cache)}"
)
