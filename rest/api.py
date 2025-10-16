import pandas as pd
import requests
from database import Database
from typing import List, Dict, Any
from loguru import logger
import base64
import streamlit as st
from pathlib import Path


class EdgewaterAPI:
    """Class to interact with Edgewater API"""

    def __init__(self, *args, **kwds):
        # Initialize instance attributes inside __init__
        self.SCRIPT_DIR = Path(__file__).parent
        self.PROJECT_ROOT = self.SCRIPT_DIR.parent
        self.LOGO_PATH = (
            self.PROJECT_ROOT
            / "database"
            / "datasource"
            / "image_assets"
            / "edgewater_logo.png"
        )
        self.BACKGROUND_PATH = (
            self.PROJECT_ROOT
            / "database"
            / "datasource"
            / "image_assets"
            / "farmstand_background.png"
        )

    def _get_base64_image(self, image_path):  # Added 'self' parameter
        """Convert image to base64 for CSS background"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            st.warning(f"Image not found: {image_path}")
            return None

    def set_background(self, image_path):
        """Set background image using CSS"""
        base64_image = self._get_base64_image(image_path)
        if base64_image:
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{base64_image}");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                /* Add semi-transparent overlay for better readability */
                .stApp::before {{
                    content: "";
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(255, 255, 255, 0.85);
                    z-index: -1;
                }}
                /* Style the dataframe container */
                .dataframe-container {{
                    background-color: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

    """
    PLANTS WORKFLOW METHODS
    """

    def get_plants(self):
        pass

    """
    PLANTINGS WORKFLOW METHODS
    """

    def get_plantings(self):
        pass

    """
    LABEL GENERATING WORKFLOW METHODS
    """

    def get_label_info(self):
        pass

    """
    SALES & ANALYTICS WORKFLOW METHODS
    """

    def get_orders(self):
        pass
