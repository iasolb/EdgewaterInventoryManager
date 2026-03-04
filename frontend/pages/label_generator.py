"""
Label Generator - Edgewater Inventory Management System
Build label orders from item lookup and export to JSON
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-3-2026 - Full build with search, label order builder, JSON export
"""

# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from rest.api import EdgewaterAPI

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Label Generator",
    page_icon="🏷️",
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

    .label-count-badge {
        background: #1565c0;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
    }

    .type-badge {
        background: #4CAF50;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .sun-badge {
        background: #FF9800;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }

    .order-summary-box {
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SESSION STATE =====
if "label_order" not in st.session_state:
    st.session_state.label_order = []  # List of {item_id, item_data, quantity}
if "search_term" not in st.session_state:
    st.session_state.search_term = ""

# ===== CACHE DATA =====
# Lookup tables auto-cached via @st.cache_data
# View data loaded lazily into session_state


def refresh_data():
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("labels")
        api.clear_lookup_caches()
    st.success("✅ Data refreshed!", icon="✅")


def build_item_display_name(row):
    """Build a readable display name from item data"""
    parts = [str(row["Item"])] if pd.notna(row.get("Item")) else ["Unknown"]
    if pd.notna(row.get("Variety")):
        parts.append(f"- {row['Variety']}")
    if pd.notna(row.get("Color")):
        parts.append(f"({row['Color']})")
    return " ".join(parts)


def get_label_data_for_item(item_id):
    """Get all label-relevant data for an item from the label view"""
    label_df = api.label_view_cache
    if label_df is None or label_df.empty:
        return None
    matches = label_df[label_df["ItemID"] == item_id]
    if matches.empty:
        return None
    # Take the first row for base item data (there may be multiple price rows)
    row = matches.iloc[0].to_dict()
    # Collect all prices
    prices = []
    for _, price_row in matches.iterrows():
        if pd.notna(price_row.get("UnitPrice")):
            prices.append(
                {
                    "unit_type": price_row.get("UnitType", ""),
                    "unit_size": price_row.get("UnitSize", ""),
                    "unit_price": float(price_row["UnitPrice"]),
                    "year": str(price_row.get("Year", "")),
                }
            )
    row["prices"] = prices
    return row


def add_to_label_order(item_id, quantity):
    """Add an item to the label order"""
    item_data = get_label_data_for_item(item_id)
    if item_data is None:
        return False

    # Check if already in order — update quantity
    for entry in st.session_state.label_order:
        if entry["item_id"] == item_id:
            entry["quantity"] += quantity
            return True

    st.session_state.label_order.append(
        {
            "item_id": item_id,
            "display_name": build_item_display_name(item_data),
            "item_data": item_data,
            "quantity": quantity,
        }
    )
    return True


def remove_from_label_order(index):
    """Remove item from label order by index"""
    if 0 <= index < len(st.session_state.label_order):
        st.session_state.label_order.pop(index)


def export_label_order_json():
    """Build export JSON from current label order"""
    export = {
        "label_order": {
            "created": datetime.now().isoformat(),
            "total_labels": sum(e["quantity"] for e in st.session_state.label_order),
            "total_items": len(st.session_state.label_order),
        },
        "items": [],
    }

    for entry in st.session_state.label_order:
        data = entry["item_data"]
        item_export = {
            "item_id": entry["item_id"],
            "label_count": entry["quantity"],
            "item_name": data.get("Item", ""),
            "variety": data.get("Variety", ""),
            "color": data.get("Color", ""),
            "type": data.get("Type", ""),
            "sun_conditions": data.get("SunConditions", ""),
            "label_description": data.get("LabelDescription", ""),
            "definition": data.get("Definition", ""),
            "picture_link": data.get("PictureLink", ""),
            "picture_layout": data.get("PictureLayout", ""),
            "prices": data.get("prices", []),
        }

        # Clean up NaN values for JSON
        for key, val in item_export.items():
            if isinstance(val, float) and pd.isna(val):
                item_export[key] = None
            elif isinstance(val, str) and val == "nan":
                item_export[key] = None

        export["items"].append(item_export)

    return export


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### 🏷️ Label Generator")
    st.markdown("---")

    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("edgewater.py")

    st.markdown("---")

    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()
        st.rerun()

    st.markdown("---")

    # Label order summary in sidebar
    st.markdown("### 📋 Current Label Order")

    if st.session_state.label_order:
        total_labels = sum(e["quantity"] for e in st.session_state.label_order)
        st.metric("Items in Order", len(st.session_state.label_order))
        st.metric("Total Labels", total_labels)

        st.markdown("---")

        for i, entry in enumerate(st.session_state.label_order):
            st.markdown(f"**{entry['display_name']}**")
            st.caption(f"× {entry['quantity']} labels")

        st.markdown("---")

        if st.button("🗑️ Clear Entire Order", use_container_width=True):
            st.session_state.label_order = []
            st.rerun()
    else:
        st.caption("No items in order yet. Use the search below to add items.")


# ===== MAIN HEADER =====
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("# 🏷️ Label Generator")

with col2:
    if st.session_state.label_order:
        total = sum(e["quantity"] for e in st.session_state.label_order)
        st.markdown(
            f'<div class="label-count-badge">🏷️ {total} labels in order</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ===== MAIN TABS =====
tab_search, tab_order, tab_export = st.tabs(
    ["🔍 Search & Add Items", "📋 Label Order", "📤 Export"]
)


# ==================== TAB 1: SEARCH & ADD ====================
with tab_search:
    st.markdown("### Find items and add to your label order")

    # Search bar
    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        search_term = st.text_input(
            "Search items",
            value=st.session_state.search_term,
            placeholder="Search by name, variety, color, type...",
            key="item_search_input",
        )

    with search_col2:
        # Type filter for search
        item_types = (
            api.item_type_cache["Type"].tolist()
            if api.item_type_cache is not None and not api.item_type_cache.empty
            else []
        )
        type_filter = st.selectbox(
            "Filter by Type",
            options=["All"] + item_types,
            key="search_type_filter",
        )

    # Get label data
    label_df = (
        api.label_view_cache.copy()
        if api.label_view_cache is not None
        else pd.DataFrame()
    )

    if label_df.empty:
        st.info("No label data available.")
    else:
        # Deduplicate to unique items (label view has multiple rows per item due to price joins)
        unique_items = label_df.drop_duplicates(subset=["ItemID"]).copy()

        # Apply search
        if search_term:
            search_lower = search_term.lower()
            mask = (
                unique_items["Item"].str.lower().str.contains(search_lower, na=False)
                | unique_items["Variety"]
                .str.lower()
                .str.contains(search_lower, na=False)
                | unique_items["Color"].str.lower().str.contains(search_lower, na=False)
                | unique_items["LabelDescription"]
                .str.lower()
                .str.contains(search_lower, na=False)
            )
            unique_items = unique_items[mask]

        # Apply type filter
        if type_filter != "All":
            unique_items = unique_items[unique_items["Type"] == type_filter]

        # Only show active items by default
        unique_items = unique_items[unique_items["Inactive"] != True]

        st.caption(f"{len(unique_items)} items found")

        # Display results
        for _, row in unique_items.head(50).iterrows():
            item_col1, item_col2, item_col3, item_col4 = st.columns([3, 1, 1, 1])

            with item_col1:
                display_name = build_item_display_name(row)
                st.markdown(f"**{display_name}**")

                # Show description preview
                if pd.notna(row.get("LabelDescription")):
                    desc = str(row["LabelDescription"])
                    preview = desc[:100] + "..." if len(desc) > 100 else desc
                    st.caption(preview)

            with item_col2:
                if pd.notna(row.get("Type")):
                    st.markdown(
                        f'<div class="type-badge">{row["Type"]}</div>',
                        unsafe_allow_html=True,
                    )
                if pd.notna(row.get("SunConditions")):
                    st.markdown(
                        f'<div class="sun-badge">☀️ {row["SunConditions"]}</div>',
                        unsafe_allow_html=True,
                    )

            with item_col3:
                # Show price if available
                if pd.notna(row.get("UnitPrice")):
                    st.markdown(f"**${row['UnitPrice']:.2f}**")
                    unit_info = ""
                    if pd.notna(row.get("UnitSize")):
                        unit_info += str(row["UnitSize"])
                    if pd.notna(row.get("UnitType")):
                        unit_info += f" {row['UnitType']}"
                    if unit_info:
                        st.caption(unit_info.strip())

            with item_col4:
                qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=1,
                    step=1,
                    key=f"qty_{row['ItemID']}",
                    label_visibility="collapsed",
                )
                if st.button("➕ Add", key=f"add_{row['ItemID']}"):
                    if add_to_label_order(int(row["ItemID"]), qty):
                        st.success(f"Added {qty}× labels")
                        st.rerun()
                    else:
                        st.error("Could not add item")

        if len(unique_items) > 50:
            st.caption(
                "Showing first 50 results. Refine your search for more specific results."
            )


# ==================== TAB 2: LABEL ORDER ====================
with tab_order:
    st.markdown("### 📋 Current Label Order")

    if not st.session_state.label_order:
        st.info("Your label order is empty. Go to the Search tab to add items.")
    else:
        total_labels = sum(e["quantity"] for e in st.session_state.label_order)
        st.markdown(
            f"**{len(st.session_state.label_order)} items — {total_labels} total labels**"
        )
        st.markdown("---")

        # Display each item in the order
        for i, entry in enumerate(st.session_state.label_order):
            data = entry["item_data"]

            order_col1, order_col2, order_col3, order_col4 = st.columns([3, 1, 1, 1])

            with order_col1:
                st.markdown(f"**{entry['display_name']}**")

                details = []
                if data.get("Type") and pd.notna(data.get("Type")):
                    details.append(f"Type: {data['Type']}")
                if data.get("SunConditions") and pd.notna(data.get("SunConditions")):
                    details.append(f"Sun: {data['SunConditions']}")
                if details:
                    st.caption(" | ".join(details))

                # Show label description
                if data.get("LabelDescription") and pd.notna(
                    data.get("LabelDescription")
                ):
                    with st.expander("Label Description", expanded=False):
                        st.write(data["LabelDescription"])

                # Show prices
                if data.get("prices"):
                    price_strs = [
                        f"${p['unit_price']:.2f} ({p['unit_size']} {p['unit_type']})"
                        for p in data["prices"]
                    ]
                    st.caption("Prices: " + " | ".join(price_strs))

            with order_col2:
                st.markdown(
                    f'<div class="label-count-badge">× {entry["quantity"]}</div>',
                    unsafe_allow_html=True,
                )

            with order_col3:
                new_qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=entry["quantity"],
                    step=1,
                    key=f"order_qty_{i}",
                    label_visibility="collapsed",
                )
                if new_qty != entry["quantity"]:
                    st.session_state.label_order[i]["quantity"] = new_qty
                    st.rerun()

            with order_col4:
                if st.button("🗑️", key=f"remove_{i}"):
                    remove_from_label_order(i)
                    st.rerun()

            st.markdown("---")


# ==================== TAB 3: EXPORT ====================
with tab_export:
    st.markdown("### 📤 Export Label Order")

    if not st.session_state.label_order:
        st.info("Add items to your label order before exporting.")
    else:
        total_labels = sum(e["quantity"] for e in st.session_state.label_order)
        st.markdown(
            f"**Ready to export: {len(st.session_state.label_order)} items, {total_labels} total labels**"
        )

        st.markdown("---")

        # Preview
        st.markdown("#### Preview")

        export_data = export_label_order_json()

        # Summary table
        preview_rows = []
        for item in export_data["items"]:
            price_str = ""
            if item["prices"]:
                price_str = ", ".join(
                    [f"${p['unit_price']:.2f}" for p in item["prices"]]
                )

            preview_rows.append(
                {
                    "Item": item["item_name"],
                    "Variety": item["variety"] or "",
                    "Color": item["color"] or "",
                    "Type": item["type"] or "",
                    "Sun": item["sun_conditions"] or "",
                    "Labels": item["label_count"],
                    "Prices": price_str,
                }
            )

        preview_df = pd.DataFrame(preview_rows)
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Export options
        st.markdown("#### Export Format")

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            # JSON export
            json_str = json.dumps(export_data, indent=2, default=str)

            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"label_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with export_col2:
            # CSV export (flat format)
            csv_rows = []
            for item in export_data["items"]:
                csv_rows.append(
                    {
                        "item_id": item["item_id"],
                        "item_name": item["item_name"],
                        "variety": item["variety"],
                        "color": item["color"],
                        "type": item["type"],
                        "sun_conditions": item["sun_conditions"],
                        "label_description": item["label_description"],
                        "label_count": item["label_count"],
                        "picture_link": item["picture_link"],
                    }
                )

            csv_df = pd.DataFrame(csv_rows)
            csv_str = csv_df.to_csv(index=False)

            st.download_button(
                label="📥 Download CSV",
                data=csv_str,
                file_name=f"label_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")

        # Raw JSON preview
        with st.expander("View Raw JSON", expanded=False):
            st.code(json_str, language="json")


# ===== FOOTER =====
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    label_df = api.label_view_cache
    item_count = (
        label_df["ItemID"].nunique()
        if label_df is not None and not label_df.empty
        else 0
    )
    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"{item_count} items available"
    )

with col2:
    st.caption("Edgewater Farm Inventory System")
