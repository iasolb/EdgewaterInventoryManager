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
from models import OrderNote as ORN
from payloads import OrderNotePayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Order Notes Administration",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("order_note_cache", api.get_order_note_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the order note cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("order_note_cache", api.get_order_note_full)
    st.success("✅ Data refreshed!")


def create_order_note_from_form(form_data: dict) -> Optional[dict]:
    """Create a new order note"""
    try:
        result = api.table_add_order_note(OrderNote=str(form_data["OrderNote"]))
        return result
    except Exception as e:
        st.error(f"❌ Error creating order note: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_order_note(note_id: int, updates: dict) -> bool:
    """Update an order note"""
    try:
        allowed_fields = {"OrderNote"}

        result = api.generic_update(
            model_class=ORN,
            id_column="OrderNoteID",
            id_value=note_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated OrderNote {note_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating order note {note_id}: {e}")
        logger.error(f"Update failed for OrderNote {note_id}: {e}")
        return False


def delete_order_note(note_id: int) -> bool:
    """Delete an order note"""
    try:
        return api._delete(ORN, "OrderNoteID", note_id)
    except Exception as e:
        st.error(f"❌ Error deleting order note {note_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("📝 Order Notes Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Order Note", expanded=st.session_state.show_add_form):
    st.write("### Create New Order Note")

    with st.form("add_order_note_form", clear_on_submit=True):
        form_note = st.text_input("Order Note *", key="form_note")

        submitted = st.form_submit_button(
            "💾 Create Order Note", type="primary", use_container_width=True
        )

        if submitted:
            if not form_note:
                st.error("❌ Order note is required!")
            else:
                form_data = {"OrderNote": form_note}

                result = create_order_note_from_form(form_data)
                if result:
                    st.success(f"✅ Order Note created! (ID: {result['OrderNoteID']})")
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Order Notes",
    placeholder="Search by note text...",
    key="search_term",
)

# Apply filters
filtered_df = api.order_note_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["OrderNote"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Order Notes ({len(filtered_df)} records)")

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
            file_name=f"order_notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "OrderNoteID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "OrderNote": st.column_config.TextColumn("Note", width="large", required=True),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="order_notes_editor",
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
                    note_id = edited_df.loc[idx, "OrderNoteID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "OrderNoteID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_order_note(note_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} order notes")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} order notes")

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

    st.write("**Delete Order Notes**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Note IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_order_note(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} order notes")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total order notes: {len(api.order_note_cache)}"
)
