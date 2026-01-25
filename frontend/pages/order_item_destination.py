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
from models import OrderItemDestination as OID
from payloads import OrderItemDestinationPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Order Item Destinations Administration",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("order_item_destination_cache", api.get_order_item_destination_full)
api.reset_cache("unit_cache", api.get_unit_full)
api.reset_cache("location_cache", api.get_location_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache(
            "order_item_destination_cache", api.get_order_item_destination_full
        )
        api.reset_cache("unit_cache", api.get_unit_full)
        api.reset_cache("location_cache", api.get_location_full)
    st.success("✅ Data refreshed!")


def create_order_item_destination_from_form(form_data: dict) -> Optional[dict]:
    """Create a new order item destination"""
    try:
        result = api.table_add_order_item_destination(
            OrderItemID=int(form_data["OrderItemID"]),
            Count=int(form_data["Count"]),
            UnitID=int(form_data["UnitID"]),
            LocationID=int(form_data["LocationID"]),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating order item destination: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_order_item_destination(destination_id: int, updates: dict) -> bool:
    """Update an order item destination"""
    try:
        allowed_fields = {"OrderItemID", "Count", "UnitID", "LocationID"}

        result = api.generic_update(
            model_class=OID,
            id_column="OrderItemDestinationID",
            id_value=destination_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated OrderItemDestination {destination_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating order item destination {destination_id}: {e}")
        logger.error(f"Update failed for OrderItemDestination {destination_id}: {e}")
        return False


def delete_order_item_destination(destination_id: int) -> bool:
    """Delete an order item destination"""
    try:
        return api._delete(OID, "OrderItemDestinationID", destination_id)
    except Exception as e:
        st.error(f"❌ Error deleting order item destination {destination_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🎯 Order Item Destinations Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander(
    "➕ Add New Order Item Destination", expanded=st.session_state.show_add_form
):
    st.write("### Create New Order Item Destination")

    # Prepare lookup dictionaries
    units_dict = api.unit_cache.apply(
        lambda x: f"{x['UnitSize']} {x['UnitType']}", axis=1
    ).to_dict()
    locations_dict = api.location_cache.set_index("LocationID")["Location"].to_dict()

    with st.form("add_order_item_destination_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            form_order_item_id = st.number_input(
                "Order Item ID *", min_value=1, step=1, key="form_order_item_id"
            )
            form_count = st.number_input(
                "Count *", min_value=1, step=1, key="form_count"
            )

        with col2:
            form_unit_id = st.selectbox(
                "Unit *",
                options=list(units_dict.keys()),
                format_func=lambda x: units_dict[x],
                key="form_unit_id",
            )
            form_location_id = st.selectbox(
                "Location *",
                options=list(locations_dict.keys()),
                format_func=lambda x: locations_dict[x],
                key="form_location_id",
            )

        submitted = st.form_submit_button(
            "💾 Create Destination", type="primary", use_container_width=True
        )

        if submitted:
            if form_count <= 0:
                st.error("❌ Count must be greater than 0!")
            else:
                form_data = {
                    "OrderItemID": form_order_item_id,
                    "Count": form_count,
                    "UnitID": form_unit_id,
                    "LocationID": form_location_id,
                }

                result = create_order_item_destination_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Order item destination created! (ID: {result['OrderItemDestinationID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    order_item_filter = st.number_input(
        "Filter by Order Item ID",
        min_value=0,
        value=0,
        step=1,
        key="order_item_filter",
    )

with filter_col2:
    location_filter = st.multiselect(
        "Filter by Location",
        options=api.location_cache["Location"].unique().tolist(),
        key="location_filter",
    )

with filter_col3:
    count_min = st.number_input(
        "Min Count", min_value=0, value=0, step=1, key="count_min"
    )

# Apply filters
filtered_df = api.order_item_destination_cache.copy()

# Order Item filter
if order_item_filter > 0:
    filtered_df = filtered_df[filtered_df["OrderItemID"] == order_item_filter]

# Location filter
if location_filter:
    location_ids = api.location_cache[
        api.location_cache["Location"].isin(location_filter)
    ]["LocationID"].tolist()
    filtered_df = filtered_df[filtered_df["LocationID"].isin(location_ids)]

# Count filter
if count_min > 0:
    filtered_df = filtered_df[filtered_df["Count"] >= count_min]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Order Item Destinations ({len(filtered_df)} records)")

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
            file_name=f"order_item_destinations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "OrderItemDestinationID": st.column_config.NumberColumn(
        "ID", disabled=True, width="small"
    ),
    "OrderItemID": st.column_config.NumberColumn("Order Item ID", width="medium"),
    "Count": st.column_config.NumberColumn("Count", width="small"),
    "UnitID": st.column_config.NumberColumn("Unit ID", width="small"),
    "LocationID": st.column_config.NumberColumn("Location ID", width="small"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="order_item_destinations_editor",
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
                    destination_id = edited_df.loc[idx, "OrderItemDestinationID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "OrderItemDestinationID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_order_item_destination(destination_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} destinations")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} destinations")

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

    st.write("**Delete Order Item Destinations**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Destination IDs (comma-separated)",
        key="bulk_delete_ids",
        placeholder="1,2,3",
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_order_item_destination(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} destinations")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total order item destinations: {len(api.order_item_destination_cache)}"
)
