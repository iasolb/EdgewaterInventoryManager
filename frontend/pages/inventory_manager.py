"""
Inventory Manager - Edgewater Inventory Management System
Modern card-based interface with expandable details
Author: Ian Solberg
Date: 1-31-2026
"""

# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from rest.api import EdgewaterAPI
from models import Inventory, Item, Unit

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== INITIALIZE API =====
api = EdgewaterAPI()

# Hide default navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Set background
api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.95, blur=0
)

# ===== CUSTOM CSS FOR CARD LAYOUT =====
st.markdown(
    """
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Card container */
    .inventory-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .inventory-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* Card header */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .item-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a1a1a;
        margin: 0;
    }
    
    .count-badge {
        background: #4CAF50;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    /* Card body */
    .card-info {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 12px;
    }
    
    .info-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .info-label {
        color: #666;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .info-value {
        color: #1a1a1a;
        font-size: 0.9rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .badge-active {
        background: #e8f5e9;
        color: #2e7d32;
    }
    
    .badge-inactive {
        background: #ffebee;
        color: #c62828;
    }
    
    .badge-should-stock {
        background: #e3f2fd;
        color: #1565c0;
    }
    
    /* Add inventory button */
    .add-inventory-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 50px;
        padding: 16px 28px;
        font-size: 1rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        cursor: pointer;
        z-index: 1000;
        transition: all 0.3s ease;
    }
    
    .add-inventory-btn:hover {
        background: #45a049;
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.5);
        transform: translateY(-2px);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: rgba(255, 255, 255, 0.98);
        padding: 20px;
    }
    
    /* Filter section */
    .filter-section {
        background: white;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #666;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    
    /* Modal overlay */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999;
    }
    
    /* Expandable details */
    .details-section {
        border-top: 1px solid #e0e0e0;
        margin-top: 16px;
        padding-top: 16px;
    }
    
    .details-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
    }
    
    .detail-card {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
    }
    
    .detail-label {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .detail-value {
        font-size: 0.95rem;
        color: #1a1a1a;
        font-weight: 500;
    }
    
    /* Loading state */
    .loading-skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
        height: 100px;
        margin-bottom: 16px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SESSION STATE =====
if "expanded_card" not in st.session_state:
    st.session_state.expanded_card = None
if "show_add_modal" not in st.session_state:
    st.session_state.show_add_modal = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}
if "filter_search" not in st.session_state:
    st.session_state.filter_search = ""
if "filter_types" not in st.session_state:
    st.session_state.filter_types = []
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "All"
if "results_limit" not in st.session_state:
    st.session_state.results_limit = 25

# ===== CACHE DATA =====
api.reset_cache("inventory_view_cache", api.get_inventory_view_full)
api.reset_cache("item_cache", api.get_item_full)
api.reset_cache("item_type_cache", api.get_item_type_full)
api.reset_cache("unit_cache", api.get_unit_full)


def refresh_data():
    """Refresh all cached data"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("inventory_view_cache", api.get_inventory_view_full)
        api.reset_cache("item_cache", api.get_item_full)
        api.reset_cache("item_type_cache", api.get_item_type_full)
        api.reset_cache("unit_cache", api.get_unit_full)
    st.success("✅ Data refreshed!", icon="✅")


def toggle_card_expansion(inventory_id):
    """Toggle expansion state of a card"""
    if st.session_state.expanded_card == inventory_id:
        st.session_state.expanded_card = None
    else:
        st.session_state.expanded_card = inventory_id


def format_date(date_value):
    """Format datetime for display"""
    if pd.isna(date_value):
        return "Not set"
    if isinstance(date_value, str):
        try:
            date_value = pd.to_datetime(date_value)
        except:
            return date_value
    return date_value.strftime("%b %d, %Y")


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### 🌿 Edgewater Inventory")
    st.markdown("---")

    # Back button
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("edgewater.py")

    st.markdown("---")

    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    # Search filter
    search_term = st.text_input(
        "Search items",
        value=st.session_state.filter_search,
        placeholder="Search by name, variety, color...",
        key="search_input",
    )
    if search_term != st.session_state.filter_search:
        st.session_state.filter_search = search_term
        st.rerun()

    # Item type filter
    item_types = (
        api.item_type_cache["Type"].tolist() if not api.item_type_cache.empty else []
    )
    selected_types = st.multiselect(
        "Item Types",
        options=item_types,
        default=st.session_state.filter_types,
        key="type_filter",
    )
    if selected_types != st.session_state.filter_types:
        st.session_state.filter_types = selected_types
        st.rerun()

    # Status filter
    status_options = ["All", "Active", "Inactive", "Should Stock"]
    selected_status = st.selectbox(
        "Status",
        options=status_options,
        index=status_options.index(st.session_state.filter_status),
        key="status_filter",
    )
    if selected_status != st.session_state.filter_status:
        st.session_state.filter_status = selected_status
        st.rerun()

    # Clear filters
    if st.button("Clear All Filters", use_container_width=True):
        st.session_state.filter_search = ""
        st.session_state.filter_types = []
        st.session_state.filter_status = "All"
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Display Options")

    # Results limit selector
    results_limit = st.selectbox(
        "Show Results",
        options=[10, 25, 50, 100],
        index=[10, 25, 50, 100].index(st.session_state.results_limit),
        key="limit_selector",
    )
    if results_limit != st.session_state.results_limit:
        st.session_state.results_limit = results_limit
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Statistics")

    # Get inventory data for stats
    inventory_df = api.inventory_view_cache
    if not inventory_df.empty:
        total_items = len(inventory_df)
        unique_items = (
            inventory_df["ItemID"].nunique() if "ItemID" in inventory_df.columns else 0
        )
        active_items = (
            len(inventory_df[inventory_df["Inactive"] == False])
            if "Inactive" in inventory_df.columns
            else 0
        )

        st.metric("Total Counts", total_items)
        st.metric("Unique Items", unique_items)
        st.metric("Active Items", active_items)


# ===== MAIN HEADER =====
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    st.markdown("# 📦 Inventory Manager")

with col3:
    if st.button("➕ Add Inventory Count", type="primary", use_container_width=True):
        st.session_state.show_add_modal = True
        st.rerun()

st.markdown("---")

# ===== GET AND FILTER DATA =====
inventory_df = api.inventory_view_cache.copy()

if inventory_df.empty:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">📦</div>
            <h3>No inventory records found</h3>
            <p>Start by adding your first inventory count</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# Apply filters
filtered_df = inventory_df.copy()

# Search filter
if st.session_state.filter_search:
    search_lower = st.session_state.filter_search.lower()
    mask = (
        filtered_df["Item"].str.lower().str.contains(search_lower, na=False)
        | filtered_df["Variety"].str.lower().str.contains(search_lower, na=False)
        | filtered_df["Color"].str.lower().str.contains(search_lower, na=False)
    )
    filtered_df = filtered_df[mask]

# Type filter
if st.session_state.filter_types:
    filtered_df = filtered_df[filtered_df["Type"].isin(st.session_state.filter_types)]

# Status filter
if st.session_state.filter_status == "Active":
    filtered_df = filtered_df[filtered_df["Inactive"] == False]
elif st.session_state.filter_status == "Inactive":
    filtered_df = filtered_df[filtered_df["Inactive"] == True]
elif st.session_state.filter_status == "Should Stock":
    filtered_df = filtered_df[filtered_df["ShouldStock"] == True]

# Sort by date (newest first)
if "DateCounted" in filtered_df.columns:
    filtered_df = filtered_df.sort_values("DateCounted", ascending=False)

# Store total count before limiting
total_filtered = len(filtered_df)

# Apply results limit for display performance
filtered_df = filtered_df.head(st.session_state.results_limit)

# ===== DISPLAY RESULTS INFO =====
result_col1, result_col2 = st.columns([3, 1])
with result_col1:
    if total_filtered > st.session_state.results_limit:
        st.markdown(
            f"### Showing {len(filtered_df)} of {total_filtered} matching records ({len(inventory_df)} total)"
        )
    else:
        st.markdown(
            f"### Showing {len(filtered_df)} of {len(inventory_df)} inventory counts"
        )
with result_col2:
    view_mode = st.selectbox(
        "View", ["Cards", "Table"], key="view_mode", label_visibility="collapsed"
    )

st.markdown("---")

# ===== ADD INVENTORY MODAL =====
if st.session_state.show_add_modal:
    with st.container():
        st.markdown("### ➕ Add New Inventory Count")

        with st.form("add_inventory_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                # Item selection
                items_df = api.item_cache
                item_options = items_df.apply(
                    lambda x: (
                        f"{x['Item']} - {x['Variety']}"
                        if pd.notna(x["Variety"])
                        else x["Item"]
                    ),
                    axis=1,
                ).tolist()
                item_ids = items_df["ItemID"].tolist()

                selected_item_idx = st.selectbox(
                    "Select Item *",
                    options=range(len(item_options)),
                    format_func=lambda i: item_options[i],
                    key="form_item",
                )
                selected_item_id = (
                    item_ids[selected_item_idx]
                    if selected_item_idx is not None
                    else None
                )

                # Unit selection
                units_df = api.unit_cache
                unit_options = units_df.apply(
                    lambda x: (
                        f"{x['UnitType']} - {x['UnitSize']}"
                        if pd.notna(x["UnitSize"])
                        else x["UnitType"]
                    ),
                    axis=1,
                ).tolist()
                unit_ids = units_df["UnitID"].tolist()

                selected_unit_idx = st.selectbox(
                    "Select Unit *",
                    options=range(len(unit_options)),
                    format_func=lambda i: unit_options[i],
                    key="form_unit",
                )
                selected_unit_id = (
                    unit_ids[selected_unit_idx]
                    if selected_unit_idx is not None
                    else None
                )

            with col2:
                number_of_units = st.number_input(
                    "Number of Units *", min_value=0.0, step=1.0, key="form_count"
                )

                date_counted = st.date_input(
                    "Date Counted", value=datetime.now().date(), key="form_date"
                )

            comments = st.text_area(
                "Comments (Optional)", key="form_comments", height=100
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                submitted = st.form_submit_button(
                    "💾 Add Count", type="primary", use_container_width=True
                )

            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                if selected_item_id and selected_unit_id and number_of_units:
                    try:
                        api.table_add_inventory(
                            ItemID=selected_item_id,
                            UnitID=selected_unit_id,
                            NumberOfUnits=number_of_units,
                            DateCounted=datetime.combine(
                                date_counted, datetime.min.time()
                            ),
                            InventoryComments=comments if comments else None,
                        )
                        st.success("✅ Inventory count added successfully!")
                        st.session_state.show_add_modal = False
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding inventory: {e}")
                else:
                    st.error("❌ Please fill in all required fields")

            if cancelled:
                st.session_state.show_add_modal = False
                st.rerun()

        st.markdown("---")

# ===== DISPLAY INVENTORY CARDS OR TABLE =====
if view_mode == "Cards":
    # Card view
    for idx, row in filtered_df.iterrows():
        is_expanded = st.session_state.expanded_card == row["InventoryID"]

        with st.container():
            # Card header
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                item_display = row["Item"]
                if pd.notna(row["Variety"]):
                    item_display += f" - {row['Variety']}"
                if pd.notna(row["Color"]):
                    item_display += f" ({row['Color']})"

                st.markdown(f"### {item_display}")

            with col2:
                st.markdown(
                    f'<div class="count-badge">{row["NumberOfUnits"]} {row["UnitType"]}</div>',
                    unsafe_allow_html=True,
                )

            with col3:
                if st.button(
                    "👁️ Details" if not is_expanded else "➖ Collapse",
                    key=f"expand_{row['InventoryID']}",
                ):
                    toggle_card_expansion(row["InventoryID"])
                    st.rerun()

            # Card info
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"**Type:** {row['Type']}")

            with col2:
                st.markdown(f"**Counted:** {format_date(row['DateCounted'])}")

            with col3:
                st.markdown(f"**Unit:** {row['UnitType']} - {row['UnitSize']}")

            with col4:
                status_class = "badge-inactive" if row["Inactive"] else "badge-active"
                status_text = "Inactive" if row["Inactive"] else "Active"
                st.markdown(
                    f'<span class="status-badge {status_class}">{status_text}</span>',
                    unsafe_allow_html=True,
                )

            # Expandable details
            if is_expanded:
                st.markdown("---")
                st.markdown("#### 📋 Detailed Information")

                detail_col1, detail_col2, detail_col3 = st.columns(3)

                with detail_col1:
                    st.markdown("**Item Details**")
                    st.markdown(f"- **Item ID:** {row['ItemID']}")
                    st.markdown(f"- **Inventory ID:** {row['InventoryID']}")
                    st.markdown(
                        f"- **Sun Conditions:** {row['SunConditions'] if pd.notna(row['SunConditions']) else 'Not specified'}"
                    )
                    st.markdown(
                        f"- **Should Stock:** {'Yes' if row['ShouldStock'] else 'No'}"
                    )

                with detail_col2:
                    st.markdown("**Unit Information**")
                    st.markdown(f"- **Unit ID:** {row['UnitID']}")
                    st.markdown(
                        f"- **Unit Category:** {row['UnitCategory'] if pd.notna(row['UnitCategory']) else 'Not specified'}"
                    )
                    st.markdown(
                        f"- **Picture Link:** {row['PictureLink'] if pd.notna(row['PictureLink']) else 'None'}"
                    )

                with detail_col3:
                    st.markdown("**Additional Info**")
                    if pd.notna(row["InventoryComments"]):
                        st.markdown(f"**Comments:**")
                        st.info(row["InventoryComments"])
                    else:
                        st.markdown("*No comments*")

                    if pd.notna(row["LabelDescription"]):
                        st.markdown(f"**Label Description:**")
                        st.info(row["LabelDescription"])

                # Action buttons in expanded view
                st.markdown("---")
                action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

                with action_col1:
                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{row['InventoryID']}",
                        use_container_width=True,
                    ):
                        st.session_state.edit_mode[row["InventoryID"]] = True
                        st.rerun()

                with action_col2:
                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{row['InventoryID']}",
                        use_container_width=True,
                    ):
                        if st.confirm(
                            f"Are you sure you want to delete this inventory count?"
                        ):
                            try:
                                api._delete(
                                    Inventory, "InventoryID", row["InventoryID"]
                                )
                                st.success("✅ Deleted successfully!")
                                refresh_data()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting: {e}")

            st.markdown("---")

