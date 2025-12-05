"""
Label Generator - Edgewater Inventory Management System
Author: Ian Solberg
Date: 10-16-2025
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rest"))
from database import get_db_session
from models import Item
from rest.api import EdgewaterAPI

api = EdgewaterAPI()

st.set_page_config(
    page_title="Label Generator",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.2, blur=0
)
st.title("Label Generator")
st.write("This feature is coming soon!")
btn_col1 = st.columns(1)[0]
with btn_col1:
    if st.button("Back", disabled=False):
        st.switch_page("edgewater.py")


content_layout = st.columns([0.1, 30, 0.1])

with content_layout[1]:  # middle column with the dataframe
    label_data, sun_conditions = api.get_label_display()
    st.dataframe(label_data, use_container_width=True)
    st.dataframe(sun_conditions, use_container_width=True)
