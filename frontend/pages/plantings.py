"""
Plantings Tracker - Edgewater Inventory Management System
Track what's planted, where, when, with seasonal notes and destinations
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-3-2026 - Full build with locations, destinations, seasonal notes
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
from models import Planting, SeasonalNotes

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Plantings Tracker",
    page_icon="🌱",
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

    .count-badge {
        background: #4CAF50;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
    }

    .location-badge {
        background: #FF9800;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .destination-badge {
        background: #2196F3;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .note-badge {
        background: #9C27B0;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }

    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .badge-active { background: #e8f5e9; color: #2e7d32; }
    .badge-inactive { background: #ffebee; color: #c62828; }
    .badge-greenhouse { background: #fff3e0; color: #e65100; }

    .empty-state {
        text-align: center;
        padding: 60px 20px;
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
if "edit_mode" not in st.session_state or not isinstance(
    st.session_state.edit_mode, dict
):
    st.session_state.edit_mode = {}
if "filter_search" not in st.session_state:
    st.session_state.filter_search = ""
if "filter_types" not in st.session_state:
    st.session_state.filter_types = []
if "filter_locations" not in st.session_state:
    st.session_state.filter_locations = []
if "results_limit" not in st.session_state:
    st.session_state.results_limit = 25

# ===== CACHE DATA =====
# Lookup tables auto-cached via @st.cache_data
# View data loaded lazily into session_state


def refresh_data():
    """Refresh all data for this page"""
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("plantings")
        api.clear_lookup_caches()
    st.success("✅ Data refreshed!", icon="✅")


def toggle_card_expansion(planting_id):
    if st.session_state.expanded_card == planting_id:
        st.session_state.expanded_card = None
    else:
        st.session_state.expanded_card = planting_id


def format_date(date_value):
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
    st.markdown("### 🌱 Plantings Tracker")
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
        "Search plantings",
        value=st.session_state.filter_search,
        placeholder="Search by item, variety, color...",
        key="search_input",
    )
    if search_term != st.session_state.filter_search:
        st.session_state.filter_search = search_term
        st.rerun()

    # Type filter
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

    # Location filter
    location_options = (
        api.location_cache["Location"].tolist()
        if api.location_cache is not None and not api.location_cache.empty
        else []
    )
    selected_locations = st.multiselect(
        "Planted Location",
        options=location_options,
        default=st.session_state.filter_locations,
        key="location_filter",
    )
    if selected_locations != st.session_state.filter_locations:
        st.session_state.filter_locations = selected_locations
        st.rerun()

    # Date range
    st.markdown("**Date Range**")
    date_start = st.date_input("From", value=None, key="date_start")
    date_end = st.date_input("To", value=None, key="date_end")

    if st.button("Clear All Filters", use_container_width=True):
        st.session_state.filter_search = ""
        st.session_state.filter_types = []
        st.session_state.filter_locations = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Display Options")

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

    plantings_df = api.planting_view_cache
    if plantings_df is not None and not plantings_df.empty:
        st.metric("Total Plantings", len(plantings_df))
        st.metric(
            "Unique Items",
            plantings_df["ItemID"].nunique() if "ItemID" in plantings_df.columns else 0,
        )
        if "PlantingLocation" in plantings_df.columns:
            locations_used = plantings_df["PlantingLocation"].dropna().nunique()
            st.metric("Locations Used", locations_used)


# ===== MAIN HEADER =====
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    st.markdown("# 🌱 Plantings Tracker")

with col3:
    if st.button("➕ Add Planting", use_container_width=True):
        st.session_state.show_add_modal = True
        st.rerun()

st.markdown("---")

# ===== GET AND FILTER DATA =====
plantings_df = (
    api.planting_view_cache.copy()
    if api.planting_view_cache is not None
    else pd.DataFrame()
)

if plantings_df.empty:
    st.markdown(
        """
        <div class="empty-state">
            <div style="font-size: 4rem; margin-bottom: 20px;">🌱</div>
            <h3>No planting records found</h3>
            <p>Start by adding your first planting</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

filtered_df = plantings_df.copy()

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

# Location filter
if st.session_state.filter_locations and "PlantingLocation" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["PlantingLocation"].isin(st.session_state.filter_locations)
    ]

# Date filters
if date_start:
    filtered_df = filtered_df[filtered_df["DatePlanted"] >= pd.to_datetime(date_start)]
