"""
Edgewater Farm API for Inventory Management System
Author: Ian Solberg
Date: 10-16-2025
"""

from loguru import logger

import pandas as pd
import requests
from database import get_db_session
import datetime
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set, Text, TypedDict, Callable, Any
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
from payloads import (
    BrokerPayload,
    GrowingSeasonPayload,
    InventoryPayload,
    ItemPayload,
    ItemTypePayload,
    OrderPayload,
    OrderItemPayload,
    OrderItemTypePayload,
    OrderNotePayload,
    PitchPayload,
    PlantingPayload,
    PricePayload,
    ShipperPayload,
    SupplierPayload,
    UnitPayload,
    UnitCategoryPayload,
)


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
        # views cache (multi - table)
        self.inventory_view_cache = None
        self.planting_view_cache = None
        self.label_view_cache = None
        self.order_view_cache = None
        # single table cache
        self.broker_cache = None
        self.item_type_cache = None
        self.unit_category_cache = None
        self.unit_cache = None
        self.shipper_cache = None
        self.supplier_cache = None
        self.growing_season_cache = None
        self.order_item_type_cache = None
        self.order_note_cache = None
        self.item_cache = None
        self.price_cache = None
        self.planting_cache = None
        self.inventory_cache = None
        self.pitch_cache = None
        self.order_cache = None
        self.order_item_cache = None
        # TODO ask about data collection for sales

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

    """ Cache Management """

    def reset_cache(self, target_cache: str, get_method: Callable) -> None:
        """
        Reset a cache by calling the get_method and storing result in the named cache attribute

        Args:
            target_cache: Name of the cache attribute (e.g., "inventory_view_cache")
            get_method: Method to call to populate the cache
        """
        try:
            result = get_method()
            setattr(self, target_cache, result)
            logger.info(f"Successfully cached {target_cache}")
        except Exception as e:
            logger.error(f"Failed to cache data for {target_cache}: {e}")
            setattr(self, target_cache, pd.DataFrame())

    def action_and_cache(
        self, action: Callable, target_cache: str, get_method: Callable
    ) -> None:
        try:
            action()
            self.target_cache = self.reset_cache(
                target_cache=target_cache, get_method=get_method
            )
        except Exception as e:
            print(
                f"error with action and cache function {action}, {target_cache}, {get_method} produce: {e}"
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
                            row_dict[key] = value
                    clean_data.append(row_dict)

                return pd.DataFrame(clean_data)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving records: {e}")
            raise

    def _get_by_id(
        self, model_class, id_column: str, id_value: Any
    ) -> Optional[Dict[str, Any]]:
        """Generic method to get a single record by ID"""
        try:
            with get_db_session() as session:
                result = (
                    session.query(model_class)
                    .filter(getattr(model_class, id_column) == id_value)
                    .first()
                )

                if result:
                    # Convert to dict before session closes to avoid detached instance
                    result_dict = {
                        key: value
                        for key, value in result.__dict__.items()
                        if key != "_sa_instance_state"
                    }
                    logger.info(f"Found record with {id_column}={id_value}")
                    return result_dict
                else:
                    logger.warning(f"No record found with {id_column}={id_value}")
                    return None

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving record: {e}")
            raise

    def _create(self, model_class, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to create a new record with proper type conversion"""
        try:
            from sqlalchemy import Text, String, Integer, Float, Boolean, DateTime

            with get_db_session() as session:
                # Create empty instance
                new_record = model_class()

                for key, value in data.items():
                    if hasattr(new_record, key):
                        column = getattr(model_class, key)
                        column_type = column.property.columns[0].type

                        if value is None:
                            setattr(new_record, key, None)
                        elif isinstance(column_type, (Text, String)):
                            setattr(new_record, key, str(value))
                        elif isinstance(column_type, Integer):
                            setattr(new_record, key, int(value))
                        elif isinstance(column_type, Float):
                            setattr(new_record, key, float(value))
                        elif isinstance(column_type, Boolean):
                            setattr(new_record, key, bool(value))
                        elif isinstance(column_type, DateTime):
                            setattr(new_record, key, value)
                        else:
                            setattr(new_record, key, value)

                session.add(new_record)
                session.commit()
                session.refresh(new_record)

                result_dict = {
                    key: value
                    for key, value in new_record.__dict__.items()
                    if key != "_sa_instance_state"
                }

                logger.info(f"Created new record in {model_class.__tablename__}")
                return result_dict

        except SQLAlchemyError as e:
            logger.error(f"Error creating record: {e}")
            raise

    def _update(
        self, model_class, id_column: str, id_value: Any, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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
                    if hasattr(record, column):
                        setattr(record, column, value)
                    else:
                        logger.warning(
                            f"Column '{column}' does not exist on {model_class.__name__}"
                        )

                session.commit()

                result_dict = {
                    key: value
                    for key, value in record.__dict__.items()
                    if key != "_sa_instance_state"
                }

                logger.info(
                    f"Updated record {id_column}={id_value} in {model_class.__tablename__}"
                )
                return result_dict

        except SQLAlchemyError as e:
            logger.error(f"Error updating record: {e}")
            raise

    def _delete(self, model_class, id_column: str, id_value: Any) -> bool:
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

    def _get_next_id(self, model_class, id_column: str) -> int:
        """Get next available ID for a table"""
        last_id = self._get_all(model_class=model_class)[id_column].max()
        return last_id + 1

    """
    SERVE INVENTORY MANAGEMENT VIEW (GET)
    """

    # GET
    def _get_inventory_view_full(self) -> pd.DataFrame:
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

    def get_inventory_view_display(self) -> pd.DataFrame:
        try:
            plant_list_full = self.inventory_view_cache
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

    """
    SERVE PLANTINGS VIEW (GET)
    """

    # GET
    def _get_plantings_view_full(self) -> pd.DataFrame:
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

    def get_plantings_display(self) -> pd.DataFrame:
        try:
            full = self.planting_view_cache

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

    """
    SERVE LABEL GENERATING VIEW (GET)
    """

    # GET
    def _get_label_view_full(self) -> pd.DataFrame:
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

    def get_label_display(
        self, item_id: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        try:
            label_data_full = self.label_view_cache

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
    SERVE ORDER TRACKING VIEW (GET)
    """

    # GET
    def _get_orders_view_full(self) -> pd.DataFrame:
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

    def get_orders_display(self) -> pd.DataFrame:
        try:
            full_orders = self.order_view_cache
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

    def get_orders_summary(self) -> pd.DataFrame:
        try:
            full_orders = self.order_view_cache
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
            summary = summary.rename(columns={"OrderItemID": "UniqueItems"})
            result = summary.sort_values(by="DatePlaced", ascending=False)
            return result
        except Exception as e:
            logger.error(f"Error getting orders summary: {e}")
            return pd.DataFrame()

    """
    CREATE METHODS (POST)
    """

    """ Inventory """

    def get_inventory_full(self) -> pd.DataFrame:
        """
        Get full inventory data from SQL view
        """
        from models import Inventory

        try:
            result = self._get_all(model_class=Inventory)
            result = result.sort_values(by="DateCounted", ascending=False)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Inventory List: {e}")
            return pd.DataFrame()

    def table_add_inventory(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: float,
        DateCounted: Optional[datetime] = None,
        InventoryComments: Optional[str] = None,
    ) -> None:
        """Add new inventory record"""
        try:
            p: InventoryPayload = {
                "InventoryID": self._get_next_id(Inventory, "InventoryID"),
                "ItemID": ItemID,
                "UnitID": UnitID,
                "NumberOfUnits": str(NumberOfUnits),
                "DateCounted": DateCounted or datetime.now(),
                "InventoryComments": InventoryComments,
            }
            result = self._create(model_class=Inventory, data=p)
            logger.info(f"Added inventory record {result['InventoryID']}")
        except Exception as e:
            logger.error(f"Error adding inventory: {e}")
            raise

    """ Brokers """

    def get_broker_full(self) -> pd.DataFrame:
        """
        Get full brokers data
        """
        from models import Broker

        try:
            result = self._get_all(model_class=Broker)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Brokers List: {e}")
            return pd.DataFrame()

    def table_add_broker(
        self, BrokerName: str, BrokerComments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add new broker record"""
        try:
            p: BrokerPayload = {
                "BrokerID": self._get_next_id(Broker, "BrokerID"),
                "Broker": BrokerName,
                "BrokerComments": BrokerComments,
            }
            result = self._create(model_class=Broker, data=p)
            logger.info(f"Added broker record {result['BrokerID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding broker: {e}")
            raise

    """ GrowingSeason """

    def get_growing_season_full(self) -> pd.DataFrame:
        """
        Get full growing season data
        """
        from models import GrowingSeason

        try:
            result = self._get_all(model_class=GrowingSeason)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Growing Season List: {e}")
            return pd.DataFrame()

    def table_add_growing_season(
        self,
        GrowingSeasonYear: str,
        StartDate: datetime,
        EndDate: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Add new growing season record"""
        try:
            p: GrowingSeasonPayload = {
                "GrowingSeasonID": self._get_next_id(GrowingSeason, "GrowingSeasonID"),
                "GrowingSeason": GrowingSeasonYear,
                "StartDate": StartDate,
                "EndDate": EndDate,
            }
            result = self._create(model_class=GrowingSeason, data=p)
            logger.info(f"Added growing season record {result['GrowingSeasonID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding growing season: {e}")
            raise

    """ Items """

    def get_item_full(self) -> pd.DataFrame:
        """
        Get full items data
        """
        from models import Item

        try:
            result = self._get_all(model_class=Item)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Items List: {e}")
            return pd.DataFrame()

    def table_add_item(
        self,
        Item: str,
        TypeID: int,
        Variety: Optional[str] = None,
        Color: Optional[str] = None,
        Inactive: bool = False,
        ShouldStock: bool = False,
        LabelDescription: Optional[str] = None,
        Definition: Optional[str] = None,
        PictureLayout: Optional[str] = None,
        PictureLink: Optional[str] = None,
        SunConditions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new item record"""
        try:
            from models import (
                Item as ItemModel,
            )

            p: ItemPayload = {
                "ItemID": self._get_next_id(
                    ItemModel, "ItemID"
                ),  # Use ItemModel class, not Item string
                "Item": Item,  # This is the string "Test" from the form
                "TypeID": TypeID,
                "Variety": Variety,
                "Color": Color,
                "Inactive": Inactive,
                "ShouldStock": ShouldStock,
                "LabelDescription": LabelDescription,
                "Definition": Definition,
                "PictureLayout": PictureLayout,
                "PictureLink": PictureLink,
                "SunConditions": SunConditions,
            }
            result = self._create(
                model_class=ItemModel, data=p
            )  # Use ItemModel here too
            logger.info(f"Added item record {result['ItemID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            raise

    """ ItemType """

    def get_item_type_full(self) -> pd.DataFrame:
        """
        Get full item type data
        """
        from models import ItemType

        try:
            result = self._get_all(model_class=ItemType)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Item Type List: {e}")
            return pd.DataFrame()

    def table_add_item_type(self, Type: str) -> Dict[str, Any]:
        """Add new item type record"""
        try:
            p: ItemTypePayload = {
                "TypeID": self._get_next_id(ItemType, "TypeID"),
                "Type": Type,
            }
            result = self._create(model_class=ItemType, data=p)
            logger.info(f"Added item type record {result['TypeID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding item type: {e}")
            raise

    """ Orders """

    def get_order_full(self) -> pd.DataFrame:
        """
        Get full orders data
        """
        from models import Order

        try:
            result = self._get_all(model_class=Order)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Orders List: {e}")
            return pd.DataFrame()

    def table_add_order(
        self,
        SupplierID: int,
        DateDue: datetime,
        GrowingSeasonID: Optional[int] = None,
        DatePlaced: Optional[datetime] = None,
        DateReceived: Optional[datetime] = None,
        OrderNumber: Optional[str] = None,
        ShipperID: Optional[int] = None,
        TrackingNumber: Optional[str] = None,
        OrderComments: Optional[str] = None,
        TotalCost: Optional[float] = None,
        GrowingSeason: Optional[str] = None,
        BrokerID: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add new order record"""
        try:
            p: OrderPayload = {
                "OrderID": self._get_next_id(Order, "OrderID"),
                "GrowingSeasonID": GrowingSeasonID,
                "DatePlaced": DatePlaced or datetime.now(),
                "DateDue": DateDue,
                "DateReceived": DateReceived,
                "SupplierID": SupplierID,
                "OrderNumber": OrderNumber,
                "ShipperID": ShipperID,
                "TrackingNumber": TrackingNumber,
                "OrderComments": OrderComments,
                "TotalCost": TotalCost,
                "GrowingSeason": GrowingSeason,
                "BrokerID": BrokerID,
            }
            result = self._create(model_class=Order, data=p)
            logger.info(f"Added order record {result['OrderID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order: {e}")
            raise

    """ OrderItems """

    def get_order_item_full(self) -> pd.DataFrame:
        """
        Get full order items data
        """
        from models import OrderItem

        try:
            result = self._get_all(model_class=OrderItem)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Order Items List: {e}")
            return pd.DataFrame()

    def table_add_order_item(
        self,
        OrderID: int,
        ItemID: int,
        NumberOfUnits: str,
        ItemCode: Optional[str] = None,
        OrderItemTypeID: Optional[int] = None,
        Unit: Optional[str] = None,
        UnitPrice: Optional[float] = None,
        Received: bool = False,
        OrderNote: Optional[int] = None,
        OrderComments: Optional[str] = None,
        Leftover: Optional[str] = None,
        ToOrder: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new order item record"""
        try:
            p: OrderItemPayload = {
                "OrderItemID": self._get_next_id(OrderItem, "OrderItemID"),
                "OrderID": OrderID,
                "ItemID": ItemID,
                "ItemCode": ItemCode,
                "OrderItemTypeID": OrderItemTypeID,
                "Unit": Unit,
                "UnitPrice": UnitPrice,
                "NumberOfUnits": NumberOfUnits,
                "Received": Received,
                "OrderNote": OrderNote,
                "OrderComments": OrderComments,
                "Leftover": Leftover,
                "ToOrder": ToOrder,
            }
            result = self._create(model_class=OrderItem, data=p)
            logger.info(f"Added order item record {result['OrderItemID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order item: {e}")
            raise

    """ OrderItemTypes """

    def get_order_item_type_full(self) -> pd.DataFrame:
        """
        Get full order item type data
        """
        from models import OrderItemType

        try:
            result = self._get_all(model_class=OrderItemType)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Order Item Type List: {e}")
            return pd.DataFrame()

    def table_add_order_item_type(self, OrderItemType: str) -> Dict[str, Any]:
        """Add new order item type record"""
        try:
            p: OrderItemTypePayload = {
                "OrderItemTypeID": self._get_next_id(OrderItemType, "OrderItemTypeID"),
                "OrderItemType": OrderItemType,
            }
            result = self._create(model_class=OrderItemType, data=p)
            logger.info(f"Added order item type record {result['OrderItemTypeID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order item type: {e}")
            raise

    """ OrderNotes """

    def get_order_note_full(self) -> pd.DataFrame:
        """
        Get full order notes data
        """
        from models import OrderNote

        try:
            result = self._get_all(model_class=OrderNote)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Order Notes List: {e}")
            return pd.DataFrame()

    def table_add_order_note(self, OrderNote: str) -> Dict[str, Any]:
        """Add new order note record"""
        try:
            p: OrderNotePayload = {
                "OrderNoteID": self._get_next_id(OrderNote, "OrderNoteID"),
                "OrderNote": OrderNote,
            }
            result = self._create(model_class=OrderNote, data=p)
            logger.info(f"Added order note record {result['OrderNoteID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order note: {e}")
            raise

    """ Pitch """

    def get_pitch_full(self) -> pd.DataFrame:
        """
        Get full pitch data
        """
        from models import Pitch

        try:
            result = self._get_all(model_class=Pitch)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Pitch List: {e}")
            return pd.DataFrame()

    def table_add_pitch(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DatePitched: Optional[datetime] = None,
        PitchComments: Optional[str] = None,
        PitchReason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new pitch record"""
        try:
            p: PitchPayload = {
                "PitchID": self._get_next_id(Pitch, "PitchID"),
                "DatePitched": DatePitched or datetime.now(),
                "ItemID": ItemID,
                "UnitID": UnitID,
                "NumberOfUnits": NumberOfUnits,
                "PitchComments": PitchComments,
                "PitchReason": PitchReason,
            }
            result = self._create(model_class=Pitch, data=p)
            logger.info(f"Added pitch record {result['PitchID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding pitch: {e}")
            raise

    """ Plantings """

    def get_planting_full(self) -> pd.DataFrame:
        """
        Get full plantings data
        """
        from models import Planting

        try:
            result = self._get_all(model_class=Planting)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Plantings List: {e}")
            return pd.DataFrame()

    def table_add_planting(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DatePlanted: Optional[datetime] = None,
        PlantingComments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new planting record"""
        try:
            p: PlantingPayload = {
                "PlantingID": self._get_next_id(Planting, "PlantingID"),
                "DatePlanted": DatePlanted or datetime.now(),
                "ItemID": ItemID,
                "UnitID": UnitID,
                "NumberOfUnits": NumberOfUnits,
                "PlantingComments": PlantingComments,
            }
            result = self._create(model_class=Planting, data=p)
            logger.info(f"Added planting record {result['PlantingID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding planting: {e}")
            raise

    """ Prices """

    def get_price_full(self) -> pd.DataFrame:
        """
        Get full prices data
        """
        from models import Price

        try:
            result = self._get_all(model_class=Price)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Prices List: {e}")
            return pd.DataFrame()

    def table_add_price(
        self,
        ItemID: int,
        UnitID: int,
        UnitPrice: float,
        Year: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new price record"""
        try:
            p: PricePayload = {
                "PriceID": self._get_next_id(Price, "PriceID"),
                "ItemID": ItemID,
                "UnitID": UnitID,
                "UnitPrice": UnitPrice,
                "Year": Year,
            }
            result = self._create(model_class=Price, data=p)
            logger.info(f"Added price record {result['PriceID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding price: {e}")
            raise

    """ Shippers """

    def get_shipper_full(self) -> pd.DataFrame:
        """
        Get full shippers data
        """
        from models import Shipper

        try:
            result = self._get_all(model_class=Shipper)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Shippers List: {e}")
            return pd.DataFrame()

    def table_add_shipper(
        self,
        Shipper: str,
        AccountNumber: Optional[str] = None,
        Phone: Optional[str] = None,
        ContactPerson: Optional[str] = None,
        Address1: Optional[str] = None,
        Address2: Optional[str] = None,
        City: Optional[str] = None,
        State: Optional[str] = None,
        Zip: Optional[str] = None,
        ShipperComments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new shipper record"""
        try:
            p: ShipperPayload = {
                "ShipperID": self._get_next_id(Shipper, "ShipperID"),
                "Shipper": Shipper,
                "AccountNumber": AccountNumber,
                "Phone": Phone,
                "ContactPerson": ContactPerson,
                "Address1": Address1,
                "Address2": Address2,
                "City": City,
                "State": State,
                "Zip": Zip,
                "ShipperComments": ShipperComments,
            }
            result = self._create(model_class=Shipper, data=p)
            logger.info(f"Added shipper record {result['ShipperID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding shipper: {e}")
            raise

    """ Suppliers """

    def get_supplier_full(self) -> pd.DataFrame:
        """
        Get full suppliers data
        """
        from models import Supplier

        try:
            result = self._get_all(model_class=Supplier)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Suppliers List: {e}")
            return pd.DataFrame()

    def table_add_supplier(
        self,
        Supplier: str,
        AccountNumber: Optional[str] = None,
        Phone: Optional[str] = None,
        Fax: Optional[str] = None,
        WebSite: Optional[str] = None,
        Email: Optional[str] = None,
        ContactPerson: Optional[str] = None,
        Address1: Optional[str] = None,
        Address2: Optional[str] = None,
        City: Optional[str] = None,
        State: Optional[str] = None,
        Zip: Optional[str] = None,
        SupplierComments: Optional[str] = None,
        SupplierType: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new supplier record"""
        try:
            p: SupplierPayload = {
                "SupplierID": self._get_next_id(Supplier, "SupplierID"),
                "Supplier": Supplier,
                "AccountNumber": AccountNumber,
                "Phone": Phone,
                "Fax": Fax,
                "WebSite": WebSite,
                "Email": Email,
                "ContactPerson": ContactPerson,
                "Address1": Address1,
                "Address2": Address2,
                "City": City,
                "State": State,
                "Zip": Zip,
                "SupplierComments": SupplierComments,
                "SupplierType": SupplierType,
            }
            result = self._create(model_class=Supplier, data=p)
            logger.info(f"Added supplier record {result['SupplierID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding supplier: {e}")
            raise

    """ UnitCategory """

    def get_unit_category_full(self) -> pd.DataFrame:
        """
        Get full unit category data
        """
        from models import UnitCategory

        try:
            result = self._get_all(model_class=UnitCategory)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Unit Category List: {e}")
            return pd.DataFrame()

    def table_add_unit_category(self, UnitCategory: str) -> Dict[str, Any]:
        """Add new unit category record"""
        try:
            p: UnitCategoryPayload = {
                "UnitCategoryID": self._get_next_id(UnitCategory, "UnitCategoryID"),
                "UnitCategory": UnitCategory,
            }
            result = self._create(model_class=UnitCategory, data=p)
            logger.info(f"Added unit category record {result['UnitCategoryID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding unit category: {e}")
            raise

    """ Units """

    def get_unit_full(self) -> pd.DataFrame:
        """
        Get full units data
        """
        from models import Unit

        try:
            result = self._get_all(model_class=Unit)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Units List: {e}")
            return pd.DataFrame()

    def table_add_unit(
        self,
        UnitType: str,
        UnitSize: str,
        UnitCategoryID: int,
    ) -> Dict[str, Any]:
        """Add new unit record"""
        try:
            p: UnitPayload = {
                "UnitID": self._get_next_id(Unit, "UnitID"),
                "UnitType": UnitType,
                "UnitSize": UnitSize,
                "UnitCategoryID": UnitCategoryID,
            }
            result = self._create(model_class=Unit, data=p)
            logger.info(f"Added unit record {result['UnitID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding unit: {e}")
            raise

    """
    Updating Routing
    """

    def generic_update(
        self,
        model_class,
        id_column: str,
        id_value: Any,
        updates: Dict[str, Any],
        allowed_fields: Optional[Set[str]] = None,
        preprocessors: Optional[Dict[str, Callable]] = None,
        strict: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Generic update with field filtering and preprocessing

        Filters updates to only allowed fields (for view->table editing),
        then applies preprocessing, then updates the base table.

        Args:
            model_class: Model class to update (base table, not view)
            id_column: Name of ID column
            id_value: Value of ID to update
            updates: Dict of fields to update (may include read-only view fields)
            allowed_fields: Set of column names that can be updated (None = allow all)
            preprocessors: Dict mapping column names to preprocessing functions
            strict: If True, raise error on disallowed fields. If False, just filter them out.

        Returns:
            Updated record dict or None if not found
        """
        try:
            existing = self._get_by_id(model_class, id_column, id_value)
            if not existing:
                logger.warning(f"Record not found: {id_column}={id_value}")
                return None

            filtered_updates = {}
            rejected_fields = []

            for column, value in updates.items():
                if allowed_fields is not None and column not in allowed_fields:
                    rejected_fields.append(column)
                    if strict:
                        raise ValueError(
                            f"Cannot update field '{column}' - it's read-only or from a joined table"
                        )
                    continue

                filtered_updates[column] = value

            if rejected_fields:
                logger.warning(f"Filtered out read-only fields: {rejected_fields}")

            if not filtered_updates:
                logger.warning("No valid fields to update after filtering")
                return existing

            processed_updates = {}
            for column, value in filtered_updates.items():
                if preprocessors and column in preprocessors:
                    try:
                        processed_value = preprocessors[column](value)
                        processed_updates[column] = processed_value
                        logger.debug(
                            f"Preprocessed {column}: {value} -> {processed_value}"
                        )
                    except Exception as e:
                        logger.error(f"Error preprocessing {column}: {e}")
                        raise ValueError(f"Invalid value for {column}: {value}")
                else:
                    processed_updates[column] = value

            result = self._update(
                model_class=model_class,
                id_column=id_column,
                id_value=id_value,
                updates=processed_updates,
            )
            return result
        except Exception as e:
            logger.exception(e)
            print(f"failed with updates {updates}, available fields: {allowed_fields}")
            return result
