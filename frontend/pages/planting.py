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
from models import Planting as PLN
from payloads import PlantingPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Plantings Administration",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("planting_cache", api.get_planting_full)
api.reset_cache("item_cache", api.get_item_full)
api.reset_cache("unit_cache", api.get_unit_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh caches after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("planting_cache", api.get_planting_full)
        api.reset_cache("item_cache", api.get_item_full)
        api.reset_cache("unit_cache", api.get_unit_full)
    st.success("✅ Data refreshed!")


def create_planting_from_form(form_data: dict) -> Optional[dict]:
    """Create a new planting record"""
    try:
        result = api.table_add_planting(
            ItemID=int(form_data["ItemID"]),
            UnitID=int(form_data["UnitID"]),
            NumberOfUnits=str(form_data["NumberOfUnits"]),
            DatePlanted=form_data.get("DatePlanted") or datetime.now(),
            PlantingComments=form_data.get("PlantingComments"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating planting: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_planting(planting_id: int, updates: dict) -> bool:
    """Update a planting record"""
    try:
        allowed_fields = {
            "ItemID",
            "UnitID",
            "NumberOfUnits",
            "DatePlanted",
            "PlantingComments",
        }

        result = api.generic_update(
            model_class=PLN,
            id_column="PlantingID",
            id_value=planting_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Planting {planting_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating planting {planting_id}: {e}")
        logger.error(f"Update failed for Planting {planting_id}: {e}")
        return False


def delete_planting(planting_id: int) -> bool:
    """Delete a planting record"""
    try:
        return api._delete(PLN, "PlantingID", planting_id)
    except Exception as e:
        st.error(f"❌ Error deleting planting {planting_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🌱 Plantings Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Planting Record", expanded=st.session_state.show_add_form):
    st.write("### Create New Planting Record")

    # Prepare lookup dictionaries
    items_dict = api.item_cache.set_index("ItemID")["Item"].to_dict()
    units_dict = api.unit_cache.apply(
        lambda x: f"{x['UnitSize']} {x['UnitType']}", axis=1
    ).to_dict()

    with st.form("add_planting_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            form_item_id = st.selectbox(
                "Item *",
                options=list(items_dict.keys()),
                format_func=lambda x: items_dict[x],
                key="form_item_id",
            )
            form_unit_id = st.selectbox(
                "Unit *",
                options=list(units_dict.keys()),
                format_func=lambda x: units_dict[x],
                key="form_unit_id",
            )
            form_number = st.number_input(
                "Number of Units *", min_value=0.0, step=0.5, key="form_number"
            )

        with col2:
            form_date = st.date_input(
                "Date Planted", value=datetime.now(), key="form_date"
            )
            form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Record", type="primary", use_container_width=True
        )

        if submitted:
            if form_number <= 0:
                st.error("❌ Number of units must be greater than 0!")
            else:
                form_data = {
                    "ItemID": form_item_id,
                    "UnitID": form_unit_id,
                    "NumberOfUnits": form_number,
                    "DatePlanted": datetime.combine(form_date, datetime.min.time()),
                    "PlantingComments": form_comments or None,
                }

                result = create_planting_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Planting record created! (ID: {result['PlantingID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    date_filter_start = st.date_input("From Date", value=None, key="date_start")

with filter_col2:
    date_filter_end = st.date_input("To Date", value=None, key="date_end")

with filter_col3:
    item_filter = st.multiselect(
        "Filter by Item",
        options=api.item_cache["Item"].unique().tolist(),
        key="item_filter",
    )

# Apply filters
filtered_df = api.planting_cache.copy()

# Date filters
if date_filter_start:
    filtered_df = filtered_df[
        filtered_df["DatePlanted"] >= pd.to_datetime(date_filter_start)
    ]
if date_filter_end:
    filtered_df = filtered_df[
        filtered_df["DatePlanted"] <= pd.to_datetime(date_filter_end)
    ]

# Item filter
if item_filter:
    item_ids = api.item_cache[api.item_cache["Item"].isin(item_filter)][
        "ItemID"
    ].tolist()
    filtered_df = filtered_df[filtered_df["ItemID"].isin(item_ids)]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Planting Records ({len(filtered_df)} records)")

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
            file_name=f"plantings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "PlantingID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "DatePlanted": st.column_config.DatetimeColumn("Date Planted", width="medium"),
    "ItemID": st.column_config.NumberColumn("Item ID", width="small"),
    "UnitID": st.column_config.NumberColumn("Unit ID", width="small"),
    "NumberOfUnits": st.column_config.TextColumn("Number of Units", width="medium"),
    "PlantingComments": st.column_config.TextColumn("Comments", width="large"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="plantings_editor",
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
                    planting_id = edited_df.loc[idx, "PlantingID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "PlantingID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_planting(planting_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} records")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} records")

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

    st.write("**Delete Planting Records**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Planting IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_planting(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} records")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total planting records: {len(api.planting_cache)}"
)
