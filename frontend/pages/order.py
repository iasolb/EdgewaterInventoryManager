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
from models import Order as ORD
from payloads import OrderPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Orders Administration",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("order_cache", api.get_order_full)
api.reset_cache("supplier_cache", api.get_supplier_full)
api.reset_cache("shipper_cache", api.get_shipper_full)
api.reset_cache("broker_cache", api.get_broker_full)
api.reset_cache("growing_season_cache", api.get_growing_season_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("order_cache", api.get_order_full)
        api.reset_cache("supplier_cache", api.get_supplier_full)
        api.reset_cache("shipper_cache", api.get_shipper_full)
        api.reset_cache("broker_cache", api.get_broker_full)
        api.reset_cache("growing_season_cache", api.get_growing_season_full)
    st.success("✅ Data refreshed!")


def create_order_from_form(form_data: dict) -> Optional[dict]:
    """Create a new order"""
    try:
        result = api.table_add_order(
            SupplierID=int(form_data["SupplierID"]),
            DateDue=form_data["DateDue"],
            GrowingSeasonID=form_data.get("GrowingSeasonID"),
            DatePlaced=form_data.get("DatePlaced"),
            DateReceived=form_data.get("DateReceived"),
            OrderNumber=form_data.get("OrderNumber"),
            ShipperID=form_data.get("ShipperID"),
            TrackingNumber=form_data.get("TrackingNumber"),
            OrderComments=form_data.get("OrderComments"),
            TotalCost=form_data.get("TotalCost"),
            GrowingSeason=form_data.get("GrowingSeason"),
            BrokerID=form_data.get("BrokerID"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating order: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_order(order_id: int, updates: dict) -> bool:
    """Update an order"""
    try:
        allowed_fields = {
            "GrowingSeasonID",
            "DatePlaced",
            "DateDue",
            "DateReceived",
            "SupplierID",
            "OrderNumber",
            "ShipperID",
            "TrackingNumber",
            "OrderComments",
            "TotalCost",
            "GrowingSeason",
            "BrokerID",
        }

        result = api.generic_update(
            model_class=ORD,
            id_column="OrderID",
            id_value=order_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Order {order_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating order {order_id}: {e}")
        logger.error(f"Update failed for Order {order_id}: {e}")
        return False


def delete_order(order_id: int) -> bool:
    """Delete an order"""
    try:
        return api._delete(ORD, "OrderID", order_id)
    except Exception as e:
        st.error(f"❌ Error deleting order {order_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📋 Orders Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW ORDER FORM ====================
with st.expander("➕ Add New Order", expanded=st.session_state.show_add_form):
    st.write("### Create New Order")

    # Prepare lookup dictionaries
    suppliers_dict = api.supplier_cache.set_index("SupplierID")["Supplier"].to_dict()
    shippers_dict = api.shipper_cache.set_index("ShipperID")["Shipper"].to_dict()
    brokers_dict = api.broker_cache.set_index("BrokerID")["Broker"].to_dict()
    seasons_dict = api.growing_season_cache.set_index("GrowingSeasonID")[
        "GrowingSeason"
    ].to_dict()

    with st.form("add_order_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_supplier_id = st.selectbox(
                "Supplier *",
                options=list(suppliers_dict.keys()),
                format_func=lambda x: suppliers_dict[x],
                key="form_supplier_id",
            )
            form_date_placed = st.date_input(
                "Date Placed", value=datetime.now(), key="form_date_placed"
            )
            form_date_due = st.date_input(
                "Date Due *", value=datetime.now(), key="form_date_due"
            )
            form_date_received = st.date_input(
                "Date Received", value=None, key="form_date_received"
            )

        with col2:
            form_season_id = st.selectbox(
                "Growing Season",
                options=[None] + list(seasons_dict.keys()),
                format_func=lambda x: "None" if x is None else seasons_dict[x],
                key="form_season_id",
            )
            form_broker_id = st.selectbox(
                "Broker",
                options=[None] + list(brokers_dict.keys()),
                format_func=lambda x: "None" if x is None else brokers_dict[x],
                key="form_broker_id",
            )
            form_shipper_id = st.selectbox(
                "Shipper",
                options=[None] + list(shippers_dict.keys()),
                format_func=lambda x: "None" if x is None else shippers_dict[x],
                key="form_shipper_id",
            )

        with col3:
            form_order_number = st.text_input("Order Number", key="form_order_number")
            form_tracking = st.text_input("Tracking Number", key="form_tracking")
            form_total_cost = st.number_input(
                "Total Cost", min_value=0.0, step=10.0, key="form_total_cost"
            )

        form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Order", type="primary", use_container_width=True
        )

        if submitted:
            form_data = {
                "SupplierID": form_supplier_id,
                "DateDue": datetime.combine(form_date_due, datetime.min.time()),
                "DatePlaced": datetime.combine(form_date_placed, datetime.min.time()),
                "DateReceived": (
                    datetime.combine(form_date_received, datetime.min.time())
                    if form_date_received
                    else None
                ),
                "GrowingSeasonID": form_season_id,
                "BrokerID": form_broker_id,
                "ShipperID": form_shipper_id,
                "OrderNumber": form_order_number or None,
                "TrackingNumber": form_tracking or None,
                "TotalCost": form_total_cost if form_total_cost > 0 else None,
                "OrderComments": form_comments or None,
            }

            result = create_order_from_form(form_data)
            if result:
                st.success(f"✅ Order created! (ID: {result['OrderID']})")
                st.session_state.show_add_form = False
                refresh_cache()
                st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    supplier_filter = st.multiselect(
        "Filter by Supplier",
        options=api.supplier_cache["Supplier"].unique().tolist(),
        key="supplier_filter",
    )

with filter_col2:
    date_filter_start = st.date_input("From Date", value=None, key="date_start")

with filter_col3:
    date_filter_end = st.date_input("To Date", value=None, key="date_end")

# Apply filters
filtered_df = api.order_cache.copy()

# Supplier filter
if supplier_filter:
    supplier_ids = api.supplier_cache[
        api.supplier_cache["Supplier"].isin(supplier_filter)
    ]["SupplierID"].tolist()
    filtered_df = filtered_df[filtered_df["SupplierID"].isin(supplier_ids)]

# Date filters
if date_filter_start:
    filtered_df = filtered_df[
        filtered_df["DatePlaced"] >= pd.to_datetime(date_filter_start)
    ]
if date_filter_end:
    filtered_df = filtered_df[
        filtered_df["DatePlaced"] <= pd.to_datetime(date_filter_end)
    ]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Orders ({len(filtered_df)} records)")

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
            file_name=f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "OrderID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "SupplierID": st.column_config.NumberColumn("Supplier ID", width="small"),
    "DatePlaced": st.column_config.DatetimeColumn("Date Placed", width="medium"),
    "DateDue": st.column_config.DatetimeColumn("Date Due", width="medium"),
    "DateReceived": st.column_config.DatetimeColumn("Date Received", width="medium"),
    "OrderNumber": st.column_config.TextColumn("Order #", width="small"),
    "TrackingNumber": st.column_config.TextColumn("Tracking #", width="medium"),
    "TotalCost": st.column_config.NumberColumn(
        "Total Cost", format="$%.2f", width="small"
    ),
    "OrderComments": st.column_config.TextColumn("Comments", width="large"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="orders_editor",
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
                    order_id = edited_df.loc[idx, "OrderID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "OrderID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_order(order_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} orders")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} orders")

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

    st.write("**Delete Orders**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Order IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_order(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} orders")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total orders: {len(api.order_cache)}"
)
