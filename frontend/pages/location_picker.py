"""
Location picker component for employee pages.
Groups locations by category (Greenhouses, Fields, Buildings/Other)
and presents a two-step selector: category → specific location.

Usage:
    from location_picker import render_location_picker
    selected_id = render_location_picker(loc_df, key_prefix="plant")
"""

import streamlit as st
import pandas as pd


def _categorize_location(name: str) -> str:
    """Assign a location to a category based on its name."""
    lower = name.lower().strip()
    if lower.startswith("field"):
        return "🌾 Fields"
    if any(lower.startswith(p) for p in ("greenhouse", "green house", "gh")):
        return "🏠 Greenhouses"
    return "🏗️ Other"


# Category display order
_CATEGORY_ORDER = ["🏠 Greenhouses", "🌾 Fields", "🏗️ Other"]


def render_location_picker(
    loc_df: pd.DataFrame,
    key_prefix: str = "loc",
    exclude: list[str] | None = None,
    label: str = "### 📍 Where are you planting?",
) -> int | None:
    """
    Render a two-step location picker: category buttons → location buttons.
    Returns the selected LocationID or None.

    Args:
        loc_df: DataFrame with LocationID and Location columns
        key_prefix: unique prefix for session_state keys (use different prefixes
                    if multiple pickers on the same page)
        exclude: list of location names to exclude (e.g. ["Pitch Pile", "Unknown"])
        label: markdown header to show above the picker
    """
    cat_key = f"{key_prefix}_category"
    loc_key = f"{key_prefix}_location_id"

    # Init session state
    if cat_key not in st.session_state:
        st.session_state[cat_key] = None
    if loc_key not in st.session_state:
        st.session_state[loc_key] = None

    if loc_df is None or loc_df.empty:
        st.caption("No locations configured.")
        return None

    # Filter exclusions
    working_df = loc_df.copy()
    if exclude:
        exclude_lower = [e.lower() for e in exclude]
        working_df = working_df[~working_df["Location"].str.lower().isin(exclude_lower)]

    if working_df.empty:
        st.caption("No locations available.")
        return None

    # Build category groups
    working_df["_category"] = working_df["Location"].apply(_categorize_location)
    categories = [c for c in _CATEGORY_ORDER if c in working_df["_category"].values]

    st.markdown(label)

    # ---- Step 1: Category selection ----
    cat_cols = st.columns(len(categories) + 1)

    # "No Location" option
    with cat_cols[0]:
        is_none = (
            st.session_state[loc_key] is None and st.session_state[cat_key] is None
        )
        if st.button(
            "✅ None" if is_none else "📍 None",
            use_container_width=True,
            type="primary" if is_none else "secondary",
            key=f"{key_prefix}_cat_none",
        ):
            st.session_state[cat_key] = None
            st.session_state[loc_key] = None
            st.rerun()

    for i, cat in enumerate(categories):
        with cat_cols[i + 1]:
            is_selected = st.session_state[cat_key] == cat
            # Count locations in this category
            count = len(working_df[working_df["_category"] == cat])
            if st.button(
                f"{'✅' if is_selected else ''} {cat} ({count})",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                key=f"{key_prefix}_cat_{i}",
            ):
                st.session_state[cat_key] = cat
                # Clear specific location when switching categories
                st.session_state[loc_key] = None
                st.rerun()

    # ---- Step 2: Specific location within category ----
    if st.session_state[cat_key] is not None:
        cat_locations = working_df[
            working_df["_category"] == st.session_state[cat_key]
        ].sort_values("Location")

        # Render location buttons in rows of 5
        locs_list = list(cat_locations.iterrows())
        rows_needed = (len(locs_list) + 4) // 5  # ceiling division

        for row_idx in range(rows_needed):
            start = row_idx * 5
            end = min(start + 5, len(locs_list))
            row_locs = locs_list[start:end]

            cols = st.columns(5)
            for col_idx, (_, loc_row) in enumerate(row_locs):
                with cols[col_idx]:
                    loc_id = int(loc_row["LocationID"])
                    loc_name = loc_row["Location"]
                    is_selected = st.session_state[loc_key] == loc_id
                    if st.button(
                        f"{'✅' if is_selected else '📍'} {loc_name}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                        key=f"{key_prefix}_loc_{loc_id}",
                    ):
                        st.session_state[loc_key] = loc_id
                        st.rerun()

    # ---- Show current selection ----
    selected_id = st.session_state[loc_key]
    if selected_id is not None:
        sel = working_df[working_df["LocationID"] == selected_id]
        if not sel.empty:
            st.caption(f"Selected: **{sel.iloc[0]['Location']}**")
    else:
        st.caption("Selected: **No location**")

    return selected_id