if date_end:
    filtered_df = filtered_df[filtered_df["DatePlanted"] <= pd.to_datetime(date_end)]

# Sort newest first
if "DatePlanted" in filtered_df.columns:
    filtered_df = filtered_df.sort_values("DatePlanted", ascending=False)

total_filtered = len(filtered_df)
filtered_df = filtered_df.head(st.session_state.results_limit)

# Store filtered set as working set for fast card expansion lookups
api.set_working_set("plantings", filtered_df)

# ===== DISPLAY RESULTS INFO =====
result_col1, result_col2 = st.columns([3, 1])
with result_col1:
    if total_filtered > st.session_state.results_limit:
        st.markdown(
            f"### Showing {len(filtered_df)} of {total_filtered} matching records ({len(plantings_df)} total)"
        )
    else:
        st.markdown(f"### Showing {len(filtered_df)} of {len(plantings_df)} plantings")
with result_col2:
    view_mode = st.selectbox(
        "View", ["Cards", "Table"], key="view_mode", label_visibility="collapsed"
    )

st.markdown("---")

# ===== ADD PLANTING MODAL =====
if st.session_state.show_add_modal:
    with st.container():
        st.markdown("### ➕ Add New Planting")

        with st.form("add_planting_form", clear_on_submit=True):
            items_df = api.item_cache
            units_df = api.unit_cache

            if items_df is None or items_df.empty or units_df is None or units_df.empty:
                st.warning("⚠️ Item or Unit data not loaded. Please refresh data.")
                st.form_submit_button("💾 Add Planting", disabled=True)
            else:
                col1, col2 = st.columns(2)

                with col1:
                    # Item selection
                    item_options = items_df.apply(
                        lambda x: (
                            f"{x['Item']} - {x['Variety']}"
                            if pd.notna(x["Variety"])
                            else str(x["Item"])
                        ),
                        axis=1,
                    ).tolist()
                    item_ids = items_df["ItemID"].tolist()

                    selected_item_label = st.selectbox(
                        "Select Item *",
                        options=item_options,
                        key="form_item",
                    )
                    selected_item_id = (
                        item_ids[item_options.index(selected_item_label)]
                        if selected_item_label
                        else None
                    )

                    # Unit selection
                    unit_options = units_df.apply(
                        lambda x: (
                            f"{x['UnitType']} - {x['UnitSize']}"
                            if pd.notna(x["UnitSize"])
                            else str(x["UnitType"])
                        ),
                        axis=1,
                    ).tolist()
                    unit_ids = units_df["UnitID"].tolist()

                    selected_unit_label = st.selectbox(
                        "Select Unit *",
                        options=unit_options,
                        key="form_unit",
                    )
                    selected_unit_id = (
                        unit_ids[unit_options.index(selected_unit_label)]
                        if selected_unit_label
                        else None
                    )

                    number_of_units = st.number_input(
                        "Number of Units *", min_value=0.0, step=1.0, key="form_count"
                    )

                with col2:
                    date_planted = st.date_input(
                        "Date Planted", value=datetime.now().date(), key="form_date"
                    )

                    # Location selection
                    loc_df = api.location_cache
                    if loc_df is not None and not loc_df.empty:
                        loc_options = ["None"] + loc_df["Location"].tolist()
                        loc_ids = [None] + loc_df["LocationID"].tolist()

                        selected_loc_label = st.selectbox(
                            "Location",
                            options=loc_options,
                            key="form_location",
                        )
                        selected_location_id = loc_ids[
                            loc_options.index(selected_loc_label)
                        ]
                    else:
                        selected_location_id = None
                        st.caption("No locations configured")

                    comments = st.text_area(
                        "Planting Comments", key="form_comments", height=100
                    )

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    submitted = st.form_submit_button(
                        "💾 Add Planting", type="primary", use_container_width=True
                    )

                with col2:
                    cancelled = st.form_submit_button(
                        "Cancel", use_container_width=True
                    )

                if submitted:
                    if selected_item_id and selected_unit_id and number_of_units:
                        try:
                            api.table_add_planting(
                                ItemID=selected_item_id,
                                UnitID=selected_unit_id,
                                NumberOfUnits=str(number_of_units),
                                DatePlanted=datetime.combine(
                                    date_planted, datetime.min.time()
                                ),
                                PlantingComments=comments if comments else None,
                                LocationID=selected_location_id,
                            )
                            st.success("✅ Planting added successfully!")
                            st.session_state.show_add_modal = False
                            refresh_data()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error adding planting: {e}")
                    else:
                        st.error("❌ Please fill in all required fields")

                if cancelled:
                    st.session_state.show_add_modal = False
                    st.rerun()

        st.markdown("---")

