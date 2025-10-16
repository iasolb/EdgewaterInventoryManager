"""
Edgewater Farm API for Inventory Management System
Author: Ian Solberg
Date: 10-16-2025
"""

import pandas as pd
import requests
from database import get_db_session
from typing import List, Dict, Any, Optional
from loguru import logger
import base64
import streamlit as st
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError


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

    def _get_base64_image(self, image_path):
        """Convert image to base64 for CSS background"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except FileNotFoundError:
            st.warning(f"Image not found: {image_path}")
            return None

    def set_background(
        self,
        image_path,
        black_and_white: bool = False,
        overlay_opacity: float = 0.85,
        blur: int = 0,
    ):
        """
        Set background image using CSS with optional filters

        Args:
            image_path: Path to the background image
            black_and_white: If True, applies grayscale filter to background
            overlay_opacity: Opacity of white overlay (0.0 to 1.0). Default 0.85
            blur: Blur amount in pixels. Default 0 (no blur)

        Example:
            api.set_background(api.BACKGROUND_PATH, black_and_white=True)
            api.set_background(api.BACKGROUND_PATH, overlay_opacity=0.7, blur=3)
        """
        base64_image = self._get_base64_image(image_path)
        if base64_image:
            # Build CSS filter string
            filters = []
            if black_and_white:
                filters.append("grayscale(100%)")
            if blur > 0:
                filters.append(f"blur({blur}px)")

            filter_css = f"filter: {' '.join(filters)};" if filters else ""

            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{base64_image}");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                    {filter_css}
                }}
                /* Add semi-transparent overlay for better readability */
                .stApp::before {{
                    content: "";
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(255, 255, 255, {overlay_opacity});
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

    # ==================== GENERIC CRUD OPERATIONS ====================

    def _get_all(self, model_class, filters: Optional[Dict] = None):
        """Generic method to get all records from a table"""
        try:
            with get_db_session() as session:
                query = session.query(model_class)

                if filters:
                    for column, value in filters.items():
                        query = query.filter(getattr(model_class, column) == value)

                results = query.all()
                logger.info(
                    f"Retrieved {len(results)} records from {model_class.__tablename__}"
                )
                return results
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving records: {e}")
            raise

    def _get_by_id(self, model_class, id_column: str, id_value: Any):
        """Generic method to get a single record by ID"""
        try:
            with get_db_session() as session:
                result = (
                    session.query(model_class)
                    .filter(getattr(model_class, id_column) == id_value)
                    .first()
                )

                if result:
                    logger.info(f"Found record with {id_column}={id_value}")
                else:
                    logger.warning(f"No record found with {id_column}={id_value}")

                return result
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving record: {e}")
            raise

    def _create(self, model_class, data: Dict[str, Any]):
        """Generic method to create a new record"""
        try:
            with get_db_session() as session:
                new_record = model_class(**data)
                session.add(new_record)
                session.commit()
                session.refresh(new_record)

                logger.info(f"Created new record in {model_class.__tablename__}")
                return new_record
        except SQLAlchemyError as e:
            logger.error(f"Error creating record: {e}")
            session.rollback()
            raise

    def _update(
        self, model_class, id_column: str, id_value: Any, updates: Dict[str, Any]
    ):
        """Generic method to update a record"""
        try:
            with get_db_session() as session:
                record = (
                    session.query(model_class)
                    .filter(getattr(model_class, id_column) == id_value)
                    .first()
                )

                if not record:
                    logger.warning(f"Record with {id_column}={id_value} not found")
                    return None

                # Update attributes
                for column, value in updates.items():
                    setattr(record, column, value)

                session.commit()
                session.refresh(record)

                logger.info(
                    f"Updated record {id_column}={id_value} in {model_class.__tablename__}"
                )
                return record
        except SQLAlchemyError as e:
            logger.error(f"Error updating record: {e}")
            session.rollback()
            raise

    def _delete(self, model_class, id_column: str, id_value: Any):
        """Generic method to delete a record"""
        try:
            with get_db_session() as session:
                record = (
                    session.query(model_class)
                    .filter(getattr(model_class, id_column) == id_value)
                    .first()
                )

                if not record:
                    logger.warning(f"Record with {id_column}={id_value} not found")
                    return False

                session.delete(record)
                session.commit()

                logger.info(
                    f"Deleted record {id_column}={id_value} from {model_class.__tablename__}"
                )
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting record: {e}")
            session.rollback()
            raise

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
