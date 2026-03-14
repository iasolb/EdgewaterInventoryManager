"""
Plantings Tracker - Edgewater Inventory Management System
Track what's planted, where, when, with seasonal notes and destinations
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-3-2026 - Full build with locations, destinations, seasonal notes
Optimized: 3-14-2026 - st.expander replaces button+rerun, pre-indexed lookups,
           cached derived data, FK decode maps, inline editing, tab layout
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
if "filter_search" not in st.session_state:
    st.session_state.filter_search = ""
if "filter_types" not in st.session_state:
    st.session_state.filter_types = []
if "filter_locations" not in st.session_state:
    st.session_state.filter_locations = []
if "results_limit" not in st.session_state:
    st.session_state.results_limit = 25


# ===== HELPERS =====


def refresh_data():
    """Refresh view cache and invalidate derived structures."""
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("plantings")
        api.clear_lookup_caches()
        for key in ("_plant_sorted", "_plant_by_id"):
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


def safe_float(val, default=0.0):
    """Convert a value to float, handling fractions like '1 3/10'."""
    if pd.isna(val) or val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    try:
        return float(s)
    except ValueError:
        pass
    # Handle mixed fractions: "1 3/10" -> 1.3
    try:
        from fractions import Fraction

        parts = s.split()
        if len(parts) == 2:
            return float(int(parts[0]) + Fraction(parts[1]))
        elif len(parts) == 1 and "/" in parts[0]:
            return float(Fraction(parts[0]))
    except Exception:
        pass
    return default


# ================================================================
# SHARED COLUMN CONFIG — built once, reused across tabs
# ================================================================

_COLUMN_CONFIG = {
    "PlantingID": st.column_config.NumberColumn("ID", width="small"),
    "Item": st.column_config.TextColumn("Item", width="medium"),
    "Variety": st.column_config.TextColumn("Variety", width="small"),
    "Color": st.column_config.TextColumn("Color", width="small"),
    "Type": st.column_config.TextColumn("Type", width="small"),
    "NumberOfUnits": st.column_config.TextColumn("Count", width="small"),
    "UnitType": st.column_config.TextColumn("Unit", width="small"),
    "DatePlanted": st.column_config.DatetimeColumn(
        "Date Planted", format="MMM DD, YYYY", width="small"
    ),
    "PlantingLocation": st.column_config.TextColumn("Planted At", width="small"),
    "DestinationLocation": st.column_config.TextColumn("Destined For", width="small"),
    "PlantingComments": st.column_config.TextColumn("Comments", width="medium"),
    "SeasonalNote": st.column_config.TextColumn("Seasonal Note", width="medium"),
    "LocationID": st.column_config.TextColumn("Location", width="small"),
    "Greenhouse": st.column_config.CheckboxColumn("Greenhouse", width="small"),
}

# Columns shown in table view
_TABLE_DISPLAY_COLS = [
    "PlantingID",
    "Item",
    "Variety",
    "Color",
    "Type",
    "NumberOfUnits",
    "UnitType",
    "DatePlanted",
    "PlantingLocation",
    "DestinationLocation",
    "PlantingComments",
    "SeasonalNote",
]

# Columns that map to the Planting base table and can be edited inline
_EDITABLE_PLANTING_COLS = {
    "NumberOfUnits",
    "DatePlanted",
    "PlantingComments",
    "LocationID",
}

# Display labels
_COL_LABELS = {
    "PlantingID": "ID",
    "Item": "Item",
    "Variety": "Variety",
    "Color": "Color",
    "Type": "Type",
    "NumberOfUnits": "Count",
    "UnitType": "Unit",
    "DatePlanted": "Planted",
    "PlantingLocation": "Planted At",
    "DestinationLocation": "Destined For",
    "PlantingComments": "Comments",
    "SeasonalNote": "Seasonal Note",
    "LocationID": "Location",
}


# ================================================================
# DATA LOADING — single read, derived structures cached in session_state
# ================================================================

_raw_cache = (
    api.planting_view_cache if api.planting_view_cache is not None else pd.DataFrame()
)

if _raw_cache.empty:
    st.markdown("# 🌱 Plantings Tracker")
    st.info("No planting data available. Check your database connection.")
    if st.button("← Back to Home"):
        st.switch_page("edgewater.py")
    st.stop()

plant_df = _raw_cache


def _build_sorted(df: pd.DataFrame) -> pd.DataFrame:
    """Sort plantings by date descending. Cached in session_state."""
    if "DatePlanted" in df.columns:
        return df.sort_values("DatePlanted", ascending=False)
    return df


def _build_plant_index(df: pd.DataFrame) -> dict:
    """Pre-build {PlantingID: Series} for O(1) per-record lookups."""
    return {row["PlantingID"]: row for _, row in df.iterrows()}


if "_plant_sorted" not in st.session_state:
    st.session_state["_plant_sorted"] = _build_sorted(plant_df)
sorted_plant = st.session_state["_plant_sorted"]

if "_plant_by_id" not in st.session_state:
    st.session_state["_plant_by_id"] = _build_plant_index(plant_df)
plant_by_id = st.session_state["_plant_by_id"]


# ================================================================
# FK decode maps for dropdown columns
# These use Tier-1 cached lookups (no DB hit on rerun)
# ================================================================

_loc_df = api.location_cache if api.location_cache is not None else pd.DataFrame()

# ID -> display name (for rendering)
_LOC_ID_TO_NAME = (
    dict(zip(_loc_df["LocationID"], _loc_df["Location"])) if not _loc_df.empty else {}
)

# Display name -> ID (for saving edits back to DB)
_LOC_NAME_TO_ID = {v: k for k, v in _LOC_ID_TO_NAME.items()}

# Options for SelectboxColumn (display names, with empty option)
_LOC_DISPLAY_OPTIONS = [""] + sorted(_LOC_ID_TO_NAME.values())


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

    search_term = st.text_input(
        "Search plantings",
        value=st.session_state.filter_search,
        placeholder="Search by item, variety, color...",
        key="search_input",
    )
    if search_term != st.session_state.filter_search:
        st.session_state.filter_search = search_term
        st.rerun()

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

    location_options = _loc_df["Location"].tolist() if not _loc_df.empty else []
    selected_locations = st.multiselect(
        "Planted Location",
        options=location_options,
        default=st.session_state.filter_locations,
        key="location_filter",
    )
    if selected_locations != st.session_state.filter_locations:
        st.session_state.filter_locations = selected_locations
        st.rerun()

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

    total_plantings = len(plant_df)
    unique_items = plant_df["ItemID"].nunique() if "ItemID" in plant_df.columns else 0
    locations_used = (
        plant_df["PlantingLocation"].dropna().nunique()
        if "PlantingLocation" in plant_df.columns
        else 0
    )

    st.metric("Total Plantings", total_plantings)
    st.metric("Unique Items", unique_items)
    st.metric("Locations Used", locations_used)


# ===== MAIN HEADER =====
st.markdown("# 🌱 Plantings Tracker")
st.markdown("---")

# ===== TABS =====
tab_cards, tab_table, tab_create = st.tabs(
    ["📋 Planting Cards", "📊 Table View", "➕ Add Planting"]
)

# ===== APPLY FILTERS =====
filtered_df = sorted_plant

if st.session_state.filter_search:
    search_lower = st.session_state.filter_search.lower()
    mask = (
        filtered_df["Item"].str.lower().str.contains(search_lower, na=False)
        | filtered_df["Variety"].str.lower().str.contains(search_lower, na=False)
        | filtered_df["Color"].str.lower().str.contains(search_lower, na=False)
    )
    filtered_df = filtered_df[mask]

if st.session_state.filter_types:
    filtered_df = filtered_df[filtered_df["Type"].isin(st.session_state.filter_types)]

if st.session_state.filter_locations and "PlantingLocation" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["PlantingLocation"].isin(st.session_state.filter_locations)
    ]

if date_start:
    filtered_df = filtered_df[filtered_df["DatePlanted"] >= pd.to_datetime(date_start)]
if date_end:
    filtered_df = filtered_df[filtered_df["DatePlanted"] <= pd.to_datetime(date_end)]

total_filtered = len(filtered_df)
filtered_df = filtered_df.head(st.session_state.results_limit)


# ==================== TAB 1: PLANTING CARDS ====================
# Uses st.expander — expanding/collapsing does NOT trigger st.rerun().

with tab_cards:
    if total_filtered > st.session_state.results_limit:
        st.markdown(
            f"### Showing {len(filtered_df)} of {total_filtered} matching records ({total_plantings} total)"
        )
    else:
        st.markdown(f"### Showing {len(filtered_df)} of {total_plantings} plantings")

    for idx, row in filtered_df.iterrows():
        item_display = row["Item"] if pd.notna(row.get("Item")) else "Unknown"
        if pd.notna(row.get("Variety")):
            item_display += f" - {row['Variety']}"
        if pd.notna(row.get("Color")):
            item_display += f" ({row['Color']})"

        unit_label = row["UnitType"] if pd.notna(row.get("UnitType")) else ""
        count_str = f"{row['NumberOfUnits']} {unit_label}"
        loc_name = (
            row["PlantingLocation"]
            if "PlantingLocation" in row.index and pd.notna(row.get("PlantingLocation"))
            else "Unassigned"
        )
        dest_name = (
            row["DestinationLocation"]
            if "DestinationLocation" in row.index
            and pd.notna(row.get("DestinationLocation"))
            else ""
        )
        date_str = format_date(row.get("DatePlanted"))
        greenhouse_icon = "🏠" if row.get("Greenhouse") else "🌿"
        has_notes = "📝" if pd.notna(row.get("SeasonalNote")) else ""

        expander_label = (
            f"{greenhouse_icon}  **{item_display}** — {count_str} — "
            f"📍 {loc_name} — {date_str} {has_notes}"
        )

        with st.expander(expander_label, expanded=False):
            # ---- Read-only summary ----
            meta1, meta2, meta3 = st.columns(3)

            with meta1:
                st.markdown("**Item Details**")
                st.markdown(f"- **Item ID:** {row['ItemID']}")
                st.markdown(f"- **Planting ID:** {row['PlantingID']}")
                st.markdown(
                    f"- **Type:** {row['Type'] if pd.notna(row.get('Type')) else 'N/A'}"
                )
                st.markdown(
                    f"- **Sun Conditions:** {row['SunConditions'] if pd.notna(row.get('SunConditions')) else 'Not specified'}"
                )
                st.markdown(
                    f"- **Should Stock:** {'Yes' if row.get('ShouldStock') else 'No'}"
                )
                st.markdown(f"- **Inactive:** {'Yes' if row.get('Inactive') else 'No'}")

            with meta2:
                st.markdown("**Location & Destination**")
                st.markdown(f"- **Planted at:** {loc_name}")
                st.markdown(f"- **Destined for:** {dest_name or 'Not set'}")
                st.markdown(
                    f"- **Units Destined:** {row['UnitsDestined'] if pd.notna(row.get('UnitsDestined')) else 'N/A'}"
                )
                st.markdown(
                    f"- **Purpose:** {row['PurposeComments'] if pd.notna(row.get('PurposeComments')) else 'None'}"
                )
                st.markdown(
                    f"- **Unit:** {row.get('UnitType', '')} - {row.get('UnitSize', '')}"
                )
                st.markdown(
                    f"- **Unit Category:** {row['UnitCategory'] if pd.notna(row.get('UnitCategory')) else 'N/A'}"
                )

            with meta3:
                st.markdown("**Seasonal Notes**")
                if pd.notna(row.get("SeasonalNote")):
                    greenhouse_text = (
                        "🏠 Greenhouse" if row.get("Greenhouse") else "🌿 Outdoor"
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

            # ---- Inline edit form (always visible inside expander) ----
            st.markdown("---")
            st.markdown("#### ✏️ Quick Edit")

            plant_id = int(row["PlantingID"])

            with st.form(f"edit_form_{plant_id}"):
                edit_col1, edit_col2, edit_col3 = st.columns(3)

                with edit_col1:
                    edit_count = st.number_input(
                        "Number of Units",
                        value=safe_float(row.get("NumberOfUnits")),
                        step=1.0,
                        key=f"edit_count_{plant_id}",
                    )
                    edit_date = st.date_input(
                        "Date Planted",
                        value=(
                            pd.to_datetime(row["DatePlanted"]).date()
                            if pd.notna(row.get("DatePlanted"))
                            else datetime.now().date()
                        ),
                        key=f"edit_date_{plant_id}",
                    )

                with edit_col2:
                    # Location dropdown using FK decode map
                    current_loc_name = (
                        _LOC_ID_TO_NAME.get(row.get("PlantingLocationID"), "")
                        if pd.notna(row.get("PlantingLocationID"))
                        else ""
                    )

                    edit_loc_label = st.selectbox(
                        "Location",
                        options=_LOC_DISPLAY_OPTIONS,
                        index=(
                            _LOC_DISPLAY_OPTIONS.index(current_loc_name)
                            if current_loc_name in _LOC_DISPLAY_OPTIONS
                            else 0
                        ),
                        key=f"edit_loc_{plant_id}",
                    )

                with edit_col3:
                    edit_comments = st.text_area(
                        "Comments",
                        value=(
                            row["PlantingComments"]
                            if pd.notna(row.get("PlantingComments"))
                            else ""
                        ),
                        key=f"edit_comments_{plant_id}",
                    )

                form_col1, form_col2 = st.columns([1, 4])

                with form_col1:
                    save_btn = st.form_submit_button(
                        "💾 Save", type="primary", use_container_width=True
                    )

                if save_btn:
                    edit_location_id = (
                        _LOC_NAME_TO_ID.get(edit_loc_label) if edit_loc_label else None
                    )

                    updates = {
                        "NumberOfUnits": str(edit_count),
                        "DatePlanted": datetime.combine(edit_date, datetime.min.time()),
                        "PlantingComments": edit_comments or None,
                        "LocationID": edit_location_id,
                    }

                    try:
                        api.generic_update(
                            model_class=Planting,
                            id_column="PlantingID",
                            id_value=plant_id,
                            updates=updates,
                            allowed_fields=_EDITABLE_PLANTING_COLS,
                        )
                        st.success("✅ Updated successfully!")
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Update failed: {e}")

            # ---- Delete (inside expander via popover — no rerun for confirm) ----
            with st.popover("🗑️ Delete Record"):
                st.warning(f"Are you sure you want to delete planting #{plant_id}?")
                if st.button(
                    "Yes, Delete",
                    key=f"confirm_delete_{plant_id}",
                    type="primary",
                ):
                    try:
                        api._delete(Planting, "PlantingID", plant_id)
                        st.success("Deleted!")
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting: {e}")


# ==================== TAB 2: TABLE VIEW ====================
with tab_table:
    st.markdown("### 📊 All Plantings (Table)")

    if filtered_df.empty:
        st.info("No records match current filters.")
    else:
        available_cols = [c for c in _TABLE_DISPLAY_COLS if c in filtered_df.columns]
        display_df = filtered_df[available_cols].copy()

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=_COLUMN_CONFIG,
        )


# ==================== TAB 3: ADD PLANTING ====================
with tab_create:
    st.markdown("### ➕ Add New Planting")

    # Lookup data for dropdowns (Tier-1 cached, no DB hit on rerun)
    items_df = api.item_cache
    units_df = api.unit_cache

    if items_df is None or items_df.empty or units_df is None or units_df.empty:
        st.warning("⚠️ Item or Unit data not loaded. Please refresh data.")
    else:
        with st.form("add_planting_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                # Item selection — build label->ID map
                item_map = {}
                for _, r in items_df.iterrows():
                    name = r.get("Item")
                    if pd.isna(name) or not name:
                        continue
                    label = str(name)
                    if pd.notna(r.get("Variety")) and r["Variety"]:
                        label += f" - {r['Variety']}"
                    if pd.notna(r.get("Color")) and r["Color"]:
                        label += f" ({r['Color']})"
                    item_map[label] = r["ItemID"]

                selected_item_label = st.selectbox(
                    "Select Item *",
                    options=[""] + sorted(item_map.keys()),
                    key="form_item",
                )

                # Unit selection — build label->ID map
                unit_map = {}
                for _, r in units_df.iterrows():
                    label = str(r["UnitType"])
                    if pd.notna(r.get("UnitSize")) and r["UnitSize"]:
                        label += f" - {r['UnitSize']}"
                    unit_map[label] = r["UnitID"]

                selected_unit_label = st.selectbox(
                    "Select Unit *",
                    options=[""] + sorted(unit_map.keys()),
                    key="form_unit",
                )

                number_of_units = st.number_input(
                    "Number of Units *", min_value=0.0, step=1.0, key="form_count"
                )

            with col2:
                date_planted = st.date_input(
                    "Date Planted", value=datetime.now().date(), key="form_date"
                )

                selected_loc_label = st.selectbox(
                    "Location",
                    options=_LOC_DISPLAY_OPTIONS,
                    key="form_location",
                )

                comments = st.text_area(
                    "Planting Comments", key="form_comments", height=100
                )

            submitted = st.form_submit_button(
                "💾 Add Planting", type="primary", use_container_width=True
            )

            if submitted:
                errors = []
                if not selected_item_label:
                    errors.append("Item is required.")
                if not selected_unit_label:
                    errors.append("Unit is required.")
                if not number_of_units:
                    errors.append("Number of units is required.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    selected_item_id = item_map[selected_item_label]
                    selected_unit_id = unit_map[selected_unit_label]
                    selected_location_id = (
                        _LOC_NAME_TO_ID.get(selected_loc_label)
                        if selected_loc_label
                        else None
                    )

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
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding planting: {e}")


# ===== FOOTER =====
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if total_filtered > st.session_state.results_limit:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Displaying {len(filtered_df)} of {total_filtered} matching records"
        )
    else:
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Displaying {len(filtered_df)} records"
        )

with col2:
    st.caption("Edgewater Farm Inventory System")
