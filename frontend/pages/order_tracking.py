"""
Order Tracking - Edgewater Inventory Management System
Manage orders with summary, detail, receiving, and calendar views
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-3-2026 - Full build with multi-view layout, receiving workflow
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
from models import Order, OrderItem

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
if "expanded_order" not in st.session_state:
    st.session_state.expanded_order = None
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

# ===== CACHE DATA =====
# Lookup tables auto-cached via @st.cache_data
# View data loaded lazily into session_state


def refresh_data():
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("orders")
        api.clear_lookup_caches()
    st.success("✅ Data refreshed!", icon="✅")


def format_date(date_value):
    if pd.isna(date_value):
        return "Not set"
    if isinstance(date_value, str):
        try:
            date_value = pd.to_datetime(date_value)
        except:
            return date_value
    return date_value.strftime("%b %d, %Y")


def get_order_status(row):
    """Determine order status from dates"""
    if pd.notna(row.get("DateReceived")):
        return "received"
    if pd.notna(row.get("DateDue")):
        try:
            due = pd.to_datetime(row["DateDue"])
            if due < pd.Timestamp.now():
                return "overdue"
        except:
            pass
    return "pending"


def format_currency(val):
    if pd.isna(val) or val is None:
        return "N/A"
    try:
        return f"${float(val):,.2f}"
    except:
        return str(val)


# ===== BUILD SUMMARY DATA =====
order_df = (
    api.order_view_cache.copy() if api.order_view_cache is not None else pd.DataFrame()
)

if order_df.empty:
    st.markdown("# 📦 Order Tracking")
    st.info("No order data available. Check your database connection.")
    if st.button("← Back to Home"):
        st.switch_page("edgewater.py")
    st.stop()

# Build order-level summary
summary = (
    order_df.groupby("OrderID")
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
summary = summary.sort_values("DatePlaced", ascending=False)


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

    # Search
    search_term = st.text_input(
        "Search orders",
        value=st.session_state.filter_search,
        placeholder="Order #, supplier, item...",
        key="search_input",
    )
    if search_term != st.session_state.filter_search:
        st.session_state.filter_search = search_term
        st.rerun()

    # Supplier filter
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

    # Status filter
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

    # Season filter
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

    # Date range
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

# ===== MAIN TABS =====
tab_summary, tab_timeline, tab_items, tab_receiving = st.tabs(
    ["📋 Order Summary", "📅 Timeline", "📦 All Items", "✅ Receiving"]
)

# ===== APPLY FILTERS TO SUMMARY =====
filtered_summary = summary.copy()

# Search
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

# Supplier
if st.session_state.filter_suppliers:
    filtered_summary = filtered_summary[
        filtered_summary["Supplier"].isin(st.session_state.filter_suppliers)
    ]

# Status
if st.session_state.filter_status == "Pending":
    filtered_summary = filtered_summary[filtered_summary["DateReceived"].isna()]
elif st.session_state.filter_status == "Received":
    filtered_summary = filtered_summary[filtered_summary["DateReceived"].notna()]
elif st.session_state.filter_status == "Overdue":
    now = pd.Timestamp.now()
    filtered_summary = filtered_summary[
        (filtered_summary["DateReceived"].isna()) & (filtered_summary["DateDue"] < now)
    ]

# Season
if st.session_state.filter_season != "All":
    filtered_summary = filtered_summary[
        filtered_summary["GrowingSeason"] == st.session_state.filter_season
    ]

# Date range
if date_start:
    filtered_summary = filtered_summary[
        filtered_summary["DatePlaced"] >= pd.to_datetime(date_start)
    ]
if date_end:
    filtered_summary = filtered_summary[
        filtered_summary["DatePlaced"] <= pd.to_datetime(date_end)
    ]

filtered_order_ids = filtered_summary["OrderID"].tolist()

# ==================== TAB 1: ORDER SUMMARY ====================
with tab_summary:
    st.markdown(f"### {len(filtered_summary)} Orders")

    for idx, row in filtered_summary.head(st.session_state.results_limit).iterrows():
        status = get_order_status(row)
        is_expanded = st.session_state.expanded_order == row["OrderID"]

        with st.container():
            # Order header row
            h1, h2, h3, h4, h5 = st.columns([2, 2, 1, 1, 1])

            with h1:
                supplier_name = (
                    row["Supplier"] if pd.notna(row["Supplier"]) else "Unknown"
                )
                order_num = row["OrderNumber"] if pd.notna(row["OrderNumber"]) else ""
                st.markdown(f"**{supplier_name}**")
                if order_num:
                    st.caption(f"Order #{order_num}")

            with h2:
                st.markdown(f"**Placed:** {format_date(row['DatePlaced'])}")
                st.markdown(f"**Due:** {format_date(row['DateDue'])}")

            with h3:
                st.markdown(
                    f'<div class="count-badge">{int(row["ItemCount"])} items</div>',
                    unsafe_allow_html=True,
                )

            with h4:
                if status == "received":
                    st.markdown(
                        '<div class="status-received">✅ Received</div>',
                        unsafe_allow_html=True,
                    )
                elif status == "overdue":
                    st.markdown(
                        '<div class="status-overdue">⚠️ Overdue</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="status-pending">⏳ Pending</div>',
                        unsafe_allow_html=True,
                    )

            with h5:
                if st.button(
                    "👁️" if not is_expanded else "➖",
                    key=f"expand_order_{row['OrderID']}",
                ):
                    if is_expanded:
                        st.session_state.expanded_order = None
                    else:
                        st.session_state.expanded_order = row["OrderID"]
                    st.rerun()

            # Expanded order details
            if is_expanded:
                st.markdown("---")

                # Order metadata
                meta1, meta2, meta3 = st.columns(3)

                with meta1:
                    st.markdown("**Order Details**")
                    st.markdown(f"- **Order ID:** {row['OrderID']}")
                    st.markdown(
                        f"- **Total Cost:** {format_currency(row['TotalCost'])}"
                    )
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

                if pd.notna(row.get("OrderComments")):
                    st.info(f"**Comments:** {row['OrderComments']}")

                # Order items for this order
                st.markdown("#### Items in this Order")
                order_items = order_df[order_df["OrderID"] == row["OrderID"]].copy()

                if not order_items.empty:
                    items_display = order_items[
                        [
                            c
                            for c in [
                                "OrderItemID",
                                "Item",
                                "Variety",
                                "Color",
                                "ItemCode",
                                "NumberOfUnits",
                                "Unit",
                                "UnitPrice",
                                "Received",
                                "OrderItemType",
                                "OrderNoteDecode",
                                "OrderItemComments",
                                "Leftover",
                                "ToOrder",
                                "LocationName",
                            ]
                            if c in order_items.columns
                        ]
                    ].copy()

                    column_config = {
                        "OrderItemID": st.column_config.NumberColumn(
                            "ID", width="small"
                        ),
                        "Item": st.column_config.TextColumn("Item", width="medium"),
                        "Variety": st.column_config.TextColumn(
                            "Variety", width="small"
                        ),
                        "Color": st.column_config.TextColumn("Color", width="small"),
                        "ItemCode": st.column_config.TextColumn("Code", width="small"),
                        "NumberOfUnits": st.column_config.TextColumn(
                            "Qty", width="small"
                        ),
                        "Unit": st.column_config.TextColumn("Unit", width="small"),
                        "UnitPrice": st.column_config.NumberColumn(
                            "Price", format="$%.2f", width="small"
                        ),
                        "Received": st.column_config.CheckboxColumn(
                            "Rcvd", width="small"
                        ),
                        "OrderItemType": st.column_config.TextColumn(
                            "Type", width="small"
                        ),
                        "OrderNoteDecode": st.column_config.TextColumn(
                            "Note", width="medium"
                        ),
                        "OrderItemComments": st.column_config.TextColumn(
                            "Comments", width="medium"
                        ),
                        "Leftover": st.column_config.TextColumn(
                            "Leftover", width="small"
                        ),
                        "ToOrder": st.column_config.TextColumn(
                            "To Order", width="small"
                        ),
                        "LocationName": st.column_config.TextColumn(
                            "Destination", width="small"
                        ),
                    }

                    st.dataframe(
                        items_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config=column_config,
                    )

            st.markdown("---")


# ==================== TAB 2: TIMELINE ====================
with tab_timeline:
    st.markdown("### 📅 Orders by Due Date")

    timeline_df = filtered_summary.copy()

    if timeline_df.empty:
        st.info("No orders match current filters.")
    else:
        # Group by due date week
        timeline_df["DueDateParsed"] = pd.to_datetime(
            timeline_df["DateDue"], errors="coerce"
        )
        timeline_df = timeline_df.dropna(subset=["DueDateParsed"])
        timeline_df = timeline_df.sort_values("DueDateParsed")

        if timeline_df.empty:
            st.info("No orders with valid due dates.")
        else:
            # Show overdue first
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

            # Upcoming orders grouped by week
            upcoming = timeline_df[
                (timeline_df["DueDateParsed"] >= now)
                | (timeline_df["DateReceived"].notna())
            ]

            if not upcoming.empty:
                upcoming["Week"] = upcoming["DueDateParsed"].dt.to_period("W")
                weeks = upcoming["Week"].unique()

                for week in sorted(weeks):
                    week_orders = upcoming[upcoming["Week"] == week]
                    week_start = week.start_time.strftime("%b %d")
                    week_end = week.end_time.strftime("%b %d, %Y")

                    st.markdown(f"#### Week of {week_start} - {week_end}")

                    for _, row in week_orders.iterrows():
                        status = get_order_status(row)
                        status_icon = "✅" if status == "received" else "⏳"
                        st.markdown(
                            f"- {status_icon} **{row['Supplier']}** — "
                            f"Due {format_date(row['DateDue'])} — "
                            f"{int(row['ItemCount'])} items — "
                            f"{format_currency(row['TotalCost'])}"
                        )

                    st.markdown("")


# ==================== TAB 3: ALL ITEMS ====================
with tab_items:
    st.markdown("### 📦 All Order Items (Expanded)")

    # Filter items to matching orders
    filtered_items = order_df[order_df["OrderID"].isin(filtered_order_ids)].copy()

    if filtered_items.empty:
        st.info("No items match current filters.")
    else:
        # Item-level search
        item_search = st.text_input(
            "Search items",
            placeholder="Search by item name, code, variety...",
            key="item_search",
        )

        if item_search:
            search_lower = item_search.lower()
            mask = (
                filtered_items["Item"].str.lower().str.contains(search_lower, na=False)
                | filtered_items["Variety"]
                .str.lower()
                .str.contains(search_lower, na=False)
                | filtered_items["ItemCode"]
                .str.lower()
                .str.contains(search_lower, na=False)
            )
            filtered_items = filtered_items[mask]

        st.markdown(
            f"**{len(filtered_items)} items across {filtered_items['OrderID'].nunique()} orders**"
        )

        display_cols = [
            c
            for c in [
                "OrderItemID",
                "OrderID",
                "Supplier",
                "Item",
                "Variety",
                "Color",
                "ItemCode",
                "NumberOfUnits",
                "Unit",
                "UnitPrice",
                "Received",
                "OrderItemType",
                "DateDue",
                "DateReceived",
                "OrderNoteDecode",
                "OrderItemComments",
                "Leftover",
                "ToOrder",
                "LocationName",
            ]
            if c in filtered_items.columns
        ]

        items_display = filtered_items[display_cols].copy()

        column_config = {
            "OrderItemID": st.column_config.NumberColumn("Item ID", width="small"),
            "OrderID": st.column_config.NumberColumn("Order", width="small"),
            "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
            "Item": st.column_config.TextColumn("Item", width="medium"),
            "Variety": st.column_config.TextColumn("Variety", width="small"),
            "Color": st.column_config.TextColumn("Color", width="small"),
            "ItemCode": st.column_config.TextColumn("Code", width="small"),
            "NumberOfUnits": st.column_config.TextColumn("Qty", width="small"),
            "Unit": st.column_config.TextColumn("Unit", width="small"),
            "UnitPrice": st.column_config.NumberColumn(
                "Price", format="$%.2f", width="small"
            ),
            "Received": st.column_config.CheckboxColumn("Rcvd", width="small"),
            "OrderItemType": st.column_config.TextColumn("Type", width="small"),
            "DateDue": st.column_config.DatetimeColumn(
                "Due", format="MMM DD, YYYY", width="small"
            ),
            "DateReceived": st.column_config.DatetimeColumn(
                "Received", format="MMM DD, YYYY", width="small"
            ),
            "OrderNoteDecode": st.column_config.TextColumn("Note", width="medium"),
            "OrderItemComments": st.column_config.TextColumn(
                "Comments", width="medium"
            ),
            "Leftover": st.column_config.TextColumn("Leftover", width="small"),
            "ToOrder": st.column_config.TextColumn("To Order", width="small"),
            "LocationName": st.column_config.TextColumn("Destination", width="small"),
        }

        st.dataframe(
            items_display.head(200),
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )

        if len(items_display) > 200:
            st.caption(f"Showing first 200 of {len(items_display)} items")


# ==================== TAB 4: RECEIVING ====================
with tab_receiving:
    st.markdown("### ✅ Receive Orders")
    st.markdown("Mark items as received, note condition, assign destinations.")

    # Only show pending orders
    pending_orders = filtered_summary[filtered_summary["DateReceived"].isna()].copy()

    if pending_orders.empty:
        st.success("🎉 All orders have been received!")
    else:
        st.markdown(f"**{len(pending_orders)} orders pending**")

        for _, order_row in pending_orders.head(
            st.session_state.results_limit
        ).iterrows():
            order_id = order_row["OrderID"]
            supplier = (
                order_row["Supplier"] if pd.notna(order_row["Supplier"]) else "Unknown"
            )
            order_num = (
                order_row["OrderNumber"]
                if pd.notna(order_row["OrderNumber"])
                else "N/A"
            )

            status = get_order_status(order_row)
            status_label = "⚠️ OVERDUE" if status == "overdue" else "⏳ Pending"

            with st.expander(
                f"{status_label} — {supplier} — Order #{order_num} — Due {format_date(order_row['DateDue'])}",
                expanded=False,
            ):
                # Order-level receive
                recv_col1, recv_col2 = st.columns([1, 3])

                with recv_col1:
                    if st.button(
                        "✅ Mark Entire Order Received",
                        key=f"recv_order_{order_id}",
                        use_container_width=True,
                    ):
                        try:
                            api.generic_update(
                                model_class=Order,
                                id_column="OrderID",
                                id_value=order_id,
                                updates={"DateReceived": datetime.now()},
                                allowed_fields={"DateReceived", "OrderComments"},
                            )
                            st.success(f"✅ Order #{order_num} marked as received!")
                            refresh_data()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

                with recv_col2:
                    order_comment = st.text_input(
                        "Receiving notes (condition, issues, etc.)",
                        key=f"recv_comment_{order_id}",
                        placeholder="e.g., 2 flats damaged, rest in good condition",
                    )
                    if order_comment:
                        if st.button(
                            "💾 Save Note",
                            key=f"save_comment_{order_id}",
                        ):
                            existing_comments = (
                                order_row["OrderComments"]
                                if pd.notna(order_row.get("OrderComments"))
                                else ""
                            )
                            timestamp = datetime.now().strftime("%m/%d/%y")
                            updated_comments = f"{existing_comments}\n[{timestamp}] {order_comment}".strip()
                            try:
                                api.generic_update(
                                    model_class=Order,
                                    id_column="OrderID",
                                    id_value=order_id,
                                    updates={"OrderComments": updated_comments},
                                    allowed_fields={"OrderComments", "DateReceived"},
                                )
                                st.success("💾 Note saved!")
                                refresh_data()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")

                # Item-level details
                st.markdown("**Items:**")
                items = order_df[order_df["OrderID"] == order_id].copy()

                if not items.empty:
                    for item_idx, item_row in items.iterrows():
                        item_id = item_row["OrderItemID"]
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
                        received = item_row.get("Received", False)

                        i_col1, i_col2, i_col3, i_col4 = st.columns([3, 1, 1, 1])

                        with i_col1:
                            received_marker = "✅" if received else "⬜"
                            st.markdown(
                                f"{received_marker} **{item_name}{variety}** — {qty} {unit}"
                            )

                        with i_col2:
                            if not received:
                                if st.button(
                                    "Receive",
                                    key=f"recv_item_{item_id}",
                                ):
                                    try:
                                        api.generic_update(
                                            model_class=OrderItem,
                                            id_column="OrderItemID",
                                            id_value=item_id,
                                            updates={"Received": True},
                                            allowed_fields={
                                                "Received",
                                                "OrderComments",
                                                "Leftover",
                                            },
                                        )
                                        st.success(f"✅ {item_name} received!")
                                        refresh_data()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ {e}")

                        with i_col3:
                            item_note = st.text_input(
                                "Condition",
                                key=f"item_note_{item_id}",
                                placeholder="Good / Damaged / Short",
                                label_visibility="collapsed",
                            )
                            if item_note:
                                if st.button("💾", key=f"save_item_note_{item_id}"):
                                    existing = (
                                        item_row["OrderItemComments"]
                                        if pd.notna(item_row.get("OrderItemComments"))
                                        else ""
                                    )
                                    timestamp = datetime.now().strftime("%m/%d/%y")
                                    updated = (
                                        f"{existing}\n[{timestamp}] {item_note}".strip()
                                    )
                                    try:
                                        api.generic_update(
                                            model_class=OrderItem,
                                            id_column="OrderItemID",
                                            id_value=item_id,
                                            updates={"OrderComments": updated},
                                            allowed_fields={
                                                "Received",
                                                "OrderComments",
                                                "Leftover",
                                            },
                                        )
                                        refresh_data()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ {e}")

                        with i_col4:
                            dest = (
                                item_row["LocationName"]
                                if pd.notna(item_row.get("LocationName"))
                                else "—"
                            )
                            st.caption(f"📍 {dest}")


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
