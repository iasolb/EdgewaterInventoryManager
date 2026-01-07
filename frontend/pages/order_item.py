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
from models import OrderItem as ORI
from payloads import OrderItemPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Order Items Administration",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("order_item_cache", api.get_order_item_full)
api.reset_cache("order_cache", api.get_order_full)
api.reset_cache("item_cache", api.get_item_full)
api.reset_cache("order_item_type_cache", api.get_order_item_type_full)
api.reset_cache("order_note_cache", api.get_order_note_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("order_item_cache", api.get_order_item_full)
        api.reset_cache("order_cache", api.get_order_full)
        api.reset_cache("item_cache", api.get_item_full)
        api.reset_cache("order_item_type_cache", api.get_order_item_type_full)
        api.reset_cache("order_note_cache", api.get_order_note_full)
    st.success("✅ Data refreshed!")


def create_order_item_from_form(form_data: dict) -> Optional[dict]:
    """Create a new order item"""
    try:
        result = api.table_add_order_item(
            OrderID=int(form_data["OrderID"]),
            ItemID=int(form_data["ItemID"]),
            NumberOfUnits=str(form_data["NumberOfUnits"]),
            ItemCode=form_data.get("ItemCode"),
            OrderItemTypeID=form_data.get("OrderItemTypeID"),
            Unit=form_data.get("Unit"),
            UnitPrice=form_data.get("UnitPrice"),
            Received=bool(form_data.get("Received", False)),
            OrderNote=form_data.get("OrderNote"),
            OrderComments=form_data.get("OrderComments"),
            Leftover=form_data.get("Leftover"),
            ToOrder=form_data.get("ToOrder"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating order item: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_order_item(order_item_id: int, updates: dict) -> bool:
    """Update an order item"""
    try:
        allowed_fields = {
            "OrderID",
            "ItemID",
            "ItemCode",
            "OrderItemTypeID",
            "Unit",
            "UnitPrice",
            "NumberOfUnits",
            "Received",
            "OrderNote",
            "OrderComments",
            "Leftover",
            "ToOrder",
        }

        result = api.generic_update(
            model_class=ORI,
            id_column="OrderItemID",
            id_value=order_item_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated OrderItem {order_item_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating order item {order_item_id}: {e}")
        logger.error(f"Update failed for OrderItem {order_item_id}: {e}")
        return False


def delete_order_item(order_item_id: int) -> bool:
    """Delete an order item"""
    try:
        return api._delete(ORI, "OrderItemID", order_item_id)
    except Exception as e:
        st.error(f"❌ Error deleting order item {order_item_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📦 Order Items Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Order Item", expanded=st.session_state.show_add_form):
    st.write("### Create New Order Item")

    # Prepare lookup dictionaries
    orders_dict = {
        row["OrderID"]: f"Order #{row['OrderID']} - {row.get('OrderNumber', 'N/A')}"
        for _, row in api.order_cache.iterrows()
    }
    items_dict = api.item_cache.set_index("ItemID")["Item"].to_dict()
    order_item_types_dict = api.order_item_type_cache.set_index("OrderItemTypeID")[
        "OrderItemType"
    ].to_dict()
    order_notes_dict = api.order_note_cache.set_index("OrderNoteID")[
        "OrderNote"
    ].to_dict()

    with st.form("add_order_item_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_order_id = st.selectbox(
                "Order *",
                options=list(orders_dict.keys()),
                format_func=lambda x: orders_dict[x],
                key="form_order_id",
            )
            form_item_id = st.selectbox(
                "Item *",
                options=list(items_dict.keys()),
                format_func=lambda x: items_dict[x],
                key="form_item_id",
            )
            form_item_code = st.text_input("Item Code", key="form_item_code")
            form_order_item_type_id = st.selectbox(
                "Order Item Type",
                options=[None] + list(order_item_types_dict.keys()),
                format_func=lambda x: "None" if x is None else order_item_types_dict[x],
                key="form_order_item_type_id",
            )

        with col2:
            form_unit = st.text_input("Unit", key="form_unit")
            form_unit_price = st.number_input(
                "Unit Price", min_value=0.0, step=0.01, key="form_unit_price"
            )
            form_number_of_units = st.text_input(
                "Number of Units *", key="form_number_of_units"
            )
            form_received = st.checkbox("Received", key="form_received")

        with col3:
            form_order_note = st.selectbox(
                "Order Note",
                options=[None] + list(order_notes_dict.keys()),
                format_func=lambda x: "None" if x is None else order_notes_dict[x],
                key="form_order_note",
            )
            form_leftover = st.text_input("Leftover", key="form_leftover")
            form_to_order = st.text_input("To Order", key="form_to_order")

        form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Order Item", type="primary", use_container_width=True
        )

        if submitted:
            if not form_number_of_units:
                st.error("❌ Number of units is required!")
            else:
                form_data = {
                    "OrderID": form_order_id,
                    "ItemID": form_item_id,
                    "NumberOfUnits": form_number_of_units,
                    "ItemCode": form_item_code or None,
                    "OrderItemTypeID": form_order_item_type_id,
                    "Unit": form_unit or None,
                    "UnitPrice": form_unit_price if form_unit_price > 0 else None,
                    "Received": form_received,
                    "OrderNote": form_order_note,
                    "OrderComments": form_comments or None,
                    "Leftover": form_leftover or None,
                    "ToOrder": form_to_order or None,
                }

                result = create_order_item_from_form(form_data)
                if result:
                    st.success(f"✅ Order Item created! (ID: {result['OrderItemID']})")
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    order_filter = st.multiselect(
        "Filter by Order",
        options=api.order_cache["OrderID"].unique().tolist(),
        key="order_filter",
    )

with filter_col2:
    item_filter = st.multiselect(
        "Filter by Item",
        options=api.item_cache["Item"].unique().tolist(),
        key="item_filter",
    )

with filter_col3:
    received_filter = st.selectbox(
        "Received Status",
        options=["All", "Received Only", "Not Received"],
        key="received_filter",
    )

with filter_col4:
    order_item_type_filter = st.multiselect(
        "Filter by Type",
        options=api.order_item_type_cache["OrderItemType"].unique().tolist(),
        key="order_item_type_filter",
    )

# Apply filters
filtered_df = api.order_item_cache.copy()

# Order filter
if order_filter:
    filtered_df = filtered_df[filtered_df["OrderID"].isin(order_filter)]

# Item filter
if item_filter:
    item_ids = api.item_cache[api.item_cache["Item"].isin(item_filter)][
        "ItemID"
    ].tolist()
    filtered_df = filtered_df[filtered_df["ItemID"].isin(item_ids)]

# Received filter
if received_filter == "Received Only":
    filtered_df = filtered_df[filtered_df["Received"] == True]
elif received_filter == "Not Received":
    filtered_df = filtered_df[filtered_df["Received"] == False]

# Order item type filter
if order_item_type_filter:
    type_ids = api.order_item_type_cache[
        api.order_item_type_cache["OrderItemType"].isin(order_item_type_filter)
    ]["OrderItemTypeID"].tolist()
    filtered_df = filtered_df[filtered_df["OrderItemTypeID"].isin(type_ids)]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Order Items ({len(filtered_df)} records)")

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
            file_name=f"order_items_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "OrderItemID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "OrderID": st.column_config.NumberColumn("Order ID", width="small"),
    "ItemID": st.column_config.NumberColumn("Item ID", width="small"),
    "ItemCode": st.column_config.TextColumn("Item Code", width="small"),
    "OrderItemTypeID": st.column_config.NumberColumn("Type ID", width="small"),
    "Unit": st.column_config.TextColumn("Unit", width="small"),
    "UnitPrice": st.column_config.NumberColumn(
        "Unit Price", format="$%.2f", width="small"
    ),
    "NumberOfUnits": st.column_config.TextColumn("# Units", width="small"),
    "Received": st.column_config.CheckboxColumn("Received", width="small"),
    "OrderNote": st.column_config.NumberColumn("Note ID", width="small"),
    "OrderComments": st.column_config.TextColumn("Comments", width="large"),
    "Leftover": st.column_config.TextColumn("Leftover", width="small"),
    "ToOrder": st.column_config.TextColumn("To Order", width="small"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="order_items_editor",
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
                    order_item_id = edited_df.loc[idx, "OrderItemID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "OrderItemID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_order_item(order_item_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} order items")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} order items")

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
        st.write("**Mark as Received**")
        received_ids = st.text_input(
            "Order Item IDs (comma-separated)",
            key="bulk_received_ids",
            placeholder="1,2,3",
        )
        if st.button("Mark Received", key="bulk_received_btn"):
            if received_ids:
                ids = [int(x.strip()) for x in received_ids.split(",")]
                success = sum([update_order_item(id, {"Received": True}) for id in ids])
                st.success(f"✅ Marked {success}/{len(ids)} items as received")
                refresh_cache()
                st.rerun()

    with bulk_col2:
        st.write("**Delete Order Items**")
        st.warning("⚠️ Permanent action!")
        delete_ids = st.text_input(
            "Order Item IDs (comma-separated)",
            key="bulk_delete_ids",
            placeholder="1,2,3",
        )
        confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
        if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
            if delete_ids:
                ids = [int(x.strip()) for x in delete_ids.split(",")]
                success = sum([delete_order_item(id) for id in ids])
                st.success(f"✅ Deleted {success}/{len(ids)} order items")
                refresh_cache()
                st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total order items: {len(api.order_item_cache)}"
)
