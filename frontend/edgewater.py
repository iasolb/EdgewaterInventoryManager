"""
Edgewater Inventory Management System - Landing Page
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
    page_title="Edgewater Inventory Manager",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "current_page" not in st.session_state:
    st.session_state.current_page = "inventory_manager"


def change_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()


SCRIPT_DIR = api.SCRIPT_DIR
PROJECT_ROOT = api.PROJECT_ROOT
LOGO_PATH = api.LOGO_PATH
BACKGROUND_PATH = api.BACKGROUND_PATH
api.set_background(BACKGROUND_PATH, black_and_white=False, overlay_opacity=0.85, blur=0)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.title("Edgewater Database Manager")
    try:
        st.image(LOGO_PATH, width=400)
    except:
        st.caption("(Logo image not found - add your logo to image_assets/)")

btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 2, 2, 2])
with btn_col1:
    if st.button("Inventory Manager", disabled=False):
        st.switch_page("pages/inventory_manager.py")
with btn_col2:
    if st.button("Plantings", disabled=False):
        st.switch_page("pages/plantings.py")
with btn_col3:
    if st.button("Label Generator", disabled=False):
        st.switch_page("pages/label_generator.py")
with btn_col4:
    if st.button("Sales and Analytics", disabled=False):
        st.switch_page("pages/sales_and_analytics.py")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #ffffff;'>
        <p>Edgewater Database + UI Migrated & Built by Ian Solberg</p>
    </div>
    """,
    unsafe_allow_html=True,
)
#     try:
#         with get_db_session() as session:
#             items = session.query(Item).all()

#             if items:
#                 data = []
#                 for item in items:
#                     item_dict = {
#                         column.name: getattr(item, column.name)
#                         for column in Item.__table__.columns
#                     }
#                     data.append(item_dict)

#                 df = pd.DataFrame(data)

#                 st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
#                 st.dataframe(df, use_container_width=True, hide_index=True, height=500)
#                 st.markdown("</div>", unsafe_allow_html=True)

#                 st.success(f"Total records: {len(df)}")
#             else:
#                 st.info("No items found in the database.")

#     except Exception as e:
#         st.error(f"Error connecting to database: {str(e)}")
#         st.info("Make sure your database is running and properly configured in .env")

#         st.subheader("Example Data (Database not connected)")
#         example_df = pd.DataFrame(
#             {
#                 "ID": [1, 2, 3],
#                 "Name": ["Tomato", "Lettuce", "Cucumber"],
#                 "Type": ["Vegetable", "Vegetable", "Vegetable"],
#                 "Price": [2.99, 1.99, 1.49],
#             }
#         )
#         st.dataframe(example_df, use_container_width=True)
