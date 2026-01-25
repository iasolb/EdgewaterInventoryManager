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
from models import Location as LOC
from payloads import LocationPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Locations Administration",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("location_cache", api.get_location_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the location cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("location_cache", api.get_location_full)
    st.success("✅ Data refreshed!")


def create_location_from_form(form_data: dict) -> Optional[dict]:
    """Create a new location"""
    try:
        result = api.table_add_location(Location=str(form_data["Location"]))
        return result
    except Exception as e:
        st.error(f"❌ Error creating location: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_location(location_id: int, updates: dict) -> bool:
    """Update a location"""
    try:
        allowed_fields = {"Location"}

        result = api.generic_update(
            model_class=LOC,
            id_column="LocationID",
            id_value=location_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Location {location_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating location {location_id}: {e}")
        logger.error(f"Update failed for Location {location_id}: {e}")
        return False


def delete_location(location_id: int) -> bool:
    """Delete a location"""
    try:
        return api._delete(LOC, "LocationID", location_id)
    except Exception as e:
        st.error(f"❌ Error deleting location {location_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📍 Locations Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Location", expanded=st.session_state.show_add_form):
    st.write("### Create New Location")

    with st.form("add_location_form", clear_on_submit=True):
        form_location = st.text_input("Location Name *", key="form_location")

        submitted = st.form_submit_button(
            "💾 Create Location", type="primary", use_container_width=True
        )

        if submitted:
            if not form_location:
                st.error("❌ Location name is required!")
            else:
                form_data = {"Location": form_location}

                result = create_location_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Location '{form_location}' created! (ID: {result['LocationID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Locations",
    placeholder="Search by location name...",
    key="search_term",
)

# Apply filters
filtered_df = api.location_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["Location"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Locations ({len(filtered_df)} records)")

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
            file_name=f"locations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "LocationID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Location": st.column_config.TextColumn(
        "Location Name", width="large", required=True
    ),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="locations_editor",
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
                    location_id = edited_df.loc[idx, "LocationID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "LocationID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_location(location_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} locations")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} locations")

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

    st.write("**Delete Locations**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Location IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_location(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} locations")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total locations: {len(api.location_cache)}"
)