# ===== DISPLAY CARDS OR TABLE =====
if view_mode == "Cards":
    for idx, row in filtered_df.iterrows():
        is_expanded = st.session_state.expanded_card == row["PlantingID"]

        with st.container():
            # Card header
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                item_display = row["Item"] if pd.notna(row.get("Item")) else "Unknown"
                if pd.notna(row.get("Variety")):
                    item_display += f" - {row['Variety']}"
                if pd.notna(row.get("Color")):
                    item_display += f" ({row['Color']})"
                st.markdown(f"### {item_display}")

            with col2:
                unit_label = row["UnitType"] if pd.notna(row.get("UnitType")) else ""
                st.markdown(
                    f'<div class="count-badge">{row["NumberOfUnits"]} {unit_label}</div>',
                    unsafe_allow_html=True,
                )

            with col3:
                loc_name = (
                    row["PlantingLocation"]
                    if "PlantingLocation" in row
                    and pd.notna(row.get("PlantingLocation"))
                    else "Unassigned"
                )
                st.markdown(
                    f'<div class="location-badge">📍 {loc_name}</div>',
                    unsafe_allow_html=True,
                )

            with col4:
                if st.button(
                    "👁️ Details" if not is_expanded else "➖ Collapse",
                    key=f"expand_{row['PlantingID']}",
                ):
                    toggle_card_expansion(row["PlantingID"])
                    st.rerun()

            # Card info row
            info1, info2, info3, info4 = st.columns(4)

            with info1:
                st.markdown(
                    f"**Type:** {row['Type'] if pd.notna(row.get('Type')) else 'N/A'}"
                )

            with info2:
                st.markdown(f"**Planted:** {format_date(row['DatePlanted'])}")

            with info3:
                dest = (
                    row["DestinationLocation"]
                    if "DestinationLocation" in row
                    and pd.notna(row.get("DestinationLocation"))
                    else "Not set"
                )
                st.markdown(f"**Destined for:** {dest}")

            with info4:
                if pd.notna(row.get("SeasonalNote")):
                    st.markdown(
                        f'<div class="note-badge">📝 Has Notes</div>',
                        unsafe_allow_html=True,
                    )
                if row.get("Greenhouse"):
                    st.markdown(
                        f'<span class="status-badge badge-greenhouse">🏠 Greenhouse</span>',
                        unsafe_allow_html=True,
                    )

            # Expanded details
            if is_expanded:
                st.markdown("---")

                # Edit mode
                if st.session_state.edit_mode.get(row["PlantingID"], False):
                    st.markdown("#### ✏️ Edit Planting Record")

                    with st.form(f"edit_form_{row['PlantingID']}"):
                        edit_col1, edit_col2, edit_col3 = st.columns(3)

                        with edit_col1:
                            edit_count = st.number_input(
                                "Number of Units",
                                value=(
                                    float(row["NumberOfUnits"])
                                    if row.get("NumberOfUnits")
                                    else 0.0
                                ),
                                step=1.0,
                                key=f"edit_count_{row['PlantingID']}",
                            )
                            edit_date = st.date_input(
                                "Date Planted",
                                value=(
                                    pd.to_datetime(row["DatePlanted"]).date()
                                    if pd.notna(row.get("DatePlanted"))
                                    else datetime.now().date()
                                ),
                                key=f"edit_date_{row['PlantingID']}",
                            )

                        with edit_col2:
                            loc_df = api.location_cache
                            if loc_df is not None and not loc_df.empty:
                                edit_loc_options = ["None"] + loc_df[
                                    "Location"
                                ].tolist()
                                edit_loc_ids = [None] + loc_df["LocationID"].tolist()

                                current_loc_label = "None"
                                if "PlantingLocationID" in row and pd.notna(
                                    row.get("PlantingLocationID")
                                ):
                                    try:
                                        loc_idx = edit_loc_ids.index(
                                            int(row["PlantingLocationID"])
                                        )
                                        current_loc_label = edit_loc_options[loc_idx]
                                    except (ValueError, TypeError):
                                        current_loc_label = "None"

                                edit_loc_label = st.selectbox(
                                    "Location",
                                    options=edit_loc_options,
                                    index=edit_loc_options.index(current_loc_label),
                                    key=f"edit_loc_{row['PlantingID']}",
                                )
                                edit_location_id = edit_loc_ids[
                                    edit_loc_options.index(edit_loc_label)
                                ]
                            else:
                                edit_location_id = None

                        with edit_col3:
                            edit_comments = st.text_area(
                                "Comments",
                                value=(
                                    row["PlantingComments"]
                                    if pd.notna(row.get("PlantingComments"))
                                    else ""
                                ),
                                key=f"edit_comments_{row['PlantingID']}",
                            )

                        save_col1, save_col2, save_col3 = st.columns([1, 1, 3])

                        with save_col1:
                            save_btn = st.form_submit_button(
                                "💾 Save", type="primary", use_container_width=True
                            )

                        with save_col2:
                            cancel_btn = st.form_submit_button(
                                "Cancel", use_container_width=True
                            )

                        if save_btn:
                            updates = {
                                "NumberOfUnits": str(edit_count),
                                "DatePlanted": datetime.combine(
                                    edit_date, datetime.min.time()
                                ),
                                "PlantingComments": edit_comments or None,
                                "LocationID": edit_location_id,
                            }

                            allowed_fields = {
                                "ItemID",
                                "UnitID",
                                "NumberOfUnits",
                                "DatePlanted",
                                "PlantingComments",
                                "LocationID",
                            }

                            result = api.generic_update(
                                model_class=Planting,
                                id_column="PlantingID",
                                id_value=row["PlantingID"],
                                updates=updates,
                                allowed_fields=allowed_fields,
                            )

                            if result:
                                st.success("✅ Updated successfully!")
                                st.session_state.edit_mode[row["PlantingID"]] = False
                                refresh_data()
                                st.rerun()
                            else:
                                st.error("❌ Update failed")

                        if cancel_btn:
                            st.session_state.edit_mode[row["PlantingID"]] = False
                            st.rerun()

                else:
                    # Read-only expanded details
                    st.markdown("#### 📋 Detailed Information")

                    detail_col1, detail_col2, detail_col3 = st.columns(3)

                    with detail_col1:
                        st.markdown("**Item Details**")
                        st.markdown(f"- **Item ID:** {row['ItemID']}")
                        st.markdown(f"- **Planting ID:** {row['PlantingID']}")
                        st.markdown(
                            f"- **Sun Conditions:** {row['SunConditions'] if pd.notna(row.get('SunConditions')) else 'Not specified'}"
                        )
                        st.markdown(
                            f"- **Should Stock:** {'Yes' if row.get('ShouldStock') else 'No'}"
                        )
                        inactive_status = "Yes" if row.get("Inactive") else "No"
                        st.markdown(f"- **Inactive:** {inactive_status}")

                    with detail_col2:
                        st.markdown("**Location & Destination**")
                        planted_loc = (
                            row["PlantingLocation"]
                            if pd.notna(row.get("PlantingLocation"))
                            else "Unassigned"
                        )
                        st.markdown(f"- **Planted at:** {planted_loc}")

                        dest_loc = (
                            row["DestinationLocation"]
                            if pd.notna(row.get("DestinationLocation"))
                            else "Not set"
                        )
                        st.markdown(f"- **Destined for:** {dest_loc}")

                        units_destined = (
                            row["UnitsDestined"]
                            if pd.notna(row.get("UnitsDestined"))
                            else "N/A"
                        )
                        st.markdown(f"- **Units Destined:** {units_destined}")

                        purpose = (
                            row["PurposeComments"]
                            if pd.notna(row.get("PurposeComments"))
                            else "None"
                        )
                        st.markdown(f"- **Purpose:** {purpose}")

                        st.markdown(
                            f"- **Unit:** {row.get('UnitType', '')} - {row.get('UnitSize', '')}"
                        )
                        st.markdown(
                            f"- **Unit Category:** {row['UnitCategory'] if pd.notna(row.get('UnitCategory')) else 'N/A'}"
                        )

                    with detail_col3:
                        st.markdown("**Seasonal Notes**")
                        if pd.notna(row.get("SeasonalNote")):
                            greenhouse_text = (
                                "🏠 Greenhouse"
                                if row.get("Greenhouse")
                                else "🌿 Outdoor"
                            )
                            st.markdown(f"- **Environment:** {greenhouse_text}")
                            st.markdown(
                                f"- **Season ID:** {int(row['GrowingSeasonID']) if pd.notna(row.get('GrowingSeasonID')) else 'N/A'}"
                            )
                            st.info(row["SeasonalNote"])
                            if pd.notna(row.get("NoteLastUpdate")):
                                st.caption(
                                    f"Last updated: {format_date(row['NoteLastUpdate'])}"
                                )
                        else:
                            st.markdown("*No seasonal notes for this planting*")

                        if pd.notna(row.get("PlantingComments")):
                            st.markdown("**Planting Comments:**")
                            st.info(row["PlantingComments"])

                        if pd.notna(row.get("Definition")):
                            st.markdown("**Definition:**")
                            st.caption(row["Definition"])

                    # Action buttons
                    st.markdown("---")
                    action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

                    with action_col1:
                        if st.button(
                            "✏️ Edit",
                            key=f"edit_{row['PlantingID']}",
                            use_container_width=True,
                        ):
                            st.session_state.edit_mode[row["PlantingID"]] = True
                            st.rerun()

                    with action_col2:
                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_{row['PlantingID']}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            st.session_state[f"confirm_delete_{row['PlantingID']}"] = (
                                True
                            )
                            st.rerun()

                    # Delete confirmation
                    if st.session_state.get(
                        f"confirm_delete_{row['PlantingID']}", False
                    ):
                        st.warning(
                            f"⚠️ Are you sure you want to delete planting #{row['PlantingID']}?"
                        )
                        confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 3])
                        with confirm_col1:
                            if st.button(
                                "Yes, Delete",
                                key=f"confirm_yes_{row['PlantingID']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    api._delete(
                                        Planting, "PlantingID", row["PlantingID"]
                                    )
                                    st.success("✅ Deleted successfully!")
                                    st.session_state.pop(
                                        f"confirm_delete_{row['PlantingID']}", None
                                    )
                                    refresh_data()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting: {e}")
                        with confirm_col2:
                            if st.button(
                                "Cancel",
                                key=f"confirm_no_{row['PlantingID']}",
                                use_container_width=True,
                            ):
                                st.session_state.pop(
                                    f"confirm_delete_{row['PlantingID']}", None
                                )
                                st.rerun()

            st.markdown("---")

