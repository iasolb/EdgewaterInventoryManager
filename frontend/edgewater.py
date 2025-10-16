"""
Edgewater Inventory Management System - Landing Page
Author: Ian Solberg
Date: 10-16-2025
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import base64

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
    st.session_state.current_page = "plants"


def change_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()


SCRIPT_DIR = api.SCRIPT_DIR
PROJECT_ROOT = api.PROJECT_ROOT
LOGO_PATH = api.LOGO_PATH
BACKGROUND_PATH = api.BACKGROUND_PATH
api.set_background(BACKGROUND_PATH)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image(LOGO_PATH, use_container_width=True)
    except:
        st.title("🌿 Edgewater Inventory Manager")
        st.caption("(Logo image not found - add your logo to image_assets/)")

btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
with btn_col1:
    if st.button("Plants", disabled=False):
        st.switch_page("pages/plants.py")
with btn_col2:
    if st.button("Plantings", disabled=False):
        st.switch_page("pages/plantings.py")
with btn_col3:
    if st.button("Label Generator (Coming Soon!)", disabled=False):
        st.switch_page("pages/label_generator.py")
with btn_col4:
    if st.button("Sales and Analytics (Coming Soon!)", disabled=False):
        st.switch_page("pages/sales_and_analytics.py")

if st.session_state.current_page == "plants":
    st.header("Inventory Items")

    try:
        with get_db_session() as session:
            items = session.query(Item).all()

            if items:
                data = []
                for item in items:
                    item_dict = {
                        column.name: getattr(item, column.name)
                        for column in Item.__table__.columns
                    }
                    data.append(item_dict)

                df = pd.DataFrame(data)

                st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True, height=500)
                st.markdown("</div>", unsafe_allow_html=True)

                st.success(f"Total records: {len(df)}")
            else:
                st.info("No items found in the database.")

    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        st.info("Make sure your database is running and properly configured in .env")

        st.subheader("Example Data (Database not connected)")
        example_df = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Tomato", "Lettuce", "Cucumber"],
                "Type": ["Vegetable", "Vegetable", "Vegetable"],
                "Price": [2.99, 1.99, 1.49],
            }
        )
        st.dataframe(example_df, use_container_width=True)

elif st.session_state.current_page == "plantings":
    st.header("Plantings")
    st.info("Plantings page content coming soon!")

elif st.session_state.current_page == "label_generator":
    st.header("Label Generator")
    st.info("Label Generator feature coming soon!")

elif st.session_state.current_page == "sales_analytics":
    st.header("Sales and Analytics")
    st.info("Sales and Analytics feature coming soon!")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Edgewater Inventory Management System</p>
    </div>
    """,
    unsafe_allow_html=True,
)
