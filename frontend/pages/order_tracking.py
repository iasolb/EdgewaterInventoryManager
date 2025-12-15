"""
Sales and Analytics - Edgewater Inventory Management System
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
api.reset_cache("order_view_cache", api._get_orders_view_full)
st.set_page_config(
    page_title="Order Tracking",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api.set_background(
    api.BACKGROUND_PATH, black_and_white=True, overlay_opacity=0.2, blur=0
)

st.title("Order Tracking")
st.write("This feature is coming soon!")
btn_col1 = st.columns(1)[0]
with btn_col1:
    if st.button("Back", disabled=False):
        st.switch_page("edgewater.py")

content_layout = st.columns([0.1, 30, 0.1])

with content_layout[1]:  # middle column with the dataframe
    st.write("Per-Order Summary")
    summary = api.get_orders_summary()
    st.dataframe(summary, use_container_width=True)
    st.write("Expanded Orders (each item)")
    data = api.get_orders_display()
    st.dataframe(data, use_container_width=True)