else:
    # Table view
    display_columns = [
        "PlantingID",
        "Item",
        "Variety",
        "Color",
        "Type",
        "NumberOfUnits",
        "UnitType",
        "DatePlanted",
    ]

    if "PlantingLocation" in filtered_df.columns:
        display_columns.append("PlantingLocation")
    if "DestinationLocation" in filtered_df.columns:
        display_columns.append("DestinationLocation")

    display_columns += ["PlantingComments"]

    if "SeasonalNote" in filtered_df.columns:
        display_columns.append("SeasonalNote")

    display_df = filtered_df[
        [c for c in display_columns if c in filtered_df.columns]
    ].copy()

    column_config = {
        "PlantingID": st.column_config.NumberColumn("ID", width="small"),
        "Item": st.column_config.TextColumn("Item", width="medium"),
        "Variety": st.column_config.TextColumn("Variety", width="small"),
        "Color": st.column_config.TextColumn("Color", width="small"),
        "Type": st.column_config.TextColumn("Type", width="small"),
        "NumberOfUnits": st.column_config.TextColumn("Count", width="small"),
        "UnitType": st.column_config.TextColumn("Unit", width="small"),
        "DatePlanted": st.column_config.DatetimeColumn(
            "Date Planted", format="MMM DD, YYYY"
        ),
        "PlantingLocation": st.column_config.TextColumn("Planted At", width="small"),
        "DestinationLocation": st.column_config.TextColumn(
            "Destined For", width="small"
        ),
        "PlantingComments": st.column_config.TextColumn("Comments", width="medium"),
        "SeasonalNote": st.column_config.TextColumn("Seasonal Note", width="medium"),
    }

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

# ===== FOOTER =====
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if total_filtered > st.session_state.results_limit:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Displaying {len(filtered_df)} of {total_filtered} matching records"
        )
    else:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Displaying {len(filtered_df)} records"
        )

with col2:
    st.caption("Edgewater Farm Inventory System")
