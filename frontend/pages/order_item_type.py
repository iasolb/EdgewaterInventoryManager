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
from models import OrderItemType as ORIT
from payloads import OrderItemTypePayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Order Item Types Administration",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("order_item_type_cache", api.get_order_item_type_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the order item type cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("order_item_type_cache", api.get_order_item_type_full)
    st.success("✅ Data refreshed!")


def create_order_item_type_from_form(form_data: dict) -> Optional[dict]:
    """Create a new order item type"""
    try:
        result = api.table_add_order_item_type(
            OrderItemType=str(form_data["OrderItemType"])
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating order item type: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_order_item_type(type_id: int, updates: dict) -> bool:
    """Update an order item type"""
    try:
        allowed_fields = {"OrderItemType"}

        result = api.generic_update(
            model_class=ORIT,
            id_column="OrderItemTypeID",
            id_value=type_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated OrderItemType {type_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating order item type {type_id}: {e}")
        logger.error(f"Update failed for OrderItemType {type_id}: {e}")
        return False


def delete_order_item_type(type_id: int) -> bool:
    """Delete an order item type"""
    try:
        return api._delete(ORIT, "OrderItemTypeID", type_id)
    except Exception as e:
        st.error(f"❌ Error deleting order item type {type_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📑 Order Item Types Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Order Item Type", expanded=st.session_state.show_add_form):
    st.write("### Create New Order Item Type")

    with st.form("add_order_item_type_form", clear_on_submit=True):
        form_type = st.text_input("Order Item Type Name *", key="form_type")

        submitted = st.form_submit_button(
            "💾 Create Order Item Type", type="primary", use_container_width=True
        )

        if submitted:
            if not form_type:
                st.error("❌ Order item type name is required!")
            else:
                form_data = {"OrderItemType": form_type}

                result = create_order_item_type_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Order Item Type '{form_type}' created! (ID: {result['OrderItemTypeID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Order Item Types",
    placeholder="Search by type name...",
    key="search_term",
)

# Apply filters
filtered_df = api.order_item_type_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["OrderItemType"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Order Item Types ({len(filtered_df)} records)")

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
            file_name=f"order_item_types_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "OrderItemTypeID": st.column_config.NumberColumn(
        "ID", disabled=True, width="small"
    ),
    "OrderItemType": st.column_config.TextColumn(
        "Type Name", width="large", required=True
    ),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="order_item_types_editor",
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
                    type_id = edited_df.loc[idx, "OrderItemTypeID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "OrderItemTypeID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_order_item_type(type_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} order item types")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} order item types")

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

    st.write("**Delete Order Item Types**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Type IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_order_item_type(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} order item types")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total order item types: {len(api.order_item_type_cache)}"
)
