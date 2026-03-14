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
from export_utils import export_csv
from models import SeasonalNotes as SN
from payloads import SeasonalNotesPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Seasonal Notes Administration",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from edgewater_theme import apply_theme

apply_theme()

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.refresh_view_cache("seasonal_notes_table")
        api.clear_lookup_caches()
    st.success("✅ Data refreshed!")


def create_seasonal_note_from_form(form_data: dict) -> Optional[dict]:
    """Create a new seasonal note"""
    try:
        result = api.table_add_seasonal_note(
            ItemID=int(form_data["ItemID"]),
            GrowingSeasonID=int(form_data["GrowingSeasonID"]),
            Greenhouse=int(form_data["Greenhouse"]),
            Note=str(form_data["Note"]),
            LastUpdate=form_data.get("LastUpdate") or datetime.now(),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating seasonal note: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_seasonal_note(note_id: int, updates: dict) -> bool:
    """Update a seasonal note"""
    try:
        allowed_fields = {
            "ItemID",
            "GrowingSeasonID",
            "Greenhouse",
            "Note",
            "LastUpdate",
        }

        result = api.generic_update(
            model_class=SN,
            id_column="NoteID",
            id_value=note_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated SeasonalNote {note_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating seasonal note {note_id}: {e}")
        logger.error(f"Update failed for SeasonalNote {note_id}: {e}")
        return False


def delete_seasonal_note(note_id: int) -> bool:
    """Delete a seasonal note"""
    try:
        return api._delete(SN, "NoteID", note_id)
    except Exception as e:
        st.error(f"❌ Error deleting seasonal note {note_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📝 Seasonal Notes Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Seasonal Note", expanded=st.session_state.show_add_form):
    st.write("### Create New Seasonal Note")

    # Prepare lookup dictionaries
    items_dict = {
        int(k): str(v)
        for k, v in api.item_cache.set_index("ItemID")["Item"].to_dict().items()
    }

    with st.form("add_seasonal_note_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            form_item_id = st.selectbox(
                "Item *",
                options=list(items_dict.keys()),
                format_func=lambda x: items_dict[x],
                key="form_item_id",
            )
            form_growing_season = st.number_input(
                "Growing Season *",
                min_value=1900,
                max_value=2100,
                value=datetime.now().year,
                step=1,
                key="form_growing_season",
            )

        with col2:
            form_greenhouse = st.number_input(
                "Greenhouse *", min_value=0, step=1, key="form_greenhouse"
            )
            form_last_update = st.date_input(
                "Last Update", value=datetime.now(), key="form_last_update"
            )

        form_note = st.text_area("Note *", key="form_note", height=150)

        submitted = st.form_submit_button(
            "💾 Create Seasonal Note", type="primary", use_container_width=True
        )

        if submitted:
            if not form_note:
                st.error("❌ Note is required!")
            else:
                form_data = {
                    "ItemID": form_item_id,
                    "GrowingSeason": form_growing_season,
                    "Greenhouse": form_greenhouse,
                    "Note": form_note,
                    "LastUpdate": datetime.combine(
                        form_last_update, datetime.min.time()
                    ),
                }

                result = create_seasonal_note_from_form(form_data)
                if result:
                    st.success(f"✅ Seasonal note created! (ID: {result['NoteID']})")
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    item_filter = st.multiselect(
        "Filter by Item",
        options=api.item_cache["Item"].unique().tolist(),
        key="item_filter",
    )

with filter_col2:
    season_filter = st.multiselect(
        "Filter by Growing Season",
        options=sorted(
            api.seasonal_notes_cache["GrowingSeasonID"].dropna().unique().tolist()
        ),
        key="season_filter",
    )

with filter_col3:
    greenhouse_filter = st.multiselect(
        "Filter by Greenhouse",
        options=sorted(
            api.seasonal_notes_cache["Greenhouse"].dropna().unique().tolist()
        ),
        key="greenhouse_filter",
    )

# Apply filters
filtered_df = api.seasonal_notes_cache.copy()

# Item filter
if item_filter:
    item_ids = api.item_cache[api.item_cache["Item"].isin(item_filter)][
        "ItemID"
    ].tolist()
    filtered_df = filtered_df[filtered_df["ItemID"].isin(item_ids)]

# Season filter
if season_filter:
    filtered_df = filtered_df[filtered_df["GrowingSeason"].isin(season_filter)]

# Greenhouse filter
if greenhouse_filter:
    filtered_df = filtered_df[filtered_df["Greenhouse"].isin(greenhouse_filter)]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Seasonal Notes ({len(filtered_df)} records)")

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
        csv = export_csv(filtered_df, SN)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"seasonal_notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "NoteID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "ItemID": st.column_config.NumberColumn("Item ID", width="small"),
    "GrowingSeason": st.column_config.NumberColumn("Growing Season", width="small"),
    "Greenhouse": st.column_config.NumberColumn("Greenhouse", width="small"),
    "Note": st.column_config.TextColumn("Note", width="large", required=True),
    "LastUpdate": st.column_config.DatetimeColumn("Last Update", width="medium"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="seasonal_notes_editor",
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
                    note_id = edited_df.loc[idx, "NoteID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "NoteID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_seasonal_note(note_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} seasonal notes")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} seasonal notes")

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

    st.write("**Delete Seasonal Notes**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Note IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_seasonal_note(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} seasonal notes")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total seasonal notes: {len(api.seasonal_notes_cache)}"
)
