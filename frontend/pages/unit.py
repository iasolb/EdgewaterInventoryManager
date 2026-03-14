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
from models import Unit as UNT

api = EdgewaterAPI()

st.set_page_config(
    page_title="Units Administration",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.clear_lookup_caches()
    st.success("✅ Data refreshed!")


def create_unit_from_form(form_data: dict) -> Optional[dict]:
    """Create a new unit"""
    try:
        result = api.table_add_unit(
            UnitType=str(form_data["UnitType"]),
            UnitSize=str(form_data["UnitSize"]),
            UnitCategoryID=int(form_data["UnitCategoryID"]),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating unit: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_unit(unit_id: int, updates: dict) -> bool:
    """Update a unit"""
    try:
        allowed_fields = {"UnitType", "UnitSize", "UnitCategoryID"}

        result = api.generic_update(
            model_class=UNT,
            id_column="UnitID",
            id_value=unit_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Unit {unit_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating unit {unit_id}: {e}")
        logger.error(f"Update failed for Unit {unit_id}: {e}")
        return False


def delete_unit(unit_id: int) -> bool:
    """Delete a unit"""
    try:
        return api._delete(UNT, "UnitID", unit_id)
    except Exception as e:
        st.error(f"❌ Error deleting unit {unit_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📐 Units Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW UNIT FORM ====================
with st.expander("➕ Add New Unit", expanded=st.session_state.show_add_form):
    st.write("### Create New Unit")

    # Prepare unit category lookup
    unit_categories_dict = {
        int(k): str(v)
        for k, v in api.unit_category_cache.set_index("UnitCategoryID")["UnitCategory"]
        .to_dict()
        .items()
    }

    with st.form("add_unit_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_unit_type = st.text_input(
                "Unit Type *", key="form_unit_type", placeholder="e.g., Flat, Pot, Tray"
            )

        with col2:
            form_unit_size = st.text_input(
                "Unit Size *",
                key="form_unit_size",
                placeholder="e.g., 4 inch, 1 gallon",
            )

        with col3:
            form_unit_category_id = st.selectbox(
                "Unit Category *",
                options=list(unit_categories_dict.keys()),
                format_func=lambda x: unit_categories_dict[x],
                key="form_unit_category_id",
            )

        submitted = st.form_submit_button(
            "💾 Create Unit", type="primary", use_container_width=True
        )

        if submitted:
            if not form_unit_type:
                st.error("❌ Unit type is required!")
            elif not form_unit_size:
                st.error("❌ Unit size is required!")
            else:
                form_data = {
                    "UnitType": form_unit_type,
                    "UnitSize": form_unit_size,
                    "UnitCategoryID": form_unit_category_id,
                }

                result = create_unit_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Unit '{form_unit_size} {form_unit_type}' created! (ID: {result['UnitID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    search_term = st.text_input(
        "Search Units",
        placeholder="Search by unit type or size...",
        key="search_term",
    )

with filter_col2:
    category_filter = st.multiselect(
        "Filter by Category",
        options=api.unit_category_cache["UnitCategory"].dropna().unique().tolist(),
        key="category_filter",
    )

# Apply filters
filtered_df = api.unit_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["UnitType"].fillna("").str.contains(
        search_term, case=False
    ) | filtered_df["UnitSize"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

# Category filter
if category_filter:
    category_ids = api.unit_category_cache[
        api.unit_category_cache["UnitCategory"].isin(category_filter)
    ]["UnitCategoryID"].tolist()
    filtered_df = filtered_df[filtered_df["UnitCategoryID"].isin(category_ids)]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Units ({len(filtered_df)} records)")

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
        csv = export_csv(filtered_df, UNT)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"units_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "UnitID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "UnitType": st.column_config.TextColumn("Unit Type", width="medium", required=True),
    "UnitSize": st.column_config.TextColumn("Unit Size", width="medium", required=True),
    "UnitCategoryID": st.column_config.NumberColumn("Category ID", width="small"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="units_editor",
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
                    unit_id = edited_df.loc[idx, "UnitID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "UnitID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_unit(unit_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} units")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} units")

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

    bulk_col1, bulk_col2 = st.columns(2)

    with bulk_col1:
        st.write("**Change Category**")
        bulk_unit_ids = st.text_input(
            "Unit IDs (comma-separated)", key="bulk_category_ids", placeholder="1,2,3"
        )
        new_category = st.selectbox(
            "New Category",
            options=list(unit_categories_dict.keys()),
            format_func=lambda x: unit_categories_dict[x],
            key="bulk_new_category",
        )
        if st.button("Update Category", key="bulk_category_btn"):
            if bulk_unit_ids:
                ids = [int(x.strip()) for x in bulk_unit_ids.split(",")]
                success = sum(
                    [update_unit(id, {"UnitCategoryID": new_category}) for id in ids]
                )
                st.success(f"✅ Updated category for {success}/{len(ids)} units")
                refresh_cache()
                st.rerun()

    with bulk_col2:
        st.write("**Delete Units**")
        st.warning("⚠️ Permanent action!")
        delete_ids = st.text_input(
            "Unit IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
        )
        confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
        if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
            if delete_ids:
                ids = [int(x.strip()) for x in delete_ids.split(",")]
                success = sum([delete_unit(id) for id in ids])
                st.success(f"✅ Deleted {success}/{len(ids)} units")
                refresh_cache()
                st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total units: {len(api.unit_cache)}"
)
