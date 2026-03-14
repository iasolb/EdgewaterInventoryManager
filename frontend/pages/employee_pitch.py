"""
Employee Pitch Page - Edgewater Inventory Management System
Mobile-first pitch entry for field workers
Big buttons, fast search, quick data entry
Author: Ian Solberg
Date: 10-16-2025
Updated: 3-14-2026 - Grouped location picker, auth gate
"""

# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))
sys.path.insert(0, str(Path(__file__).parent))

from rest.api import EdgewaterAPI
from rest.authenticate import Authenticate, ROLE_EMPLOYEE
from models import Pitch

# ===== STREAMLIT CONFIG =====
st.set_page_config(
    page_title="Pitch Items",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from edgewater_theme import apply_theme

apply_theme()
# ===== AUTH GATE =====
auth = Authenticate()
auth.require_role(ROLE_EMPLOYEE)

# ===== INITIALIZE API =====
api = EdgewaterAPI()

# Hide default nav + mobile-first styling
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }

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

        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
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

        .pitch-reason-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .reason-dead { background: #ffebee; color: #c62828; }
        .reason-damaged { background: #fff3e0; color: #e65100; }
        .reason-expired { background: #fce4ec; color: #880e4f; }
        .reason-quality { background: #e8eaf6; color: #283593; }
        .reason-other { background: #f5f5f5; color: #424242; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== SESSION STATE =====
if "pitch_success" not in st.session_state:
    st.session_state.pitch_success = None


def refresh_data():
    with st.spinner("Refreshing..."):
        api.refresh_view_cache("pitch")
        api.clear_lookup_caches()


# Common pitch reasons
PITCH_REASONS = [
    "Dead",
    "Damaged",
    "Diseased",
    "Poor Quality",
    "Overgrown",
    "Expired",
    "Unsellable",
    "Pest Damage",
    "Weather Damage",
    "Other",
]


def get_reason_class(reason):
    if not reason or pd.isna(reason):
        return "reason-other"
    r = str(reason).lower()
    if "dead" in r:
        return "reason-dead"
    if "damage" in r:
        return "reason-damaged"
    if "expir" in r:
        return "reason-expired"
    if "quality" in r or "unsell" in r:
        return "reason-quality"
    return "reason-other"


# ===== HEADER =====
h1, h2, h3 = st.columns([1, 2, 1])

with h1:
    if st.button("← Back", use_container_width=True):
        st.switch_page("edgewater.py")

with h2:
    st.markdown("## 🗑️ Pitch Items")

with h3:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()

# Show success message
if st.session_state.pitch_success:
    st.success(st.session_state.pitch_success)
    st.session_state.pitch_success = None

st.markdown("---")

# ===== REASON QUICK-SELECT =====
st.markdown("### ❓ Why are you pitching?")

if "selected_reason" not in st.session_state:
    st.session_state.selected_reason = PITCH_REASONS[0]

# Show reasons in rows of 5
reason_row1 = st.columns(5)
reason_row2 = st.columns(5)

for i, reason in enumerate(PITCH_REASONS):
    col = reason_row1[i] if i < 5 else reason_row2[i - 5]
    with col:
        is_selected = st.session_state.selected_reason == reason
        btn_type = "primary" if is_selected else "secondary"
        label = f"✅ {reason}" if is_selected else reason
        if st.button(
            label,
            use_container_width=True,
            type=btn_type,
            key=f"reason_{reason}",
        ):
            st.session_state.selected_reason = reason
            st.rerun()

st.caption(f"Selected: **{st.session_state.selected_reason}**")

st.markdown("---")

# ===== MAIN: PITCH FORM + TODAY'S LOG =====
form_col, log_col = st.columns([3, 2])

# ==================== LEFT: PITCH FORM ====================
with form_col:
    st.markdown("### 🗑️ What are you pitching?")

    # Item search
    search_term = st.text_input(
        "Search items",
        placeholder="Type item name, variety, or color...",
        key="pitch_search",
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
                key="pitch_item_select",
            )

            if selected_label:
                idx = match_options.index(selected_label)
                selected_item_id = match_ids[idx]
                selected_item = items_df[items_df["ItemID"] == selected_item_id].iloc[0]

                info1, info2 = st.columns(2)
                with info1:
                    st.caption(f"ID: {selected_item_id}")
                    if pd.notna(selected_item.get("SunConditions")):
                        st.caption(f"☀️ {selected_item['SunConditions']}")
                with info2:
                    if selected_item.get("ShouldStock"):
                        st.caption("✅ Should Stock")
                    if selected_item.get("Inactive"):
                        st.caption("⚠️ Inactive item")
    elif not search_term:
        st.caption("Start typing to find an item...")

    # Pitch form
    if selected_item is not None:
        st.markdown("---")

        with st.form("pitch_form", clear_on_submit=True):
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
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
                        key="pitch_unit",
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
                    key="pitch_qty",
                )

            comments = st.text_area(
                "Notes (optional)",
                placeholder="Additional details about condition...",
                height=80,
                key="pitch_comments",
            )

            submitted = st.form_submit_button(
                "🗑️ Pitch Item",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if selected_unit_id and number_of_units > 0:
                    try:
                        api.table_add_pitch(
                            ItemID=int(selected_item["ItemID"]),
                            UnitID=selected_unit_id,
                            NumberOfUnits=str(int(number_of_units)),
                            DatePitched=datetime.now(),
                            PitchComments=comments if comments else None,
                            PitchReason=st.session_state.selected_reason,
                        )
                        display_name = str(selected_item["Item"])
                        if pd.notna(selected_item.get("Variety")):
                            display_name += f" - {selected_item['Variety']}"
                        st.session_state.pitch_success = (
                            f"✅ Pitched {int(number_of_units)}× {display_name} "
                            f"— {st.session_state.selected_reason}"
                        )
                        refresh_data()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Fill in unit and quantity")


# ==================== RIGHT: TODAY'S LOG ====================
with log_col:
    st.markdown("### 📋 Today's Pitches")

    pitch_df = api.pitch_view_cache

    if pitch_df is not None and not pitch_df.empty:
        if "DatePitched" in pitch_df.columns:
            pitch_df = pitch_df.sort_values("DatePitched", ascending=False)

        today = pd.Timestamp.now().normalize()
        today_pitches = pitch_df[
            pd.to_datetime(pitch_df["DatePitched"], errors="coerce") >= today
        ].copy()

        if not today_pitches.empty:
            stat1, stat2 = st.columns(2)
            with stat1:
                st.markdown(
                    f'<div class="big-metric">{len(today_pitches)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="sub-metric">pitches today</div>',
                    unsafe_allow_html=True,
                )
            with stat2:
                unique_today = (
                    today_pitches["ItemID"].nunique()
                    if "ItemID" in today_pitches.columns
                    else 0
                )
                st.markdown(
                    f'<div class="big-metric">{unique_today}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="sub-metric">unique items</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            for _, row in today_pitches.head(20).iterrows():
                item_name = row["Item"] if pd.notna(row.get("Item")) else "Unknown"
                variety = f" - {row['Variety']}" if pd.notna(row.get("Variety")) else ""
                qty = row.get("NumberOfUnits", "?")
                unit = row.get("UnitType", "")
                reason = row.get("PitchReason", "")
                reason_class = get_reason_class(reason)

                r1, r2 = st.columns([3, 1])
                with r1:
                    st.markdown(f"**{item_name}{variety}** — {qty} {unit}")
                with r2:
                    if reason:
                        st.markdown(
                            f'<span class="pitch-reason-badge {reason_class}">{reason}</span>',
                            unsafe_allow_html=True,
                        )

                if pd.notna(row.get("PitchComments")):
                    st.caption(f"  💬 {row['PitchComments']}")

        else:
            st.caption("No pitches logged today yet.")

        st.markdown("---")
        week_ago = today - pd.Timedelta(days=7)
        week_pitches = pitch_df[
            pd.to_datetime(pitch_df["DatePitched"], errors="coerce") >= week_ago
        ]
        if not week_pitches.empty:
            st.caption(
                f"**This week:** {len(week_pitches)} pitches, "
                f"{week_pitches['ItemID'].nunique()} unique items"
            )
    else:
        st.caption("No pitch data available.")


# ===== FOOTER =====
st.markdown("---")
st.caption(
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Edgewater Farm Inventory System"
)
