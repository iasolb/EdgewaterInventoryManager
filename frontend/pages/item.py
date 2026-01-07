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
from models import Item as IM
from payloads import ItemPayload

api = EdgewaterAPI()


st.set_page_config(
    page_title="Items Table Administration",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("item_cache", api.get_item_full)
api.reset_cache("item_type_cache", api.get_item_type_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the item cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("item_cache", api.get_item_full)
        api.reset_cache("item_type_cache", api.get_item_type_full)
    st.success("✅ Data refreshed!")


def verify_db_write(item_id: int, field: str, expected_value) -> bool:
    """Verify a database write by querying directly"""
    try:
        # Query fresh from DB (bypass cache)
        from_db = api._get_by_id(IM, "ItemID", item_id)
        if from_db and from_db.get(field) == expected_value:
            logger.info(
                f"✓ Verified DB write: Item {item_id}.{field} = {expected_value}"
            )
            return True
        else:
            logger.warning(f"✗ DB verification failed: Item {item_id}.{field}")
            return False
    except Exception as e:
        logger.error(f"Error verifying DB write: {e}")
        return False


def create_item_from_form(form_data: dict) -> Optional[dict]:
    """Create a new item using the API's table_add_item method"""
    try:
        result = api.table_add_item(
            Item=str(form_data["Item"]),  # Ensure string
            TypeID=int(form_data["TypeID"]),  # Ensure int
            Variety=str(form_data.get("Variety")) if form_data.get("Variety") else None,
            Color=str(form_data.get("Color")) if form_data.get("Color") else None,
            Inactive=bool(form_data.get("Inactive", False)),
            ShouldStock=bool(form_data.get("ShouldStock", False)),
            LabelDescription=(
                str(form_data.get("LabelDescription"))
                if form_data.get("LabelDescription")
                else None
            ),
            Definition=(
                str(form_data.get("Definition"))
                if form_data.get("Definition")
                else None
            ),
            PictureLayout=(
                str(form_data.get("PictureLayout"))
                if form_data.get("PictureLayout")
                else None
            ),
            PictureLink=(
                str(form_data.get("PictureLink"))
                if form_data.get("PictureLink")
                else None
            ),
            SunConditions=(
                str(form_data.get("SunConditions"))
                if form_data.get("SunConditions")
                else None
            ),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating item: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_item(item_id: int, updates: dict) -> bool:
    """Update an item using the API's generic_update method"""
    try:
        allowed_fields = {
            "Item",
            "Variety",
            "Color",
            "Inactive",
            "ShouldStock",
            "TypeID",
            "LabelDescription",
            "Definition",
            "PictureLayout",
            "PictureLink",
            "SunConditions",
        }

        result = api.generic_update(
            model_class=IM,
            id_column="ItemID",
            id_value=item_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Item {item_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating item {item_id}: {e}")
        logger.error(f"Update failed for Item {item_id}: {e}")
        return False


def delete_item(item_id: int) -> bool:
    """Delete an item using the API's _delete method"""
    try:
        return api._delete(IM, "ItemID", item_id)
    except Exception as e:
        st.error(f"❌ Error deleting item {item_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📦 Items Table Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW ITEM FORM ====================
with st.expander("➕ Add New Item", expanded=st.session_state.show_add_form):
    st.write("### Create New Item")

    item_types = api.item_type_cache.set_index("TypeID")["Type"].to_dict()

    with st.form("add_item_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            form_item = st.text_input("Item Name *", key="form_item")
            form_variety = st.text_input("Variety", key="form_variety")
            form_color = st.text_input("Color", key="form_color")
            form_inactive = st.checkbox("Inactive", key="form_inactive")

        with col2:
            form_type_id = st.selectbox(
                "Type *",
                options=list(item_types.keys()),
                format_func=lambda x: item_types[x],
                key="form_type_id",
            )
            form_should_stock = st.checkbox("Should Stock", key="form_should_stock")
            form_sun = st.text_input("Sun Conditions", key="form_sun")

        with col3:
            form_label = st.text_area("Label Description", key="form_label", height=100)
            form_def = st.text_area("Definition", key="form_def", height=100)

        col1, col2 = st.columns(2)
        with col1:
            form_pic_layout = st.text_input("Picture Layout", key="form_pic_layout")
        with col2:
            form_pic_link = st.text_input("Picture Link", key="form_pic_link")

        submitted = st.form_submit_button(
            "💾 Create Item", type="primary", use_container_width=True
        )

        if submitted:
            if not form_item:
                st.error("❌ Item name is required!")
            else:
                form_data = {
                    "Item": form_item,
                    "TypeID": form_type_id,
                    "Variety": form_variety or None,
                    "Color": form_color or None,
                    "Inactive": form_inactive,
                    "ShouldStock": form_should_stock,
                    "LabelDescription": form_label or None,
                    "Definition": form_def or None,
                    "PictureLayout": form_pic_layout or None,
                    "PictureLink": form_pic_link or None,
                    "SunConditions": form_sun or None,
                }

                result = create_item_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Item '{form_item}' created! (ID: {result['ItemID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])

with filter_col1:
    search_term = st.text_input(
        "Search Items",
        placeholder="Search by name, variety, or color...",
        key="search_term",
    )

with filter_col2:
    type_filter = st.multiselect(
        "Filter by Type",
        options=api.item_type_cache["Type"].unique().tolist(),
        key="type_filter",
    )

with filter_col3:
    status_filter = st.selectbox(
        "Status", options=["All", "Active Only", "Inactive Only"], key="status_filter"
    )

with filter_col4:
    stock_filter = st.selectbox(
        "Stock Status",
        options=["All", "Should Stock", "Don't Stock"],
        key="stock_filter",
    )

# Apply filters
# Data is already loaded by ensure_caches_loaded()
filtered_df = api.item_cache.copy()

# Search filter
if search_term:
    mask = (
        filtered_df["Item"].fillna("").str.contains(search_term, case=False)
        | filtered_df["Variety"].fillna("").str.contains(search_term, case=False)
        | filtered_df["Color"].fillna("").str.contains(search_term, case=False)
    )
    filtered_df = filtered_df[mask]

if type_filter:
    type_ids = api.item_type_cache[api.item_type_cache["Type"].isin(type_filter)][
        "TypeID"
    ].tolist()
    filtered_df = filtered_df[filtered_df["TypeID"].isin(type_ids)]

if status_filter == "Active Only":
    filtered_df = filtered_df[filtered_df["Inactive"] == False]
elif status_filter == "Inactive Only":
    filtered_df = filtered_df[filtered_df["Inactive"] == True]

if stock_filter == "Should Stock":
    filtered_df = filtered_df[filtered_df["ShouldStock"] == True]
elif stock_filter == "Don't Stock":
    filtered_df = filtered_df[filtered_df["ShouldStock"] == False]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Items ({len(filtered_df)} records)")

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
            file_name=f"items_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "ItemID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Item": st.column_config.TextColumn("Item Name", width="medium", required=True),
    "Variety": st.column_config.TextColumn("Variety", width="medium"),
    "Color": st.column_config.TextColumn("Color", width="small"),
    "TypeID": st.column_config.NumberColumn("Type ID", width="small"),
    "Inactive": st.column_config.CheckboxColumn("Inactive", width="small"),
    "ShouldStock": st.column_config.CheckboxColumn("Stock?", width="small"),
    "SunConditions": st.column_config.TextColumn("Sun", width="medium"),
    "LabelDescription": st.column_config.TextColumn("Label", width="large"),
    "Definition": st.column_config.TextColumn("Definition", width="large"),
    "PictureLayout": st.column_config.TextColumn("Pic Layout", width="medium"),
    "PictureLink": st.column_config.TextColumn("Pic Link", width="medium"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",  # No row deletion in table - use bulk delete
        column_config=column_config,
        hide_index=True,
        key="items_editor",
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
                    item_id = edited_df.loc[idx, "ItemID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "ItemID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_item(item_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} items")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} items")

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

    item_types = api.item_type_cache.set_index("TypeID")["Type"].to_dict()

    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)

    with bulk_col1:
        st.write("**Mark as Inactive**")
        inactive_ids = st.text_input(
            "Item IDs (comma-separated)", key="bulk_inactive_ids", placeholder="1,2,3"
        )
        if st.button("Set Inactive", key="bulk_inactive_btn"):
            if inactive_ids:
                ids = [int(x.strip()) for x in inactive_ids.split(",")]
                success = sum([update_item(id, {"Inactive": True}) for id in ids])
                st.success(f"✅ Marked {success}/{len(ids)} items as inactive")
                refresh_cache()
                st.rerun()

    with bulk_col2:
        st.write("**Change Type**")
        bulk_type_ids = st.text_input(
            "Item IDs (comma-separated)", key="bulk_type_ids", placeholder="1,2,3"
        )
        new_type = st.selectbox(
            "New Type",
            options=list(item_types.keys()),
            format_func=lambda x: item_types[x],
            key="bulk_new_type",
        )
        if st.button("Update Type", key="bulk_type_btn"):
            if bulk_type_ids:
                ids = [int(x.strip()) for x in bulk_type_ids.split(",")]
                success = sum([update_item(id, {"TypeID": new_type}) for id in ids])
                st.success(f"✅ Updated type for {success}/{len(ids)} items")
                refresh_cache()
                st.rerun()

    with bulk_col3:
        st.write("**Delete Items**")
        st.warning("⚠️ Permanent action!")
        delete_ids = st.text_input(
            "Item IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
        )
        confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
        if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
            if delete_ids:
                ids = [int(x.strip()) for x in delete_ids.split(",")]
                success = sum([delete_item(id) for id in ids])
                st.success(f"✅ Deleted {success}/{len(ids)} items")
                refresh_cache()
                st.rerun()

# ==================== FOOTER ====================
st.divider()

col1, col2 = st.columns([3, 1])

with col1:
    st.caption(
        f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total items in database: {len(api.item_cache)}"
    )

with col2:
    if st.button("🔍 Debug View", use_container_width=True):
        st.session_state.show_debug = not st.session_state.get("show_debug", False)

# ==================== DEBUG PANEL ====================
if st.session_state.get("show_debug", False):
    with st.expander("🐛 Debug & Verification Tools", expanded=True):
        st.write("### Database Verification")

        debug_col1, debug_col2 = st.columns(2)

        with debug_col1:
            st.write("**Query Item from DB**")
            check_id = st.number_input(
                "Item ID to verify", min_value=1, step=1, key="check_id"
            )
            if st.button("🔍 Query DB Directly"):
                result = api._get_by_id(IM, "ItemID", check_id)
                if result:
                    st.success(f"✅ Found in database:")
                    st.json(result)
                else:
                    st.error(f"❌ Item {check_id} not found in database")

        with debug_col2:
            st.write("**Compare Cache vs DB**")
            compare_id = st.number_input(
                "Item ID to compare", min_value=1, step=1, key="compare_id"
            )
            if st.button("⚖️ Compare Cache vs DB"):
                cached = api.item_cache[api.item_cache["ItemID"] == compare_id]
                from_db = api._get_by_id(IM, "ItemID", compare_id)

                if not cached.empty and from_db:
                    st.write("**From Cache:**")
                    st.json(cached.iloc[0].to_dict())
                    st.write("**From Database:**")
                    st.json(from_db)

                    if cached.iloc[0].to_dict() == from_db:
                        st.success("✅ Cache and DB are in sync")
                    else:
                        st.warning("⚠️ Cache and DB differ - cache may be stale")
                else:
                    st.error("Item not found in cache or DB")

        st.divider()
        st.write("**Recent Operations Log**")
        st.caption("Check your terminal/logs for detailed operation logs")
