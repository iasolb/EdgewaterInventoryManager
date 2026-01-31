"""
Employee Page - Edgewater Inventory Management System
Author: Ian Solberg
Date: 1-31-2026
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
api.reset_cache("planting_view_cache", api.get_pitch_view)
st.set_page_config(
    page_title="Plantings",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.2, blur=0
)

st.title("Employee Pitch Page")
st.write("This feature is coming soon!")
btn_col1 = st.columns(1)[0]
with btn_col1:
    if st.button("Back", disabled=False):
        st.switch_page("edgewater.py")


content_layout = st.columns([0.1, 30, 0.1])
