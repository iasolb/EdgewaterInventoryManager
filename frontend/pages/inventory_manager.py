"""
Plants Page - Edgewater Inventory Management System
Author: Ian Solberg
Date: 10-16-2025
"""

# ====== IMPORTS ======
from sqlalchemy import Text
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))

from database import get_db_session
from models import Item
from rest.api import EdgewaterAPI

# ===== STREAMLIT CONFIG =====

st.set_page_config(
    page_title="Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state.show_form = False
# ===== INITIALIZE API AND PAGE =====
api = EdgewaterAPI()

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

api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.2, blur=0
)
api.assign_inventory_data()
# ==== Sidebar ==============
st.sidebar.header("Edgewater Inventory Manager")
options = st.container()


## SideBar Filters
st.sidebar.header("Filters")

# ===== Item Search (Text Input) =====
selected_search = st.sidebar.text_input("Search Items")

# ===== TypeID Selection (MultiSelect) =====
st.sidebar.write("Select Item Types to Filter:")
item_types = api.get_item_types()
selected_types = st.sidebar.multiselect(
    "Item Types",
    options=item_types["Type"].tolist(),
    default=[],
    key="selected_types",
)

# Top row with buttons
top_row = st.columns([1, 2, 1])

# back button
with top_row[0]:  # left column - back button
    if st.button("← Back"):
        st.switch_page("edgewater.py")

with top_row[1]:  # middle column - empty or title
    pass

with top_row[2]:  # Add Item Button
    if st.button("Add New Item", disabled=False):
        st.session_state.show_form = True

# ===== Add New Item Logic (FORM) =====
# TODO check create crud

if st.session_state.show_form:  # Add Item Form Logic
    with st.form("add_item_form"):
        st.write("Add Item Information")
        Item = st.text_input("Item Name")
        Variety = st.text_input("Variety")
        Inactive = st.checkbox("Inactive", value=False)
        Color = st.text_input("Color")
        ShouldStock = st.checkbox("Should Stock", value=False)
        TypeID = st.selectbox("Item Type", options=api.get_item_types())
        LabelDescription = st.text_area("Label Description")
        Definition = st.text_area("Definition")
        PictureLink = st.text_input("Picture Link")
        SunConditions = st.selectbox("Sun Conditions", options=api.get_sun_conditions())
        submitted = st.form_submit_button("Submit")
        if submitted:
            decoded_item_type = api.decode_type(TypeID)
            item_data = {
                "Item": Item,
                "Variety": Variety,
                "Inactive": Inactive,
                "Color": Color,
                "ShouldStock": ShouldStock,
                "TypeID": api.get_type_id_by_name(TypeID),
                "LabelDescription": LabelDescription,
                "Definition": Definition,
                "PictureLink": PictureLink,
                "SunConditions": SunConditions,
            }
            api._create(model_class=Item, data=item_data)
        st.write("This feature is coming soon!")

# ===== Edit Existing Item (Form) =====
# TODO check update crud

# ===== Delete Item (Button with Confirmation) =====
# TODO check delete crud

# ===== Item Table (DataFrame) =====

content_layout = st.columns([0.1, 30, 0.1])

with content_layout[1]:  # middle column with the dataframe
    data = api.get_inventory_display()
    st.dataframe(data, use_container_width=True)
