"""
Plants Page - Edgewater Inventory Management System
Author: Ian Solberg
Date: 10-16-2025
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from database import get_db_session
from models import Item
from rest.api import EdgewaterAPI

# ===== MUST BE FIRST STREAMLIT COMMAND =====
st.set_page_config(
    page_title="Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== NOW you can use other Streamlit commands =====
api = EdgewaterAPI()

# Hide default navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Set background
api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.2, blur=0
)

# Sidebar
st.sidebar.header("Edgewater Inventory Manager")
left_col, middle_col, right_col = st.columns([1, 2, 1])

# Back button in left column
with left_col:
    if st.button("← Back"):
        st.switch_page("edgewater.py")

# Content box in right column
with right_col:
    if st.button("Add New Item", disabled=False):
        pass
    st.write("This feature is coming soon!")


## SideBar Filters
st.sidebar.header("Filters")

# ===== Item Search (Text Input) =====
selected_search = st.sidebar.text_input("Search Items")

# ===== TypeID Selection (MultiSelect) =====
st.sidebar.write("Select Item Types to Filter:")
selected_types = st.sidebar.multiselect(
    "Item Types",
    options=["Vegetable", "Fruit", "Herb", "Flower"],
    default=[],
    key="selected_types",
)

# ===== Item Table (DataFrame) =====
# ===== Add New Item (Form) =====
# ===== Edit Existing Item (Form) =====
# ===== Delete Item (Button with Confirmation) =====
