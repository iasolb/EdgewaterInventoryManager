"""
Order Tracking - Edgewater Inventory Management System
Manage orders with summary, detail, receiving, and calendar views
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-3-2026 - Full build with multi-view layout, receiving workflow
Optimized: st.expander replaces button+rerun, pre-indexed lookups,
           cached summary, create order form
"""

# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from rest.api import EdgewaterAPI
from models import Order, OrderItem, OrderItemDestination

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Order Tracking",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== INITIALIZE API =====
api = EdgewaterAPI()

# Hide default navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== THEME-SAFE CSS =====
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    .status-received {
        background: #e8f5e9;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-pending {
        background: #fff3e0;
        color: #e65100;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-overdue {
        background: #ffebee;
        color: #c62828;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .supplier-badge {
        background: #1565c0;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .cost-badge {
        background: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .count-badge {
        background: #FF9800;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SESSION STATE =====
if "filter_search" not in st.session_state:
    st.session_state.filter_search = ""
if "filter_suppliers" not in st.session_state:
    st.session_state.filter_suppliers = []
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "All"
if "filter_season" not in st.session_state:
    st.session_state.filter_season = "All"
if "results_limit" not in st.session_state:
    st.session_state.results_limit = 25


# ===== HELPERS =====


def refresh_data():
    """Refresh view cache and invalidate derived structures."""
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("orders")
        api.clear_lookup_caches()
        for key in ("_order_summary", "_order_items_by_id"):
            st.session_state.pop(key, None)
    st.success("Data refreshed!", icon="✅")


def format_date(date_value):
    if pd.isna(date_value):
        return "Not set"
    if isinstance(date_value, str):
        try:
            date_value = pd.to_datetime(date_value)
        except Exception:
            return date_value
    return date_value.strftime("%b %d, %Y")


def get_order_status(row):
    """Determine order status from dates."""
    if pd.notna(row.get("DateReceived")):
        return "received"
    if pd.notna(row.get("DateDue")):
        try:
            due = pd.to_datetime(row["DateDue"])
            if due < pd.Timestamp.now():
                return "overdue"
        except Exception:
            pass
    return "pending"


def format_currency(val):
    if pd.isna(val) or val is None:
        return "N/A"
    try:
        return f"${float(val):,.2f}"
    except Exception:
        return str(val)


_STATUS_HTML = {
    "received": '<span class="status-received">✅ Received</span>',
    "overdue": '<span class="status-overdue">⚠️ Overdue</span>',
    "pending": '<span class="status-pending">⏳ Pending</span>',
}

# Shared column config — built once, reused across tabs
_ITEM_COLUMN_CONFIG = {
    "OrderItemID": st.column_config.NumberColumn("ID", width="small"),
    "OrderID": st.column_config.NumberColumn("Order", width="small"),
    "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
    "Item": st.column_config.TextColumn("Item", width="medium"),
    "Variety": st.column_config.TextColumn("Variety", width="small"),
    "Color": st.column_config.TextColumn("Color", width="small"),
    "ItemCode": st.column_config.TextColumn("Code", width="small"),
    "NumberOfUnits": st.column_config.TextColumn("Qty", width="small"),
    "Unit": st.column_config.TextColumn("Unit", width="small"),
    "UnitPrice": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
    "Received": st.column_config.CheckboxColumn("Rcvd", width="small"),
    "OrderItemType": st.column_config.TextColumn("Type", width="small"),
    "OrderItemTypeID": st.column_config.TextColumn("Type", width="small"),
    "DateDue": st.column_config.DatetimeColumn(
        "Due", format="MMM DD, YYYY", width="small"
    ),
    "DateReceived": st.column_config.DatetimeColumn(
        "Received", format="MMM DD, YYYY", width="small"
    ),
    "OrderNoteDecode": st.column_config.TextColumn("Note", width="medium"),
    "OrderNote": st.column_config.TextColumn("Note", width="medium"),
    "OrderItemComments": st.column_config.TextColumn("Comments", width="medium"),
    "Leftover": st.column_config.TextColumn("Leftover", width="small"),
    "ToOrder": st.column_config.TextColumn("To Order", width="small"),
    "LocationName": st.column_config.TextColumn("Destination", width="small"),
}

# Columns to display for item tables
_ITEM_DISPLAY_COLS_DETAIL = [
    "OrderItemID",
    "Item",
    "Variety",
    "Color",
    "ItemCode",
    "NumberOfUnits",
    "Unit",
    "UnitPrice",
    "Received",
    "OrderItemTypeID",
    "OrderNote",
    "OrderItemComments",
    "Leftover",
    "ToOrder",
    "LocationName",
]

_ITEM_DISPLAY_COLS_ALL = [
    "OrderItemID",
    "OrderID",
    "Supplier",
] + _ITEM_DISPLAY_COLS_DETAIL[
    1:
]  # skip duplicate OrderItemID

# Columns that map to the OrderItem base table and can be edited inline
_EDITABLE_ORDER_ITEM_COLS = {
    "Received",
    "OrderItemComments",
    "Leftover",
    "ToOrder",
    "UnitPrice",
    "NumberOfUnits",
    "Unit",
    "ItemCode",
    "OrderNote",
    "OrderItemTypeID",
}

# Display names for item table columns
_COL_LABELS = {
    "OrderItemID": "ID",
    "Item": "Item",
    "Variety": "Variety",
    "Color": "Color",
    "ItemCode": "Code",
    "NumberOfUnits": "Qty",
    "Unit": "Unit",
    "UnitPrice": "Price",
    "Received": "Rcvd",
    "OrderItemTypeID": "Type",
    "OrderNote": "Note",
    "OrderItemType": "Type",
    "OrderNoteDecode": "Note",
    "OrderItemComments": "Comments",
    "Leftover": "Leftover",
    "ToOrder": "To Order",
    "LocationName": "Destination",
}


# ================================================================
# DATA LOADING — single read, derived structures cached in session_state
# ================================================================

_raw_cache = api.order_view_cache

if _raw_cache is None or _raw_cache.empty:
    st.markdown("# 📦 Order Tracking")
    st.info("No order data available. Check your database connection.")
    if st.button("← Back to Home"):
        st.switch_page("edgewater.py")
    st.stop()

order_df = _raw_cache


def _build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build order-level summary. Cached in session_state."""
    s = (
        df.groupby("OrderID")
        .agg(
            {
                "Supplier": "first",
                "Broker": "first",
                "Shipper": "first",
                "DatePlaced": "first",
                "DateDue": "first",
                "DateReceived": "first",
                "OrderNumber": "first",
                "TrackingNumber": "first",
                "TotalCost": "first",
                "GrowingSeason": "first",
                "OrderComments": "first",
                "OrderItemID": "count",
            }
        )
        .reset_index()
        .rename(columns={"OrderItemID": "ItemCount"})
    )
    return s.sort_values("DatePlaced", ascending=False)


def _build_order_index(df: pd.DataFrame) -> dict:
    """Pre-build {OrderID: DataFrame} for O(1) per-order lookups."""
    return {oid: group for oid, group in df.groupby("OrderID")}


if "_order_summary" not in st.session_state:
    st.session_state["_order_summary"] = _build_summary(order_df)
summary = st.session_state["_order_summary"]

if "_order_items_by_id" not in st.session_state:
    st.session_state["_order_items_by_id"] = _build_order_index(order_df)
order_items_by_id = st.session_state["_order_items_by_id"]


def get_order_items(order_id: int) -> pd.DataFrame:
    """O(1) lookup for items belonging to a specific order."""
    return order_items_by_id.get(order_id, pd.DataFrame())


# ================================================================
# FK decode maps for dropdown columns in data_editor
# These use Tier-1 cached lookups (no DB hit on rerun)
# ================================================================

_order_note_df = api.order_note_cache
_order_item_type_df = api.order_item_type_cache

# ID -> display name (for rendering)
_NOTE_ID_TO_NAME = (
    dict(zip(_order_note_df["OrderNoteID"], _order_note_df["OrderNote"]))
    if not _order_note_df.empty
    else {}
)
_OIT_ID_TO_NAME = (
    dict(
        zip(
            _order_item_type_df["OrderItemTypeID"],
            _order_item_type_df["OrderItemType"],
        )
    )
    if not _order_item_type_df.empty
    else {}
)

# Display name -> ID (for saving edits back to DB)
_NOTE_NAME_TO_ID = {v: k for k, v in _NOTE_ID_TO_NAME.items()}
_OIT_NAME_TO_ID = {v: k for k, v in _OIT_ID_TO_NAME.items()}

# Options for SelectboxColumn (display names, with empty option)
_NOTE_DISPLAY_OPTIONS = [""] + sorted(_NOTE_ID_TO_NAME.values())
_OIT_DISPLAY_OPTIONS = [""] + sorted(_OIT_ID_TO_NAME.values())

# ================================================================
# Location lookups for destination assignment (receiving workflow)
# ================================================================
_location_df = api.location_cache
_unit_df = api.unit_cache

_LOCATION_ID_TO_NAME = (
    dict(zip(_location_df["LocationID"], _location_df["Location"]))
    if not _location_df.empty
    else {}
)
_LOCATION_NAME_TO_ID = {v: k for k, v in _LOCATION_ID_TO_NAME.items()}


# Group locations by category for organized multiselect display
def _categorize_location(name: str) -> str:
    lower = name.lower().strip()
    if lower.startswith("field"):
        return "Fields"
    if any(lower.startswith(p) for p in ("greenhouse", "green house", "gh")):
        return "Greenhouses"
    return "Other"


_LOCATION_NAMES_GROUPED = []
if not _location_df.empty:
    _loc_working = _location_df.copy()
    _loc_working["_cat"] = _loc_working["Location"].apply(_categorize_location)
    for _cat in ["Greenhouses", "Fields", "Other"]:
        _cat_locs = _loc_working[_loc_working["_cat"] == _cat].sort_values("Location")
        _LOCATION_NAMES_GROUPED.extend(_cat_locs["Location"].tolist())

_UNIT_ID_TO_LABEL = (
    {
        int(r["UnitID"]): f"{r['UnitSize']} {r['UnitType']}"
        for _, r in _unit_df.iterrows()
    }
    if not _unit_df.empty
    else {}
)
_UNIT_LABEL_TO_ID = {v: k for k, v in _UNIT_ID_TO_LABEL.items()}

# Pre-load existing destinations grouped by OrderItemID
_oid_df = api.order_item_destination_cache
_DESTINATIONS_BY_ITEM = {}
if not _oid_df.empty:
    for _oi_id, _group in _oid_df.groupby("OrderItemID"):
        _DESTINATIONS_BY_ITEM[int(_oi_id)] = _group.to_dict("records")


def _display_items_dataframe(items_df: pd.DataFrame, cols: list, max_rows: int = 0):
    """Render an items dataframe with shared column config. Decodes FK IDs to names."""
    available = [c for c in cols if c in items_df.columns]
    display = items_df[available].copy()

    # Decode FK IDs to human-readable names
    if "OrderNote" in display.columns and _NOTE_ID_TO_NAME:
        display["OrderNote"] = display["OrderNote"].map(_NOTE_ID_TO_NAME).fillna("")
    if "OrderItemTypeID" in display.columns and _OIT_ID_TO_NAME:
        display["OrderItemTypeID"] = (
            display["OrderItemTypeID"].map(_OIT_ID_TO_NAME).fillna("")
        )

    if max_rows and len(display) > max_rows:
        st.dataframe(
            display.head(max_rows),
            use_container_width=True,
            hide_index=True,
            column_config=_ITEM_COLUMN_CONFIG,
        )
        st.caption(f"Showing first {max_rows} of {len(display)} items")
    else:
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config=_ITEM_COLUMN_CONFIG,
        )


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### 📦 Order Tracking")
    st.markdown("---")

    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("edgewater.py")

    st.markdown("---")

    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    search_term = st.text_input(
        "Search orders",
        value=st.session_state.filter_search,
        placeholder="Order #, supplier, item...",
        key="search_input",
    )
    if search_term != st.session_state.filter_search:
        st.session_state.filter_search = search_term
        st.rerun()

    supplier_list = sorted(summary["Supplier"].dropna().unique().tolist())
    selected_suppliers = st.multiselect(
        "Supplier",
        options=supplier_list,
        default=st.session_state.filter_suppliers,
        key="supplier_filter",
    )
    if selected_suppliers != st.session_state.filter_suppliers:
        st.session_state.filter_suppliers = selected_suppliers
        st.rerun()

    status_options = ["All", "Pending", "Received", "Overdue"]
    selected_status = st.selectbox(
        "Status",
        options=status_options,
        index=status_options.index(st.session_state.filter_status),
        key="status_filter",
    )
    if selected_status != st.session_state.filter_status:
        st.session_state.filter_status = selected_status
        st.rerun()

    seasons = ["All"] + sorted(
        summary["GrowingSeason"].dropna().unique().tolist(), reverse=True
    )
    selected_season = st.selectbox(
        "Growing Season",
        options=seasons,
        index=(
            seasons.index(st.session_state.filter_season)
            if st.session_state.filter_season in seasons
            else 0
        ),
        key="season_filter",
    )
    if selected_season != st.session_state.filter_season:
        st.session_state.filter_season = selected_season
        st.rerun()

    st.markdown("**Date Range (Placed)**")
    date_start = st.date_input("From", value=None, key="date_start")
    date_end = st.date_input("To", value=None, key="date_end")

    if st.button("Clear All Filters", use_container_width=True):
        st.session_state.filter_search = ""
        st.session_state.filter_suppliers = []
        st.session_state.filter_status = "All"
        st.session_state.filter_season = "All"
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Statistics")

    total_orders = len(summary)
    total_cost = summary["TotalCost"].sum()
    pending_count = len(summary[summary["DateReceived"].isna()])
    received_count = len(summary[summary["DateReceived"].notna()])

    st.metric("Total Orders", total_orders)
    st.metric("Total Cost", format_currency(total_cost))
    st.metric("Pending", pending_count)
    st.metric("Received", received_count)


# ===== MAIN HEADER =====
st.markdown("# 📦 Order Tracking")
st.markdown("---")

# ===== TABS =====
tab_summary, tab_timeline, tab_items, tab_receiving, tab_create = st.tabs(
    ["📋 Order Summary", "📅 Timeline", "📦 All Items", "✅ Receiving", "➕ New Order"]
)

# ===== APPLY FILTERS =====
filtered_summary = summary

if st.session_state.filter_search:
    search_lower = st.session_state.filter_search.lower()
    mask = (
        filtered_summary["Supplier"].str.lower().str.contains(search_lower, na=False)
        | filtered_summary["OrderNumber"]
        .str.lower()
        .str.contains(search_lower, na=False)
        | filtered_summary["OrderComments"]
        .str.lower()
        .str.contains(search_lower, na=False)
    )
    filtered_summary = filtered_summary[mask]

if st.session_state.filter_suppliers:
    filtered_summary = filtered_summary[
        filtered_summary["Supplier"].isin(st.session_state.filter_suppliers)
    ]

if st.session_state.filter_status == "Pending":
    filtered_summary = filtered_summary[filtered_summary["DateReceived"].isna()]
elif st.session_state.filter_status == "Received":
    filtered_summary = filtered_summary[filtered_summary["DateReceived"].notna()]
elif st.session_state.filter_status == "Overdue":
    now = pd.Timestamp.now()
    filtered_summary = filtered_summary[
        (filtered_summary["DateReceived"].isna()) & (filtered_summary["DateDue"] < now)
    ]

if st.session_state.filter_season != "All":
    filtered_summary = filtered_summary[
        filtered_summary["GrowingSeason"] == st.session_state.filter_season
    ]

if date_start:
    filtered_summary = filtered_summary[
        filtered_summary["DatePlaced"] >= pd.to_datetime(date_start)
    ]
if date_end:
    filtered_summary = filtered_summary[
        filtered_summary["DatePlaced"] <= pd.to_datetime(date_end)
    ]

filtered_order_ids = set(filtered_summary["OrderID"].tolist())


# ==================== TAB 1: ORDER SUMMARY ====================
# Uses st.expander — expanding/collapsing does NOT trigger st.rerun().
# This is the main fix for the slow card-expand experience.

with tab_summary:
    st.markdown(f"### {len(filtered_summary)} Orders")

    for idx, row in filtered_summary.head(st.session_state.results_limit).iterrows():
        status = get_order_status(row)

        supplier_name = row["Supplier"] if pd.notna(row["Supplier"]) else "Unknown"
        order_num = row["OrderNumber"] if pd.notna(row["OrderNumber"]) else "N/A"
        cost_str = format_currency(row["TotalCost"])
        item_count = int(row["ItemCount"])
        status_icon = {"received": "✅", "overdue": "⚠️", "pending": "⏳"}[status]

        expander_label = (
            f"{status_icon}  **{supplier_name}** — #{order_num} — "
            f"{format_date(row['DatePlaced'])} — {item_count} items — {cost_str}"
        )

        with st.expander(expander_label, expanded=False):
            st.markdown(_STATUS_HTML[status], unsafe_allow_html=True)

            meta1, meta2, meta3 = st.columns(3)

            with meta1:
                st.markdown("**Order Details**")
                st.markdown(f"- **Order ID:** {row['OrderID']}")
                st.markdown(f"- **Total Cost:** {cost_str}")
                st.markdown(
                    f"- **Growing Season:** {row['GrowingSeason'] if pd.notna(row['GrowingSeason']) else 'N/A'}"
                )
                if pd.notna(row.get("TrackingNumber")):
                    st.markdown(f"- **Tracking:** {row['TrackingNumber']}")

            with meta2:
                st.markdown("**Supplier & Broker**")
                st.markdown(
                    f"- **Supplier:** {row['Supplier'] if pd.notna(row['Supplier']) else 'N/A'}"
                )
                st.markdown(
                    f"- **Broker:** {row['Broker'] if pd.notna(row['Broker']) else 'N/A'}"
                )
                st.markdown(
                    f"- **Shipper:** {row['Shipper'] if pd.notna(row['Shipper']) else 'N/A'}"
                )

            with meta3:
                st.markdown("**Dates**")
                st.markdown(f"- **Placed:** {format_date(row['DatePlaced'])}")
                st.markdown(f"- **Due:** {format_date(row['DateDue'])}")
                st.markdown(f"- **Received:** {format_date(row['DateReceived'])}")

                order_id_int = int(row["OrderID"])
                if pd.notna(row["DateReceived"]):
                    # Order is marked received — allow undoing
                    if st.button(
                        "↩️ Mark Unreceived",
                        key=f"unreceive_order_{order_id_int}",
                    ):
                        try:
                            api.generic_update(
                                model_class=Order,
                                id_column="OrderID",
                                id_value=order_id_int,
                                updates={"DateReceived": None},
                                allowed_fields={"DateReceived", "OrderComments"},
                            )
                            st.success("Order marked as unreceived.")
                            refresh_data()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    # Order is pending — allow marking received
                    if st.button(
                        "✅ Mark Received",
                        key=f"receive_order_{order_id_int}",
                    ):
                        try:
                            api.generic_update(
                                model_class=Order,
                                id_column="OrderID",
                                id_value=order_id_int,
                                updates={"DateReceived": datetime.now()},
                                allowed_fields={"DateReceived", "OrderComments"},
                            )
                            st.success("Order marked as received.")
                            refresh_data()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")

            if pd.notna(row.get("OrderComments")):
                st.info(f"**Comments:** {row['OrderComments']}")

            st.markdown("#### Items in this Order")
            oi = get_order_items(row["OrderID"])
            if not oi.empty:
                available_cols = [
                    c for c in _ITEM_DISPLAY_COLS_DETAIL if c in oi.columns
                ]
                edit_df = oi[available_cols].copy()

                # Decode FK IDs to display names for the editor
                if "OrderNote" in edit_df.columns:
                    edit_df["OrderNote"] = (
                        edit_df["OrderNote"].map(_NOTE_ID_TO_NAME).fillna("")
                    )
                if "OrderItemTypeID" in edit_df.columns:
                    edit_df["OrderItemTypeID"] = (
                        edit_df["OrderItemTypeID"].map(_OIT_ID_TO_NAME).fillna("")
                    )

                # Build column config
                edit_column_config = {}
                for col in available_cols:
                    label = _COL_LABELS.get(col, col)
                    if col == "OrderItemID":
                        edit_column_config[col] = st.column_config.NumberColumn(
                            label,
                            width="small",
                            disabled=True,
                        )
                    elif col == "UnitPrice":
                        edit_column_config[col] = st.column_config.NumberColumn(
                            label,
                            format="$%.2f",
                            width="small",
                        )
                    elif col == "Received":
                        edit_column_config[col] = st.column_config.CheckboxColumn(
                            label,
                            width="small",
                        )
                    elif col == "OrderNote":
                        edit_column_config[col] = st.column_config.SelectboxColumn(
                            label,
                            options=_NOTE_DISPLAY_OPTIONS,
                            width="small",
                        )
                    elif col == "OrderItemTypeID":
                        edit_column_config[col] = st.column_config.SelectboxColumn(
                            label,
                            options=_OIT_DISPLAY_OPTIONS,
                            width="small",
                        )
                    elif col in _EDITABLE_ORDER_ITEM_COLS:
                        edit_column_config[col] = st.column_config.TextColumn(
                            label,
                            width="small",
                        )
                    else:
                        edit_column_config[col] = st.column_config.TextColumn(
                            label,
                            width="small",
                            disabled=True,
                        )

                order_id_for_key = int(row["OrderID"])
                edited = st.data_editor(
                    edit_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=edit_column_config,
                    num_rows="fixed",
                    key=f"editor_{order_id_for_key}",
                )

                # Detect changes and show save button
                has_changes = not edit_df.reset_index(drop=True).equals(
                    edited.reset_index(drop=True)
                )
                if has_changes:
                    if st.button(
                        "💾 Save Changes",
                        key=f"save_items_{order_id_for_key}",
                        type="primary",
                    ):
                        save_errors = []
                        save_count = 0
                        for idx_row in range(len(edited)):
                            orig_row = edit_df.iloc[idx_row]
                            edit_row = edited.iloc[idx_row]
                            item_id = int(orig_row["OrderItemID"])

                            updates = {}
                            for col in _EDITABLE_ORDER_ITEM_COLS:
                                if col not in edit_df.columns:
                                    continue
                                orig_val = orig_row[col]
                                new_val = edit_row[col]
                                if pd.isna(orig_val) and pd.isna(new_val):
                                    continue
                                if orig_val != new_val:
                                    # Translate display names back to FK IDs
                                    if col == "OrderNote":
                                        new_val = (
                                            _NOTE_NAME_TO_ID.get(new_val)
                                            if new_val
                                            else None
                                        )
                                    elif col == "OrderItemTypeID":
                                        new_val = (
                                            _OIT_NAME_TO_ID.get(new_val)
                                            if new_val
                                            else None
                                        )
                                    updates[col] = new_val

                            if updates:
                                try:
                                    api.generic_update(
                                        model_class=OrderItem,
                                        id_column="OrderItemID",
                                        id_value=item_id,
                                        updates=updates,
                                        allowed_fields=_EDITABLE_ORDER_ITEM_COLS,
                                    )
                                    save_count += 1
                                except Exception as e:
                                    save_errors.append(f"Item {item_id}: {e}")

                        if save_errors:
                            for err in save_errors:
                                st.error(f"❌ {err}")
                        if save_count:
                            st.success(f"✅ Updated {save_count} item(s).")
                            refresh_data()
                            st.rerun()
                else:
                    st.caption("Edit cells above, then save.")


# ==================== TAB 2: TIMELINE ====================
with tab_timeline:
    st.markdown("### 📅 Orders by Due Date")

    if filtered_summary.empty:
        st.info("No orders match current filters.")
    else:
        timeline_df = filtered_summary.copy()
        timeline_df["DueDateParsed"] = pd.to_datetime(
            timeline_df["DateDue"], errors="coerce"
        )
        timeline_df = timeline_df.dropna(subset=["DueDateParsed"])
        timeline_df = timeline_df.sort_values("DueDateParsed")

        if timeline_df.empty:
            st.info("No orders with valid due dates.")
        else:
            now = pd.Timestamp.now()
            overdue = timeline_df[
                (timeline_df["DueDateParsed"] < now)
                & (timeline_df["DateReceived"].isna())
            ]

            if not overdue.empty:
                st.markdown("#### ⚠️ Overdue")
                for _, row in overdue.iterrows():
                    days_late = (now - row["DueDateParsed"]).days
                    st.markdown(
                        f"- **{row['Supplier']}** — Order #{row['OrderNumber'] if pd.notna(row['OrderNumber']) else 'N/A'} "
                        f"— Due {format_date(row['DateDue'])} ({days_late} days late) "
                        f"— {int(row['ItemCount'])} items — {format_currency(row['TotalCost'])}"
                    )
                st.markdown("---")

            upcoming = timeline_df[
                (timeline_df["DueDateParsed"] >= now)
                | (timeline_df["DateReceived"].notna())
            ]

            if not upcoming.empty:
                upcoming = upcoming.copy()
                upcoming["Week"] = upcoming["DueDateParsed"].dt.to_period("W")

                for week in sorted(upcoming["Week"].unique()):
                    week_orders = upcoming[upcoming["Week"] == week]
                    week_start = week.start_time.strftime("%b %d")
                    week_end = week.end_time.strftime("%b %d, %Y")

                    st.markdown(f"#### Week of {week_start} - {week_end}")

                    for _, row in week_orders.iterrows():
                        s = get_order_status(row)
                        icon = "✅" if s == "received" else "⏳"
                        st.markdown(
                            f"- {icon} **{row['Supplier']}** — "
                            f"Due {format_date(row['DateDue'])} — "
                            f"{int(row['ItemCount'])} items — "
                            f"{format_currency(row['TotalCost'])}"
                        )
                    st.markdown("")


# ==================== TAB 3: ALL ITEMS ====================
with tab_items:
    st.markdown("### 📦 All Order Items (Expanded)")

    if filtered_order_ids:
        parts = [
            order_items_by_id[oid]
            for oid in filtered_order_ids
            if oid in order_items_by_id
        ]
        filtered_items = (
            pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        )
    else:
        filtered_items = pd.DataFrame()

    if filtered_items.empty:
        st.info("No items match current filters.")
    else:
        item_search = st.text_input(
            "Search items",
            placeholder="Search by item name, code, variety...",
            key="item_search",
        )

        if item_search:
            sl = item_search.lower()
            mask = (
                filtered_items["Item"].str.lower().str.contains(sl, na=False)
                | filtered_items["Variety"].str.lower().str.contains(sl, na=False)
                | filtered_items["ItemCode"].str.lower().str.contains(sl, na=False)
            )
            filtered_items = filtered_items[mask]

        st.markdown(
            f"**{len(filtered_items)} items across {filtered_items['OrderID'].nunique()} orders**"
        )

        _display_items_dataframe(filtered_items, _ITEM_DISPLAY_COLS_ALL, max_rows=200)


# ==================== TAB 4: RECEIVING ====================
with tab_receiving:
    st.markdown("### ✅ Receive Orders")
    st.markdown(
        "Check items, pick destination(s), then save. "
        "Items with **multiple destinations** will prompt you to allocate quantities."
    )

    pending_orders = filtered_summary[filtered_summary["DateReceived"].isna()]

    if pending_orders.empty:
        st.success("🎉 All orders have been received!")
    else:
        st.markdown(f"**{len(pending_orders)} orders pending**")

        # ---- Allocation workflow state ----
        # When items need qty split across multiple locations, we queue them here.
        # Each entry: {order_id, item_id, item_label, total_qty, unit, locations, unit_id}
        if "_alloc_queue" not in st.session_state:
            st.session_state._alloc_queue = []
        if "_alloc_index" not in st.session_state:
            st.session_state._alloc_index = 0

        # ---- If allocation queue is active, show allocation forms ----
        if st.session_state._alloc_queue:
            idx = st.session_state._alloc_index
            queue = st.session_state._alloc_queue

            if idx >= len(queue):
                # All allocations done — save them all
                alloc_errors = []
                alloc_count = 0
                for entry in queue:
                    for loc_name, qty in entry["allocations"].items():
                        if qty > 0:
                            loc_id = _LOCATION_NAME_TO_ID.get(loc_name)
                            if loc_id:
                                try:
                                    api.table_add_order_item_destination(
                                        OrderItemID=entry["item_id"],
                                        Count=qty,
                                        UnitID=entry["unit_id"],
                                        LocationID=loc_id,
                                    )
                                    alloc_count += 1
                                except Exception as e:
                                    alloc_errors.append(f"{entry['item_label']}: {e}")

                if alloc_errors:
                    for err in alloc_errors:
                        st.error(f"❌ {err}")
                if alloc_count:
                    st.success(f"✅ Created {alloc_count} destination assignment(s).")

                # Clear queue
                st.session_state._alloc_queue = []
                st.session_state._alloc_index = 0
                refresh_data()
                st.rerun()
            else:
                # Show allocation form for current item
                current = queue[idx]
                st.markdown("---")
                st.markdown(f"### 📦 Allocate: {current['item_label']}")
                st.markdown(
                    f"**Total qty:** {current['total_qty']} {current['unit']}  |  "
                    f"**Destinations:** {', '.join(current['locations'])}  |  "
                    f"**Item {idx + 1} of {len(queue)}**"
                )

                with st.form(f"alloc_form_{current['item_id']}"):
                    st.markdown("Enter quantity for each destination:")

                    try:
                        total_numeric = int(float(str(current["total_qty"]).split()[0]))
                    except (ValueError, IndexError):
                        total_numeric = 1

                    n_locs = len(current["locations"])
                    # Default: split evenly, remainder to first
                    base_split = total_numeric // n_locs
                    remainder = total_numeric - (base_split * n_locs)

                    alloc_cols = st.columns(n_locs)
                    for i, loc_name in enumerate(current["locations"]):
                        default_val = base_split + (1 if i < remainder else 0)
                        with alloc_cols[i]:
                            st.number_input(
                                f"📍 {loc_name}",
                                min_value=0,
                                value=default_val,
                                step=1,
                                key=f"alloc_qty_{current['item_id']}_{i}",
                            )

                    alloc_submitted = st.form_submit_button(
                        f"✅ Confirm & {'Next Item' if idx < len(queue) - 1 else 'Finish'}",
                        type="primary",
                        use_container_width=True,
                    )

                    if alloc_submitted:
                        # Collect allocations
                        allocations = {}
                        total_allocated = 0
                        for i, loc_name in enumerate(current["locations"]):
                            qty = st.session_state.get(
                                f"alloc_qty_{current['item_id']}_{i}", 0
                            )
                            allocations[loc_name] = qty
                            total_allocated += qty

                        if total_allocated == 0:
                            st.error("❌ Total allocated must be greater than 0.")
                        else:
                            current["allocations"] = allocations
                            st.session_state._alloc_index += 1
                            st.rerun()

        # ---- Normal receiving forms (no active allocation queue) ----
        else:
            for _, order_row in pending_orders.head(
                st.session_state.results_limit
            ).iterrows():
                order_id = int(order_row["OrderID"])
                supplier = (
                    order_row["Supplier"]
                    if pd.notna(order_row["Supplier"])
                    else "Unknown"
                )
                order_num = (
                    order_row["OrderNumber"]
                    if pd.notna(order_row["OrderNumber"])
                    else "N/A"
                )

                status = get_order_status(order_row)
                status_label = "⚠️ OVERDUE" if status == "overdue" else "⏳ Pending"

                items = get_order_items(order_id)
                item_count = len(items) if not items.empty else 0

                with st.expander(
                    f"{status_label} — {supplier} — Order #{order_num} "
                    f"— {item_count} items "
                    f"— Due {format_date(order_row['DateDue'])}",
                    expanded=False,
                ):
                    with st.form(f"recv_form_{order_id}"):
                        # ---- Order-level ----
                        recv_col1, recv_col2 = st.columns([1, 3])

                        with recv_col1:
                            receive_all = st.checkbox(
                                "Receive entire order",
                                value=False,
                                key=f"recv_all_{order_id}",
                            )

                        with recv_col2:
                            order_comment = st.text_input(
                                "Receiving notes",
                                key=f"recv_comment_{order_id}",
                                placeholder="e.g., 2 flats damaged",
                            )

                        # ---- Item-level ----
                        if not items.empty:
                            # Quick summary of what's in this order
                            unit_summary = (
                                items.groupby("Unit")["NumberOfUnits"].count().to_dict()
                            )
                            summary_parts = [
                                f"{count} {utype}"
                                for utype, count in unit_summary.items()
                                if pd.notna(utype)
                            ]
                            if summary_parts:
                                st.caption(
                                    f"📋 {len(items)} items: "
                                    + ", ".join(summary_parts)
                                )

                        st.markdown("**Items:**")

                        item_db_states = {}

                        if not items.empty:
                            for item_idx, item_row in items.iterrows():
                                item_id = int(item_row["OrderItemID"])
                                item_name = (
                                    item_row["Item"]
                                    if pd.notna(item_row.get("Item"))
                                    else "Unknown"
                                )
                                variety = (
                                    f" - {item_row['Variety']}"
                                    if pd.notna(item_row.get("Variety"))
                                    else ""
                                )
                                qty = item_row.get("NumberOfUnits", "?")
                                unit = item_row.get("Unit", "")
                                db_received = bool(item_row.get("Received", False))
                                item_db_states[item_id] = {
                                    "received": db_received,
                                    "comments": item_row.get("OrderItemComments", ""),
                                    "qty": str(qty),
                                    "unit": str(unit),
                                    "label": f"{item_name}{variety}",
                                }

                                # Existing destinations for display
                                existing_dests = _DESTINATIONS_BY_ITEM.get(item_id, [])
                                existing_loc_names = [
                                    _LOCATION_ID_TO_NAME.get(d["LocationID"], "?")
                                    for d in existing_dests
                                ]

                                i_col1, i_col2, i_col3 = st.columns([2, 1, 2])

                                with i_col1:
                                    st.checkbox(
                                        f"**{item_name}{variety}** — " f"{qty} {unit}",
                                        value=db_received,
                                        key=f"recv_chk_{order_id}_{item_id}",
                                    )

                                with i_col2:
                                    st.text_input(
                                        "Condition",
                                        key=f"recv_note_{order_id}_{item_id}",
                                        placeholder="Good / Damaged",
                                        label_visibility="collapsed",
                                    )

                                with i_col3:
                                    st.multiselect(
                                        "Destinations",
                                        options=_LOCATION_NAMES_GROUPED,
                                        default=existing_loc_names,
                                        key=f"recv_dest_{order_id}_{item_id}",
                                        label_visibility="collapsed",
                                        placeholder="📍 Select destination(s)",
                                    )

                        # ---- Submit ----
                        submitted = st.form_submit_button(
                            "💾 Save Changes",
                            type="primary",
                            use_container_width=True,
                        )

                        if submitted:
                            save_errors = []
                            save_count = 0
                            alloc_needed = []

                            for item_id, db_state in item_db_states.items():
                                db_received = db_state["received"]

                                # Read form widget values
                                chk_key = f"recv_chk_{order_id}_{item_id}"
                                new_received = st.session_state.get(
                                    chk_key, db_received
                                )
                                if receive_all:
                                    new_received = True

                                note_key = f"recv_note_{order_id}_{item_id}"
                                condition_note = st.session_state.get(note_key, "")

                                updates = {}

                                if new_received != db_received:
                                    updates["Received"] = new_received

                                if condition_note:
                                    existing = db_state["comments"]
                                    if pd.isna(existing):
                                        existing = ""
                                    timestamp = datetime.now().strftime("%m/%d/%y")
                                    updates["OrderComments"] = (
                                        f"{existing}\n[{timestamp}] "
                                        f"{condition_note}"
                                    ).strip()

                                if updates:
                                    try:
                                        api.generic_update(
                                            model_class=OrderItem,
                                            id_column="OrderItemID",
                                            id_value=item_id,
                                            updates=updates,
                                            allowed_fields={
                                                "Received",
                                                "OrderComments",
                                                "Leftover",
                                            },
                                        )
                                        save_count += 1
                                    except Exception as e:
                                        save_errors.append(f"Item {item_id}: {e}")

                                # Process destinations
                                dest_key = f"recv_dest_{order_id}_{item_id}"
                                selected_locs = st.session_state.get(dest_key, [])

                                # Find which are NEW (not already in DB)
                                existing_dests = _DESTINATIONS_BY_ITEM.get(item_id, [])
                                existing_loc_ids = {
                                    d["LocationID"] for d in existing_dests
                                }
                                new_locs = [
                                    loc
                                    for loc in selected_locs
                                    if _LOCATION_NAME_TO_ID.get(loc)
                                    not in existing_loc_ids
                                ]

                                if len(new_locs) == 0:
                                    pass  # No new destinations
                                elif len(new_locs) == 1:
                                    # Single new destination — assign
                                    # full qty directly
                                    loc_id = _LOCATION_NAME_TO_ID.get(new_locs[0])
                                    if loc_id:
                                        try:
                                            qty_val = int(
                                                float(str(db_state["qty"]).split()[0])
                                            )
                                        except (ValueError, IndexError):
                                            qty_val = 1

                                        # Get a UnitID from existing
                                        # destinations or first available
                                        unit_id = None
                                        if existing_dests:
                                            unit_id = existing_dests[0].get("UnitID")
                                        if not unit_id and _UNIT_ID_TO_LABEL:
                                            unit_id = list(_UNIT_ID_TO_LABEL.keys())[0]

                                        try:
                                            api.table_add_order_item_destination(
                                                OrderItemID=item_id,
                                                Count=max(qty_val, 1),
                                                UnitID=unit_id or 1,
                                                LocationID=loc_id,
                                            )
                                            save_count += 1
                                        except Exception as e:
                                            save_errors.append(
                                                f"Dest {new_locs[0]}: {e}"
                                            )
                                else:
                                    # Multiple new destinations — queue
                                    # for allocation
                                    unit_id = None
                                    if existing_dests:
                                        unit_id = existing_dests[0].get("UnitID")
                                    if not unit_id and _UNIT_ID_TO_LABEL:
                                        unit_id = list(_UNIT_ID_TO_LABEL.keys())[0]

                                    alloc_needed.append(
                                        {
                                            "order_id": order_id,
                                            "item_id": item_id,
                                            "item_label": db_state["label"],
                                            "total_qty": db_state["qty"],
                                            "unit": db_state["unit"],
                                            "locations": new_locs,
                                            "unit_id": unit_id or 1,
                                            "allocations": {},
                                        }
                                    )

                            # Process order-level changes
                            order_updates = {}

                            if order_comment:
                                existing_order_comments = (
                                    order_row["OrderComments"]
                                    if pd.notna(order_row.get("OrderComments"))
                                    else ""
                                )
                                timestamp = datetime.now().strftime("%m/%d/%y")
                                order_updates["OrderComments"] = (
                                    f"{existing_order_comments}\n"
                                    f"[{timestamp}] {order_comment}"
                                ).strip()

                            if receive_all:
                                order_updates["DateReceived"] = datetime.now()

                            if order_updates:
                                try:
                                    api.generic_update(
                                        model_class=Order,
                                        id_column="OrderID",
                                        id_value=order_id,
                                        updates=order_updates,
                                        allowed_fields={
                                            "OrderComments",
                                            "DateReceived",
                                        },
                                    )
                                    save_count += 1
                                except Exception as e:
                                    save_errors.append(f"Order: {e}")

                            if save_errors:
                                for err in save_errors:
                                    st.error(f"❌ {err}")
                            if save_count:
                                st.success(f"✅ Saved {save_count} change(s).")

                            # If allocations needed, queue them up
                            if alloc_needed:
                                st.session_state._alloc_queue = alloc_needed
                                st.session_state._alloc_index = 0
                                st.info(
                                    f"📦 {len(alloc_needed)} item(s) need "
                                    f"quantity allocation across locations. "
                                    f"Redirecting..."
                                )
                                st.rerun()
                            elif save_count and not save_errors:
                                refresh_data()
                                st.rerun()
                            elif not save_errors:
                                st.info("No changes to save.")


# ==================== TAB 5: CREATE ORDER ====================
with tab_create:
    st.markdown("### ➕ Create New Order")

    # Lookup data for dropdowns (Tier-1 cached, no DB hit on rerun)
    supplier_df = api.supplier_cache
    broker_df = api.broker_cache
    shipper_df = api.shipper_cache
    season_df = api.growing_season_cache
    item_df = api.item_cache
    order_item_type_df = api.order_item_type_cache
    order_note_df = api.order_note_cache

    # Build display maps: "Name" -> ID
    supplier_map = (
        dict(zip(supplier_df["Supplier"], supplier_df["SupplierID"]))
        if not supplier_df.empty
        else {}
    )
    broker_map = (
        dict(zip(broker_df["Broker"], broker_df["BrokerID"]))
        if not broker_df.empty
        else {}
    )
    shipper_map = (
        dict(zip(shipper_df["Shipper"], shipper_df["ShipperID"]))
        if not shipper_df.empty
        else {}
    )
    season_map = (
        dict(zip(season_df["GrowingSeason"], season_df["GrowingSeasonID"]))
        if not season_df.empty
        else {}
    )

    item_map = {}
    if not item_df.empty:
        for _, r in item_df.iterrows():
            name = r.get("Item")
            if pd.isna(name) or not name:
                continue
            label = str(name)
            if pd.notna(r.get("Variety")) and r["Variety"]:
                label += f" - {r['Variety']}"
            if pd.notna(r.get("Color")) and r["Color"]:
                label += f" ({r['Color']})"
            item_map[label] = r["ItemID"]

    oit_map = (
        dict(
            zip(
                order_item_type_df["OrderItemType"],
                order_item_type_df["OrderItemTypeID"],
            )
        )
        if not order_item_type_df.empty
        else {}
    )
    note_map = (
        dict(zip(order_note_df["OrderNote"], order_note_df["OrderNoteID"]))
        if not order_note_df.empty
        else {}
    )

    # ---- Line items (outside form — needs dynamic add/remove buttons) ----
    # This section is purely session_state; nothing hits the DB until final submit.

    st.markdown("#### 1. Build Item List")
    st.caption(
        "Add items below. Nothing is saved until you submit the full order at the bottom."
    )

    if "new_order_line_items" not in st.session_state:
        st.session_state.new_order_line_items = []

    li_col1, li_col2, li_col3, li_col4 = st.columns([3, 1, 1, 1])

    with li_col1:
        li_item = st.selectbox(
            "Item",
            options=[""] + sorted(item_map.keys()),
            key="li_item_select",
        )
    with li_col2:
        li_qty = st.text_input("Qty", key="li_qty", placeholder="e.g., 10")
    with li_col3:
        li_unit = st.text_input("Unit", key="li_unit", placeholder="e.g., Flat")
    with li_col4:
        li_price = st.number_input(
            "Unit Price",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="li_price",
        )

    li_extra1, li_extra2, li_extra3 = st.columns(3)
    with li_extra1:
        li_code = st.text_input("Item Code", key="li_code", placeholder="Supplier code")
    with li_extra2:
        li_type = st.selectbox(
            "Item Type",
            options=["None"] + list(oit_map.keys()),
            key="li_type_select",
        )
    with li_extra3:
        li_note = st.selectbox(
            "Order Note",
            options=["None"] + list(note_map.keys()),
            key="li_note_select",
        )

    if st.button("➕ Add Item to List", key="add_line_item"):
        if li_item and li_qty:
            st.session_state.new_order_line_items.append(
                {
                    "item_label": li_item,
                    "ItemID": item_map[li_item],
                    "NumberOfUnits": li_qty,
                    "Unit": li_unit or None,
                    "UnitPrice": li_price if li_price > 0 else None,
                    "ItemCode": li_code or None,
                    "OrderItemTypeID": (
                        oit_map.get(li_type) if li_type != "None" else None
                    ),
                    "OrderNote": (note_map.get(li_note) if li_note != "None" else None),
                }
            )
            st.rerun()
        else:
            st.warning("Please select an item and enter a quantity.")

    # Show pending line items
    if st.session_state.new_order_line_items:
        st.markdown(f"**{len(st.session_state.new_order_line_items)} item(s) staged:**")
        for i, li in enumerate(st.session_state.new_order_line_items):
            li_display, li_remove = st.columns([5, 1])
            with li_display:
                price_str = f" @ ${li['UnitPrice']:.2f}" if li.get("UnitPrice") else ""
                st.markdown(
                    f"{i + 1}. **{li['item_label']}** — "
                    f"{li['NumberOfUnits']} {li.get('Unit') or ''}{price_str}"
                )
            with li_remove:
                if st.button("🗑️", key=f"remove_li_{i}"):
                    st.session_state.new_order_line_items.pop(i)
                    st.rerun()
    else:
        st.info("No items added yet. You can also add items after creating the order.")

    st.markdown("---")

    # ---- Order header + submit (inside st.form — no reruns on input) ----
    # All fields here are batched: typing, selecting, etc. won't cause a
    # page rerun. Only clicking "Create Order" submits everything.

    st.markdown("#### 2. Order Details & Submit")

    with st.form("create_order_form", clear_on_submit=True):
        oc1, oc2 = st.columns(2)

        with oc1:
            new_supplier = st.selectbox(
                "Supplier *",
                options=[""] + list(supplier_map.keys()),
                key="form_supplier",
            )
            new_broker = st.selectbox(
                "Broker",
                options=["None"] + list(broker_map.keys()),
                key="form_broker",
            )
            new_shipper = st.selectbox(
                "Shipper",
                options=["None"] + list(shipper_map.keys()),
                key="form_shipper",
            )
            new_season = st.selectbox(
                "Growing Season",
                options=["None"] + list(season_map.keys()),
                key="form_season",
            )

        with oc2:
            new_date_placed = st.date_input(
                "Date Placed",
                value=datetime.now().date(),
                key="form_date_placed",
            )
            new_date_due = st.date_input(
                "Date Due *",
                value=None,
                key="form_date_due",
            )
            new_order_number = st.text_input(
                "Order Number",
                key="form_order_number",
                placeholder="e.g., PO-2026-001",
            )
            new_tracking = st.text_input(
                "Tracking Number",
                key="form_tracking",
            )

        new_total_cost = st.number_input(
            "Total Cost",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="form_total_cost",
        )
        new_order_comments = st.text_area(
            "Order Comments",
            key="form_comments",
            placeholder="Any notes about this order...",
        )

        # Show summary of what will be created
        n_items = len(st.session_state.new_order_line_items)
        if n_items:
            st.caption(f"This will create 1 order + {n_items} item(s) staged above.")
        else:
            st.caption(
                "This will create an order with no items (you can add them later)."
            )

        submitted = st.form_submit_button(
            "✅ Create Order",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            errors = []
            if not new_supplier:
                errors.append("Supplier is required.")
            if not new_date_due:
                errors.append("Date Due is required.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                try:
                    order_result = api.table_add_order(
                        SupplierID=supplier_map[new_supplier],
                        DateDue=datetime.combine(new_date_due, datetime.min.time()),
                        DatePlaced=datetime.combine(
                            new_date_placed, datetime.min.time()
                        ),
                        OrderNumber=new_order_number or None,
                        BrokerID=(
                            broker_map.get(new_broker) if new_broker != "None" else None
                        ),
                        ShipperID=(
                            shipper_map.get(new_shipper)
                            if new_shipper != "None"
                            else None
                        ),
                        GrowingSeasonID=(
                            season_map.get(new_season) if new_season != "None" else None
                        ),
                        GrowingSeason=(new_season if new_season != "None" else None),
                        TrackingNumber=new_tracking or None,
                        TotalCost=(new_total_cost if new_total_cost > 0 else None),
                        OrderComments=new_order_comments or None,
                    )

                    new_order_id = order_result["OrderID"]

                    items_added = 0
                    for li in st.session_state.new_order_line_items:
                        api.table_add_order_item(
                            OrderID=new_order_id,
                            ItemID=li["ItemID"],
                            NumberOfUnits=li["NumberOfUnits"],
                            Unit=li.get("Unit"),
                            UnitPrice=li.get("UnitPrice"),
                            ItemCode=li.get("ItemCode"),
                            OrderItemTypeID=li.get("OrderItemTypeID"),
                            OrderNote=li.get("OrderNote"),
                        )
                        items_added += 1

                    st.session_state.new_order_line_items = []

                    st.success(
                        f"✅ Order #{new_order_id} created"
                        + (f" with {items_added} items!" if items_added else "!")
                    )

                    refresh_data()
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error creating order: {e}")


# ===== FOOTER =====
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"{len(filtered_summary)} orders | {len(order_df)} total items"
    )

with col2:
    st.caption("Edgewater Farm Inventory System")
