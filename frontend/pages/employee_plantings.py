"""
Employee Plantings - Edgewater Inventory Management System
Mobile-first planting entry for field workers
Big buttons, fast search, quick data entry
Author: Ian Solberg
Date: 3-3-2026
"""

# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from rest.api import EdgewaterAPI
from models import Planting

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Log Planting",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===== INITIALIZE API =====
api = EdgewaterAPI()

# Hide default nav + mobile-first styling
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }

        /* Bigger touch targets for mobile */
        .stButton > button {
            min-height: 3.2rem;
            font-size: 1.1rem;
        }

        .stSelectbox > div > div,
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            font-size: 1.1rem;
            min-height: 2.8rem;
        }

        /* Tighten up padding on mobile */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .location-btn-active {
            background: #4CAF50 !important;
            color: white !important;
            border: 2px solid #2e7d32 !important;
        }

        .big-metric {
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
        }

        .sub-metric {
            font-size: 0.9rem;
            text-align: center;
            opacity: 0.7;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SESSION STATE =====
if "planting_success" not in st.session_state:
    st.session_state.planting_success = None
if "selected_location_id" not in st.session_state:
    st.session_state.selected_location_id = None

# ===== CACHE DATA =====
# Lookup tables auto-cached via @st.cache_data
# View data loaded lazily into session_state


def refresh_data():
    with st.spinner("Refreshing..."):
        api.refresh_view_cache("plantings")
        api.clear_lookup_caches()


# ===== HEADER =====
h1, h2, h3 = st.columns([1, 2, 1])

with h1:
    if st.button("← Back", use_container_width=True):
        st.switch_page("edgewater.py")

with h2:
    st.markdown("## 🌱 Log Planting")

with h3:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()

# Show success message
if st.session_state.planting_success:
    st.success(st.session_state.planting_success)
    st.session_state.planting_success = None

st.markdown("---")

# ===== LOCATION QUICK-SELECT =====
# Big buttons for location — tap once, stays selected
st.markdown("### 📍 Where are you planting?")

loc_df = api.location_cache
if loc_df is not None and not loc_df.empty:
    # Filter out Pitch Pile — not a planting location
    planting_locs = loc_df[loc_df["Location"].str.lower() != "pitch pile"].copy()
    loc_cols = st.columns(len(planting_locs) + 1)

    # "No Location" option
    with loc_cols[0]:
        is_selected = st.session_state.selected_location_id is None
        btn_type = "primary" if is_selected else "secondary"
        if st.button(
            "📍 No Location" if not is_selected else "✅ No Location",
            use_container_width=True,
            type=btn_type,
            key="loc_none",
        ):
            st.session_state.selected_location_id = None
            st.rerun()

    for i, (_, loc_row) in enumerate(planting_locs.iterrows()):
        with loc_cols[i + 1]:
            loc_id = int(loc_row["LocationID"])
            loc_name = loc_row["Location"]
            is_selected = st.session_state.selected_location_id == loc_id
            btn_type = "primary" if is_selected else "secondary"
            if st.button(
                f"📍 {loc_name}" if not is_selected else f"✅ {loc_name}",
                use_container_width=True,
                type=btn_type,
                key=f"loc_{loc_id}",
            ):
                st.session_state.selected_location_id = loc_id
                st.rerun()

    # Show current selection
    if st.session_state.selected_location_id is not None:
        sel_loc = loc_df[loc_df["LocationID"] == st.session_state.selected_location_id]
        if not sel_loc.empty:
            st.caption(f"Selected: **{sel_loc.iloc[0]['Location']}**")
    else:
        st.caption("Selected: **No location**")
else:
    st.caption("No locations configured.")

st.markdown("---")

# ===== MAIN: PLANTING FORM + TODAY'S LOG =====
form_col, log_col = st.columns([3, 2])

# ==================== LEFT: PLANTING FORM ====================
with form_col:
    st.markdown("### 🌱 What are you planting?")

    # Item search
    search_term = st.text_input(
        "Search items",
        placeholder="Type item name, variety, or color...",
        key="plant_search",
        label_visibility="collapsed",
    )

    items_df = api.item_cache
    selected_item = None

    if search_term and items_df is not None and not items_df.empty:
        search_lower = search_term.lower()
        mask = (
            items_df["Item"].str.lower().str.contains(search_lower, na=False)
            | items_df["Variety"].str.lower().str.contains(search_lower, na=False)
            | items_df["Color"].str.lower().str.contains(search_lower, na=False)
        )
        matches = items_df[mask].head(20)

        if matches.empty:
            st.caption("No items found.")
        else:
            match_options = []
            match_ids = []
            for _, row in matches.iterrows():
                display = str(row["Item"]) if pd.notna(row["Item"]) else "Unknown"
                if pd.notna(row.get("Variety")):
                    display += f" - {row['Variety']}"
                if pd.notna(row.get("Color")):
                    display += f" ({row['Color']})"
                match_options.append(display)
                match_ids.append(int(row["ItemID"]))

            selected_label = st.selectbox(
                "Select item",
                options=match_options,
                key="plant_item_select",
            )

            if selected_label:
                idx = match_options.index(selected_label)
                selected_item_id = match_ids[idx]
                selected_item = items_df[items_df["ItemID"] == selected_item_id].iloc[0]

                # Quick item info
                info1, info2 = st.columns(2)
                with info1:
                    st.caption(f"ID: {selected_item_id}")
                    if pd.notna(selected_item.get("SunConditions")):
                        st.caption(f"☀️ {selected_item['SunConditions']}")
                with info2:
                    if selected_item.get("Inactive"):
                        st.caption("⚠️ Inactive item")
    elif not search_term:
        st.caption("Start typing to find an item...")

    # Planting form
    if selected_item is not None:
        st.markdown("---")

        with st.form("planting_form", clear_on_submit=True):
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                # Unit selection
                units_df = api.unit_cache
                if units_df is not None and not units_df.empty:
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
                        "Unit *",
                        options=unit_options,
                        key="plant_unit",
                    )
                    selected_unit_id = unit_ids[unit_options.index(selected_unit_label)]
                else:
                    st.warning("No units loaded")
                    selected_unit_id = None

            with row1_col2:
                number_of_units = st.number_input(
                    "How many? *",
                    min_value=1.0,
                    step=1.0,
                    key="plant_qty",
                )

            comments = st.text_area(
                "Notes (optional)",
                placeholder="Condition, location details, intent...",
                height=80,
                key="plant_comments",
            )

            submitted = st.form_submit_button(
                "🌱 Log Planting",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if selected_unit_id and number_of_units > 0:
                    try:
                        api.table_add_planting(
                            ItemID=int(selected_item["ItemID"]),
                            UnitID=selected_unit_id,
                            NumberOfUnits=str(int(number_of_units)),
                            DatePlanted=datetime.now(),
                            PlantingComments=comments if comments else None,
                            LocationID=st.session_state.selected_location_id,
                        )
                        display_name = str(selected_item["Item"])
                        if pd.notna(selected_item.get("Variety")):
                            display_name += f" - {selected_item['Variety']}"
                        loc_name = "No location"
                        if st.session_state.selected_location_id and loc_df is not None:
                            sel = loc_df[
                                loc_df["LocationID"]
                                == st.session_state.selected_location_id
                            ]
                            if not sel.empty:
                                loc_name = sel.iloc[0]["Location"]
                        st.session_state.planting_success = f"✅ Planted {int(number_of_units)}× {display_name} at {loc_name}"
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Fill in unit and quantity")


# ==================== RIGHT: TODAY'S LOG ====================
with log_col:
    st.markdown("### 📋 Today's Plantings")

    planting_df = api.planting_view_cache

    if planting_df is not None and not planting_df.empty:
        today = pd.Timestamp.now().normalize()
        today_plantings = planting_df[
            pd.to_datetime(planting_df["DatePlanted"], errors="coerce") >= today
        ].copy()

        if "DatePlanted" in today_plantings.columns:
            today_plantings = today_plantings.sort_values(
                "DatePlanted", ascending=False
            )

        if not today_plantings.empty:
            # Today stats
            stat1, stat2 = st.columns(2)
            with stat1:
                st.markdown(
                    f'<div class="big-metric">{len(today_plantings)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="sub-metric">plantings today</div>',
                    unsafe_allow_html=True,
                )
            with stat2:
                unique_today = (
                    today_plantings["ItemID"].nunique()
                    if "ItemID" in today_plantings.columns
                    else 0
                )
                st.markdown(
                    f'<div class="big-metric">{unique_today}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="sub-metric">unique items</div>', unsafe_allow_html=True
                )

            st.markdown("---")

            for _, row in today_plantings.head(20).iterrows():
                item_name = row["Item"] if pd.notna(row.get("Item")) else "Unknown"
                variety = f" - {row['Variety']}" if pd.notna(row.get("Variety")) else ""
                qty = row.get("NumberOfUnits", "?")
                unit = row.get("UnitType", "")

                loc = (
                    row["PlantingLocation"]
                    if "PlantingLocation" in row
                    and pd.notna(row.get("PlantingLocation"))
                    else ""
                )

                r1, r2 = st.columns([3, 1])
                with r1:
                    st.markdown(f"**{item_name}{variety}** — {qty} {unit}")
                with r2:
                    if loc:
                        st.caption(f"📍 {loc}")

                if pd.notna(row.get("PlantingComments")):
                    st.caption(f"  💬 {row['PlantingComments']}")

        else:
            st.caption("No plantings logged today yet.")

        # This week summary
        st.markdown("---")
        week_ago = today - pd.Timedelta(days=7)
        week_plantings = planting_df[
            pd.to_datetime(planting_df["DatePlanted"], errors="coerce") >= week_ago
        ]
        if not week_plantings.empty:
            st.caption(
                f"**This week:** {len(week_plantings)} plantings, {week_plantings['ItemID'].nunique()} unique items"
            )
    else:
        st.caption("No planting data available.")


# ===== FOOTER =====
st.markdown("---")
st.caption(
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Edgewater Farm Inventory System"
)
