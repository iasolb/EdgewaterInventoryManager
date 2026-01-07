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
from models import Broker as BRK
from payloads import BrokerPayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Brokers Administration",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("broker_cache", api.get_broker_full)

# ==================== SESSION STATE ====================
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


def refresh_cache():
    """Refresh the broker cache after mutations"""
    with st.spinner("Refreshing data..."):
        api.reset_cache("broker_cache", api.get_broker_full)
    st.success("✅ Data refreshed!")


def create_broker_from_form(form_data: dict) -> Optional[dict]:
    """Create a new broker"""
    try:
        result = api.table_add_broker(
            BrokerName=str(form_data["Broker"]),
            BrokerComments=form_data.get("BrokerComments"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating broker: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_broker(broker_id: int, updates: dict) -> bool:
    """Update a broker"""
    try:
        allowed_fields = {"Broker", "BrokerComments"}

        result = api.generic_update(
            model_class=BRK,
            id_column="BrokerID",
            id_value=broker_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Broker {broker_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating broker {broker_id}: {e}")
        logger.error(f"Update failed for Broker {broker_id}: {e}")
        return False


def delete_broker(broker_id: int) -> bool:
    """Delete a broker"""
    try:
        return api._delete(BRK, "BrokerID", broker_id)
    except Exception as e:
        st.error(f"❌ Error deleting broker {broker_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("🤝 Brokers Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Broker", expanded=st.session_state.show_add_form):
    st.write("### Create New Broker")

    with st.form("add_broker_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            form_broker = st.text_input("Broker Name *", key="form_broker")

        with col2:
            form_comments = st.text_area("Comments", key="form_comments", height=100)

        submitted = st.form_submit_button(
            "💾 Create Broker", type="primary", use_container_width=True
        )

        if submitted:
            if not form_broker:
                st.error("❌ Broker name is required!")
            else:
                form_data = {
                    "Broker": form_broker,
                    "BrokerComments": form_comments or None,
                }

                result = create_broker_from_form(form_data)
                if result:
                    st.success(
                        f"✅ Broker '{form_broker}' created! (ID: {result['BrokerID']})"
                    )
                    st.session_state.show_add_form = False
                    refresh_cache()
                    st.rerun()

    st.divider()

# ==================== FILTERS & SEARCH ====================
st.write("### 🔍 Search & Filter")

search_term = st.text_input(
    "Search Brokers",
    placeholder="Search by broker name or comments...",
    key="search_term",
)

# Apply filters
filtered_df = api.broker_cache.copy()

# Search filter
if search_term:
    mask = filtered_df["Broker"].fillna("").str.contains(
        search_term, case=False
    ) | filtered_df["BrokerComments"].fillna("").str.contains(search_term, case=False)
    filtered_df = filtered_df[mask]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Brokers ({len(filtered_df)} records)")

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
            file_name=f"brokers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "BrokerID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "Broker": st.column_config.TextColumn("Broker Name", width="medium", required=True),
    "BrokerComments": st.column_config.TextColumn("Comments", width="large"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="brokers_editor",
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
                    broker_id = edited_df.loc[idx, "BrokerID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "BrokerID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_broker(broker_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} brokers")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} brokers")

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

    st.write("**Delete Brokers**")
    st.warning("⚠️ Permanent action!")
    delete_ids = st.text_input(
        "Broker IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
    )
    confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
    if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
        if delete_ids:
            ids = [int(x.strip()) for x in delete_ids.split(",")]
            success = sum([delete_broker(id) for id in ids])
            st.success(f"✅ Deleted {success}/{len(ids)} brokers")
            refresh_cache()
            st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total brokers: {len(api.broker_cache)}"
)