else:
    # Table view
    display_columns = [
        "InventoryID",
        "Item",
        "Variety",
        "Color",
        "Type",
        "NumberOfUnits",
        "UnitType",
        "DateCounted",
        "Inactive",
        "ShouldStock",
    ]

    display_df = filtered_df[display_columns].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "InventoryID": st.column_config.NumberColumn("ID", width="small"),
            "Item": st.column_config.TextColumn("Item", width="medium"),
            "Variety": st.column_config.TextColumn("Variety", width="small"),
            "Color": st.column_config.TextColumn("Color", width="small"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "NumberOfUnits": st.column_config.TextColumn("Count", width="small"),
            "UnitType": st.column_config.TextColumn("Unit", width="small"),
            "DateCounted": st.column_config.DatetimeColumn(
                "Date Counted", format="MMM DD, YYYY"
            ),
            "Inactive": st.column_config.CheckboxColumn("Inactive", width="small"),
            "ShouldStock": st.column_config.CheckboxColumn("Stock?", width="small"),
        },
    )

# ===== FOOTER =====
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if total_filtered > st.session_state.results_limit:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Displaying {len(filtered_df)} of {total_filtered} matching records (limited for performance)"
        )
    else:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Displaying {len(filtered_df)} records"
        )

with col2:
    st.caption("Edgewater Farm Inventory System")
