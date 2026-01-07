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
from models import GrowingSeason as GS
from payloads import GrowingSeasonPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Growing Seasons Administration",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("growing_season_cache", api.get_growing_season_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the growing season cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("growing_season_cache", api.get_growing_season_full)
    st.success("✅ Data refreshed!")


def create_growing_season_from_form(form_data: dict) -> Optional[dict]:
    """Create a new growing season"""
    try:
        result = api.table_add_growing_season(
            GrowingSeasonYear=str(form_data["GrowingSeason"]),
            StartDate=form_data["StartDate"],
            EndDate=form_data.get("EndDate"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating growing season: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_growing_season(season_id: int, updates: dict) -> bool:
    """Update a growing season"""
    try:
        allowed_fields = {"GrowingSeason", "StartDate", "EndDate"}

        result = api.generic_update(
            model_class=GS,
            id_column="GrowingSeasonID",
            id_value=season_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated GrowingSeason {season_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating growing season {season_id}: {e}")
        logger.error(f"Update failed for GrowingSeason {season_id}: {e}")
        return False


def delete_growing_season(season_id: int) -> bool:
    """Delete a growing season"""
    try:
        return api._delete(GS, "GrowingSeasonID", season_id)
    except Exception as e:
        st.error(f"❌ Error deleting growing season {season_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🌱 Growing Seasons Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Growing Season", expanded=st.session_state.show_add_form):
    st.write("### Create New Growing Season")

    with st.form("add_growing_season_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_season = st.text_input(
                "Season Name *", key="form_season", placeholder="e.g., 2024"
            )

        with col2:
            form_start_date = st.date_input(
                "Start Date *", value=datetime.now(), key="form_start_date"
            )

        with col3:
            form_end_date = st.date_input("End Date", value=None, key="form_end_date")

        submitted = st.form_submit_button(
            "💾 Create Growing Season", type="primary", use_container_width=True
        )

        if submitted:
            if not form_season:
                st.error("❌ Season name is required!")
            else:
                form_data = {
                    "GrowingSeason": form_season,
                    "StartDate": datetime.combine(form_start_date, datetime.min.time()),
                    "EndDate": (
                        datetime.combine(form_end_date, datetime.min.time())
                        if form_end_date
                        else None
                    ),
                }

                result = create_growing_season_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Growing Season '{form_season}' created! (ID: {result['GrowingSeasonID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Growing Seasons",
    placeholder="Search by season name...",
    key="search_term",
)

# Apply filters
filtered_df = api.growing_season_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["GrowingSeason"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Growing Seasons ({len(filtered_df)} records)")

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
            file_name=f"growing_seasons_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "GrowingSeasonID": st.column_config.NumberColumn(
        "ID", disabled=True, width="small"
    ),
    "GrowingSeason": st.column_config.TextColumn(
        "Season Name", width="medium", required=True
    ),
    "StartDate": st.column_config.DatetimeColumn("Start Date", width="medium"),
    "EndDate": st.column_config.DatetimeColumn("End Date", width="medium"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="growing_seasons_editor",
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
                    season_id = edited_df.loc[idx, "GrowingSeasonID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "GrowingSeasonID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_growing_season(season_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} growing seasons")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} growing seasons")

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

    st.write("**Delete Growing Seasons**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Season IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_growing_season(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} growing seasons")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total growing seasons: {len(api.growing_season_cache)}"
)
