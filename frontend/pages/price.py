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
from models import Price as PRC
from payloads import PricePayload

api = EdgewaterAPI()

st.set_page_config(
    page_title="Prices Administration",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.reset_cache("price_cache", api.get_price_full)
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
        api.reset_cache("price_cache", api.get_price_full)
        api.reset_cache("item_cache", api.get_item_full)
        api.reset_cache("unit_cache", api.get_unit_full)
    st.success("✅ Data refreshed!")


def create_price_from_form(form_data: dict) -> Optional[dict]:
    """Create a new price record"""
    try:
        result = api.table_add_price(
            ItemID=int(form_data["ItemID"]),
            UnitID=int(form_data["UnitID"]),
            UnitPrice=float(form_data["UnitPrice"]),
            Year=form_data.get("Year"),
        )
        return result
    except Exception as e:
        st.error(f"❌ Error creating price: {e}")
        logger.error(f"Create failed: {e}")
        return None


def update_price(price_id: int, updates: dict) -> bool:
    """Update a price record"""
    try:
        allowed_fields = {"ItemID", "UnitID", "UnitPrice", "Year"}

        result = api.generic_update(
            model_class=PRC,
            id_column="PriceID",
            id_value=price_id,
            updates=updates,
            allowed_fields=allowed_fields,
        )

        if result:
            logger.info(f"✓ Updated Price {price_id}: {updates}")

        return result is not None
    except Exception as e:
        st.error(f"❌ Error updating price {price_id}: {e}")
        logger.error(f"Update failed for Price {price_id}: {e}")
        return False


def delete_price(price_id: int) -> bool:
    """Delete a price record"""
    try:
        return api._delete(PRC, "PriceID", price_id)
    except Exception as e:
        st.error(f"❌ Error deleting price {price_id}: {e}")
        return False


# ==================== HEADER ====================
top_row = st.columns([1, 2, 1])

with top_row[0]:
    if st.button("← Back to Admin"):
        st.switch_page("pages/admin_landing.py")

with top_row[1]:
    st.title("💰 Prices Administration")

with top_row[2]:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_cache()
        st.rerun()

st.divider()

# ==================== ADD NEW FORM ====================
with st.expander("➕ Add New Price Record", expanded=st.session_state.show_add_form):
    st.write("### Create New Price Record")

    # Prepare lookup dictionaries
    items_dict = api.item_cache.set_index("ItemID")["Item"].to_dict()
    units_dict = api.unit_cache.apply(
        lambda x: f"{x['UnitSize']} {x['UnitType']}", axis=1
    ).to_dict()

    with st.form("add_price_form", clear_on_submit=True):
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

        with col2:
            form_unit_price = st.number_input(
                "Unit Price *", min_value=0.0, step=0.01, key="form_unit_price"
            )
            form_year = st.text_input("Year", key="form_year", placeholder="e.g., 2024")

        submitted = st.form_submit_button(
            "💾 Create Price Record", type="primary", use_container_width=True
        )

        if submitted:
            if form_unit_price <= 0:
                st.error("❌ Unit price must be greater than 0!")
            else:
                form_data = {
                    "ItemID": form_item_id,
                    "UnitID": form_unit_id,
                    "UnitPrice": form_unit_price,
                    "Year": form_year or None,
                }

                result = create_price_from_form(form_data)
                if result:
                    st.success(f"✅ Price record created! (ID: {result['PriceID']})")
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
    year_filter = st.multiselect(
        "Filter by Year",
        options=api.price_cache["Year"].dropna().unique().tolist(),
        key="year_filter",
    )

with filter_col3:
    price_min = st.number_input(
        "Min Price", min_value=0.0, value=0.0, step=1.0, key="price_min"
    )

# Apply filters
filtered_df = api.price_cache.copy()

# Item filter
if item_filter:
    item_ids = api.item_cache[api.item_cache["Item"].isin(item_filter)][
        "ItemID"
    ].tolist()
    filtered_df = filtered_df[filtered_df["ItemID"].isin(item_ids)]

# Year filter
if year_filter:
    filtered_df = filtered_df[filtered_df["Year"].isin(year_filter)]

# Price filter
if price_min > 0:
    filtered_df = filtered_df[filtered_df["UnitPrice"] >= price_min]

st.divider()

# ==================== DATA DISPLAY & EDITING ====================
st.write(f"### 📊 Price Records ({len(filtered_df)} records)")

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
            file_name=f"prices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

column_config = {
    "PriceID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
    "ItemID": st.column_config.NumberColumn("Item ID", width="small"),
    "UnitID": st.column_config.NumberColumn("Unit ID", width="small"),
    "UnitPrice": st.column_config.NumberColumn(
        "Unit Price", format="$%.2f", width="medium"
    ),
    "Year": st.column_config.TextColumn("Year", width="small"),
}

if st.session_state.edit_mode:
    st.info("✏️ **Edit Mode** - Make changes, then click 'Save Changes'")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        hide_index=True,
        key="prices_editor",
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
                    price_id = edited_df.loc[idx, "PriceID"]
                    original_row = filtered_df.loc[idx]
                    edited_row = edited_df.loc[idx]

                    changes = {}
                    for col in edited_df.columns:
                        if col != "PriceID":
                            orig_val = original_row[col]
                            edit_val = edited_row[col]

                            if pd.isna(orig_val) and pd.isna(edit_val):
                                continue
                            if orig_val != edit_val:
                                changes[col] = edit_val

                    if changes:
                        if update_price(price_id, changes):
                            success_count += 1
                        else:
                            error_count += 1

                if success_count > 0:
                    st.success(f"✅ Updated {success_count} price records")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} price records")

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
        st.write("**Update Year**")
        bulk_price_ids = st.text_input(
            "Price IDs (comma-separated)", key="bulk_price_ids", placeholder="1,2,3"
        )
        new_year = st.text_input("New Year", key="bulk_new_year", placeholder="2024")
        if st.button("Update Year", key="bulk_year_btn"):
            if bulk_price_ids and new_year:
                ids = [int(x.strip()) for x in bulk_price_ids.split(",")]
                success = sum([update_price(id, {"Year": new_year}) for id in ids])
                st.success(f"✅ Updated year for {success}/{len(ids)} price records")
                refresh_cache()
                st.rerun()

    with bulk_col2:
        st.write("**Delete Price Records**")
        st.warning("⚠️ Permanent action!")
        delete_ids = st.text_input(
            "Price IDs (comma-separated)", key="bulk_delete_ids", placeholder="1,2,3"
        )
        confirm_delete = st.checkbox("Confirm deletion", key="confirm_bulk_delete")
        if st.button("🗑️ Delete", key="bulk_delete_btn", disabled=not confirm_delete):
            if delete_ids:
                ids = [int(x.strip()) for x in delete_ids.split(",")]
                success = sum([delete_price(id) for id in ids])
                st.success(f"✅ Deleted {success}/{len(ids)} price records")
                refresh_cache()
                st.rerun()

# ==================== FOOTER ====================
st.divider()

st.caption(
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total price records: {len(api.price_cache)}"
)
