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
from collections import defaultdict
from typing import Tuple, Optional, DefaultDict
import base64
from models import (
    Inventory,
    Item,
    ItemType,
    Unit,
    UnitCategory,
    Broker,
    Shipper,
    Supplier,
    GrowingSeason,
    OrderItemType,
    OrderNote,
    Price,
    Planting,
    Pitch,
    Order,
    OrderItem,
)
import streamlit as st
import os
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError


class EdgewaterAPI:
    """Class to interact with Edgewater API"""

    def __init__(self, *args, **kwds):
        """
        Constructor for EdgewaterAPI
        """
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
        self.inventory_data = None
        self.plantings_data = None
        self.label_data = None
        self.orders_data = None
        # self.sales_data = None # TODO ask about data collection for sales

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
                clean_data = []
                for row in results:
                    row_dict = {}
                    for key, value in row.__dict__.items():
                        if (
                            key != "_sa_instance_state"
                        ):  # Skip SQLAlchemy internal state
                            row_dict[key] = (
                                value  # unpack the iterator object (must happen in lowest level crud before session closes)
                            )
                    clean_data.append(row_dict)

                return pd.DataFrame(clean_data)

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
    MISC TOOLBOX (may become separate module)
    """

    def decode_type(self, type_name: str) -> int:
        """
        retrieves the numerical coding for typeID in items table
        """
        type_mapping = {
            "Unassigned": 0,
            "Soil": 3,
            "Labels and Tags": 4,
            "Annual": 6,
            "Perennial": 7,
            "Vegetable": 8,
            "Hard Good": 11,
            "Fruit": 12,
            "Herb": 13,
        }
        return type_mapping.get(type_name, 0)  # Default to 0 if not found

    def get_sun_conditions(self) -> List:
        """
        Get list of sun conditions for dropdowns
        """
        return self._get_all(model_class=Item).SunConditions.unique().tolist()

    def get_item_types(self):
        """
        Get list of item types for dropdowns
        """
        from models import ItemType

        return pd.DataFrame(self._get_all(model_class=ItemType))

    """
    MANAGE INVENTORY WORKFLOW METHODS
    """

    # GET
    def _get_inventory_full(self) -> pd.DataFrame:
        """
        Get full inventory data from SQL view
        """
        from models import InventoryFullView

        try:
            result = self._get_all(model_class=InventoryFullView)
            result = result.sort_values(by="DateCounted", ascending=False)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Inventory List: {e}")
            return pd.DataFrame()

    def assign_inventory_data(self) -> None:
        try:
            self.inventory_data = self._get_inventory_full()
        except Exception as e:
            logger.error(f"error assigning inventory data to api state var: {e}")

    def get_inventory_display(self) -> pd.DataFrame:
        try:
            plant_list_full = self.inventory_data
            result = plant_list_full[
                [
                    "NumberOfUnits",
                    "DateCounted",
                    "Item",
                    "Variety",
                    "Color",
                    "Type",
                    "SunConditions",
                    "UnitSize",
                    "UnitType",
                    "Inactive",
                    "ShouldStock",
                    "LabelDescription",
                    "InventoryComments",
                ]
            ]
            return result
        except Exception as e:
            logger.error(f"Error Inventory Display Subset: {e}")
            return pd.DataFrame()

    # POST
    def inventory_add(self, entry_data: Dict[str, Any]):
        from models import Item

        try:
            last_id = self._get_all(model_class=Item)["ItemID"].max()
            entry_data["ItemID"] = last_id + 1
            self._create(model_class=Item, data=entry_data)
        except Exception as e:
            print(f"Error adding to plant list: {e}")

    # DELETE
    def inventory_remove(self, target_id: int):
        from models import Item, Inventory

        try:
            pass
        except Exception as e:
            logger.error(f"Error deleting item entry: {e}")

    # UPDATE
    def inventory_update(self, target_id: int, update_data: Dict[str, Any]):
        try:
            pass
        except Exception as e:
            logger.error(f"Error updating item info: {e}")

    """
    PLANTINGS WORKFLOW METHODS
    """

    # GET
    def _get_plantings_full(self) -> pd.DataFrame:
        """
        Get full plantings data from SQL view
        """
        from models import PlantingsFullView

        try:
            result = self._get_all(model_class=PlantingsFullView)
            result = result.sort_values(
                by=["DatePlanted", "PlantingID"],
                ascending=False,
            )

            return result
        except Exception as e:
            logger.error(f"Error retrieving Plantings List: {e}")
            return pd.DataFrame()

    def assign_planting_data(self):
        try:
            self.plantings_data = self._get_plantings_full()
        except Exception as e:
            logger.error(f"error assigning planting data to api state var: {e}")

    def get_plantings_display(self, *filters: Dict[str, any]) -> pd.DataFrame:
        try:
            full = self.plantings_data

            plantings_display = full[
                [
                    "PlantingID",
                    "NumberOfUnits",
                    "Item",
                    "Variety",
                    "Color",
                    "DatePlanted",
                    "PlantingComments",
                    "ItemID",
                    "UnitType",
                    "UnitSize",
                    "UnitCategory",
                ]
            ]
            # TODO ADD FILTER LOGIC
            return plantings_display
        except Exception as e:
            logger.error(f"error retriving plantings subset: {e}")
            return pd.DataFrame()

    # POST
    def plantings_add(self, entry_data: Dict[str, Any]):
        from models import Planting

        try:
            last_id = self._get_all(model_class=Planting)["PlantingID"].max()
            entry_data["PlantingID"] = last_id + 1
            self._create(model_class=Item, data=entry_data)
        except Exception as e:
            print(f"Error adding to plant list: {e}")

    # DELETE
    def plantings_remove(self, target_id: int):
        from models import Planting

        try:
            pass
        except Exception as e:
            logger.error(f"Error deleting item entry: {e}")

    # UPDATE
    def plantings_update(self, target_id: int, update_data: Dict[str, Any]):
        try:
            pass
        except Exception as e:
            logger.error(f"Error updating item info: {e}")

    """
    LABEL GENERATING WORKFLOW METHODS
    """

    # GET
    def _get_label_data_full(self) -> pd.DataFrame:
        """
        Get full label data from SQL view
        """
        from models import LabelDataFullView

        try:
            result = self._get_all(model_class=LabelDataFullView)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Label Data: {e}")
            return pd.DataFrame()

    def assign_label_data(self) -> None:
        try:
            self.label_data = self._get_label_data_full()
        except Exception as e:
            logger.error(f"error assigning label data to api state var: {e}")

    def get_label_display(
        self, item_id: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        try:
            label_data_full = self.label_data

            if item_id:
                label_data_full = label_data_full[label_data_full["ItemID"] == item_id]
            label_data = label_data_full[
                [
                    "Item",
                    "Variety",
                    "Color",
                    "Type",
                    "LabelDescription",
                    "UnitPrice",
                    "SunConditions",
                ]
            ]
            return label_data
        except Exception as e:
            logger.error(f"Error getting label subset: {e} (data operations error)")
            return pd.DataFrame(), pd.DataFrame()

    """
    ORDER TRACKING WORKFLOWS
    """

    # GET
    def _get_orders_full(self) -> pd.DataFrame:
        """
        Get full orders data from SQL view
        """
        from models import OrdersFullView

        try:
            result = self._get_all(model_class=OrdersFullView)
            result = result.sort_values(
                by=["DatePlaced", "DateDue"],
                ascending=False,
            )
            return result
        except Exception as e:
            logger.error(f"Error retrieving Orders Data: {e}")
            return pd.DataFrame()

    def assign_orders_data(self) -> None:
        try:
            self.orders_data = self._get_orders_full()
        except Exception as e:
            logger.error(f"error assigning order data to api state var: {e}")

    def get_orders_display(self, *filters: Dict[str, any]) -> pd.DataFrame:
        try:
            full_orders = self.orders_data
            result = full_orders[
                [
                    "Supplier",
                    "Broker",
                    "Shipper",
                    "DatePlaced",
                    "DateDue",
                    "DateReceived",
                    "Received",
                    "ToOrder",
                    "ItemCode",
                    "ItemID",
                    "Unit",
                    "NumberOfUnits",
                    "UnitPrice",
                    "OrderNoteCode",
                    "OrderNoteDecode",
                    "OrderItemComments",
                    "OrderComments",
                    "Leftover",
                    "OrderItemID",
                    "OrderID",
                    "GrowingSeason",
                    "OrderItemType",
                    "OrderNumber",
                    "TrackingNumber",
                    "TotalCost",
                    "BrokerComments",
                    "ShipperComments",
                    "SupplierComments",
                ]
            ]
            # TODO ADD FILTER LOGIC
            return result
        except Exception as e:
            logger.error(
                f"Error getting Order data subset: {e} (data operations error)"
            )
            return pd.DataFrame()

    def get_orders_summary(self) -> pd.DataFrame:  # TODO FIX THIS FUNCTION !!!
        try:
            full_orders = self.orders_data
            summary = (
                full_orders.groupby("OrderID")
                .agg(
                    {
                        "Supplier": "first",
                        "Broker": "first",
                        "Shipper": "first",
                        "DatePlaced": "first",
                        "DateDue": "first",
                        "DateReceived": "first",
                        "Received": "first",
                        "OrderNumber": "first",
                        "TrackingNumber": "first",
                        "TotalCost": "first",
                        "GrowingSeason": "first",
                        "OrderItemID": "count",
                        "OrderComments": "first",
                        "BrokerComments": "first",
                        "ShipperComments": "first",
                        "SupplierComments": "first",
                    }
                )
                .reset_index()
            )

            # Rename count column since counting number of unique items
            summary = summary.rename(columns={"OrderItemID": "UniqueItems"})
            result = summary.sort_values(by="DatePlaced", ascending=False)
            return result
        except Exception as e:
            logger.error(f"Error getting orders summary: {e}")
            return pd.DataFrame()

    # POST
    def orders_add(self, entry_data: Dict[str, any]) -> None:
        from models import Order

        try:
            last_id = self._get_all(model_class=Order)["OrderID"].max()
            entry_data["OrderID"] = last_id + 1
            self._create(model_class=Item, data=entry_data)
        except Exception as e:
            print(f"Error adding to plant list: {e}")

    # DELETE
    def orders_remove(self, target_id: int):
        from models import Order

        try:
            pass
        except Exception as e:
            logger.error(f"Error deleting item entry: {e}")

    # UPDATE
    def orders_update(self, target_id: int, update_data: Dict[str, Any]):
        from models import Order

        try:
            pass
        except Exception as e:
            logger.error(f"Error updating item info: {e}")

    """
    SALES & ANALYTICS WORKFLOWS
    """

    # def _get_sales_full(self) -> pd.DataFrame:
    #     try:
    #         pass
    #     except Exception as e:
    #         logger.error(f"Error retrieving Sales Data from db: {e}")
    #         return pd.DataFrame()

    # def get_sales_display(self) -> pd.DataFrame:
    #     try:
    #         pass
    #     except Exception as e:
    #         logger.error(
    #             f"Error getting sales data subset: {e} (data operations error)"
    #         )
    #         return pd.DataFrame(), pd.DataFrame()
