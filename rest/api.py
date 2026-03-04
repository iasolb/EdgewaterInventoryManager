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
    OrderItemDestination,
    Users,
    Location,
    SeasonalNotes,
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
    OrderItemDestinationPayload,
    SeasonalNotesPayload,
    UserPayload,
    LocationPayload,
)


class EdgewaterAPI:
    """Class to interact with Edgewater API"""

    def __init__(self, *args, **kwds):
        """
        Constructor for EdgewaterAPI
        """
        # Path configuration
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

    """ Cache Management - Two-tier system
    
    Tier 1: Lookup tables (@st.cache_data with TTL)
        Small, rarely-changing reference data (items, units, types, locations, etc.)
        Auto-expires after TTL, shared across sessions.
        
    Tier 2: View caches (st.session_state)
        Large view data (inventory, plantings, orders). Loaded once per session,
        explicit refresh via refresh button. Pages derive filtered working sets
        from these.
    """

    # ===== TIER 1: CACHED LOOKUP LOADERS =====
    # These are static methods using @st.cache_data so they persist across reruns
    # and are shared across sessions. TTL ensures they refresh periodically.

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_items():
        from models import Item
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Item).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} items (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_item_types():
        from models import ItemType
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(ItemType).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} item types (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading item types: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_units():
        from models import Unit
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Unit).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} units (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading units: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_unit_categories():
        from models import UnitCategory
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(UnitCategory).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} unit categories (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading unit categories: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_locations():
        from models import Location
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Location).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} locations (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading locations: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_suppliers():
        from models import Supplier
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Supplier).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} suppliers (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading suppliers: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_shippers():
        from models import Shipper
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Shipper).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} shippers (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading shippers: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_brokers():
        from models import Broker
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(Broker).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} brokers (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading brokers: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_growing_seasons():
        from models import GrowingSeason
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(GrowingSeason).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                logger.info(f"Loaded {len(data)} growing seasons (cached)")
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading growing seasons: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_order_item_types():
        from models import OrderItemType
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(OrderItemType).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading order item types: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def _load_order_notes():
        from models import OrderNote
        from database import get_db_session

        try:
            with get_db_session() as session:
                results = session.query(OrderNote).all()
                data = [
                    {k: v for k, v in r.__dict__.items() if k != "_sa_instance_state"}
                    for r in results
                ]
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading order notes: {e}")
            return pd.DataFrame()

    # ===== TIER 1: PROPERTY ACCESSORS =====
    # Pages use these just like before: api.item_cache, api.unit_cache, etc.
    # But now they hit @st.cache_data instead of instance attributes.

    @property
    def item_cache(self):
        return EdgewaterAPI._load_items()

    @property
    def item_type_cache(self):
        return EdgewaterAPI._load_item_types()

    @property
    def unit_cache(self):
        return EdgewaterAPI._load_units()

    @property
    def unit_category_cache(self):
        return EdgewaterAPI._load_unit_categories()

    @property
    def location_cache(self):
        return EdgewaterAPI._load_locations()

    @property
    def supplier_cache(self):
        return EdgewaterAPI._load_suppliers()

    @property
    def shipper_cache(self):
        return EdgewaterAPI._load_shippers()

    @property
    def broker_cache(self):
        return EdgewaterAPI._load_brokers()

    @property
    def growing_season_cache(self):
        return EdgewaterAPI._load_growing_seasons()

    @property
    def order_item_type_cache(self):
        return EdgewaterAPI._load_order_item_types()

    @property
    def order_note_cache(self):
        return EdgewaterAPI._load_order_notes()

    # ===== TIER 2: SESSION-STATE VIEW CACHES =====
    # Large view data stored in st.session_state, loaded once per session.

    def _get_session_cache(self, key: str, loader: Callable) -> pd.DataFrame:
        """Get a view cache from session_state, loading if not present"""
        if key not in st.session_state or st.session_state[key] is None:
            try:
                result = loader()
                st.session_state[key] = result
                logger.info(f"Loaded {key} into session_state ({len(result)} rows)")
            except Exception as e:
                logger.error(f"Failed to load {key}: {e}")
                st.session_state[key] = pd.DataFrame()
        return st.session_state[key]

    def _refresh_session_cache(self, key: str, loader: Callable) -> pd.DataFrame:
        """Force refresh a view cache in session_state"""
        try:
            result = loader()
            st.session_state[key] = result
            logger.info(f"Refreshed {key} ({len(result)} rows)")
            return result
        except Exception as e:
            logger.error(f"Failed to refresh {key}: {e}")
            st.session_state[key] = pd.DataFrame()
            return pd.DataFrame()

    @property
    def inventory_view_cache(self):
        return self._get_session_cache("_inv_view", self.get_inventory_view_full)

    @property
    def planting_view_cache(self):
        return self._get_session_cache("_plant_view", self.get_plantings_view_full)

    @property
    def order_view_cache(self):
        return self._get_session_cache("_order_view", self.get_orders_view_full)

    @property
    def label_view_cache(self):
        return self._get_session_cache("_label_view", self.get_label_view_full)

    @property
    def pitch_view_cache(self):
        return self._get_session_cache("_pitch_view", self.get_pitch_view)

    # ===== TIER 2: SESSION-STATE SINGLE-TABLE CACHES (admin pages) =====
    # These are the raw table caches for large tables that admin pages use directly.

    @property
    def inventory_cache(self):
        return self._get_session_cache("_inv_table", self.get_inventory_full)

    @property
    def planting_cache(self):
        return self._get_session_cache("_plant_table", self.get_planting_full)

    @property
    def pitch_cache(self):
        return self._get_session_cache("_pitch_table", self.get_pitch_full)

    @property
    def order_cache(self):
        return self._get_session_cache("_order_table", self.get_order_full)

    @property
    def order_item_cache(self):
        return self._get_session_cache("_order_item_table", self.get_order_item_full)

    @property
    def price_cache(self):
        return self._get_session_cache("_price_table", self.get_price_full)

    @property
    def seasonal_notes_cache(self):
        return self._get_session_cache(
            "_seasonal_notes_table", self.get_seasonal_notes_full
        )

    @property
    def order_item_destination_cache(self):
        return self._get_session_cache(
            "_oid_table", self.get_order_item_destination_full
        )

    @property
    def user_cache(self):
        return self._get_session_cache("_user_table", self.get_user_full)

    def refresh_view_cache(self, view_name: str) -> None:
        """Refresh a specific view or table cache. Call from page refresh buttons.

        Args:
            view_name: One of 'inventory', 'plantings', 'orders', 'labels', 'pitch',
                       'inventory_table', 'planting_table', 'pitch_table', 'order_table',
                       'order_item_table', 'price_table', 'seasonal_notes_table',
                       'oid_table', 'user_table', 'all'
        """
        view_map = {
            "inventory": ("_inv_view", self.get_inventory_view_full),
            "plantings": ("_plant_view", self.get_plantings_view_full),
            "orders": ("_order_view", self.get_orders_view_full),
            "labels": ("_label_view", self.get_label_view_full),
            "pitch": ("_pitch_view", self.get_pitch_view),
            "inventory_table": ("_inv_table", self.get_inventory_full),
            "planting_table": ("_plant_table", self.get_planting_full),
            "pitch_table": ("_pitch_table", self.get_pitch_full),
            "order_table": ("_order_table", self.get_order_full),
            "order_item_table": ("_order_item_table", self.get_order_item_full),
            "price_table": ("_price_table", self.get_price_full),
            "seasonal_notes_table": (
                "_seasonal_notes_table",
                self.get_seasonal_notes_full,
            ),
            "oid_table": ("_oid_table", self.get_order_item_destination_full),
            "user_table": ("_user_table", self.get_user_full),
        }
        if view_name == "all":
            for key, loader in view_map.values():
                self._refresh_session_cache(key, loader)
        elif view_name in view_map:
            key, loader = view_map[view_name]
            self._refresh_session_cache(key, loader)
        else:
            logger.warning(f"Unknown view cache: {view_name}")

    @staticmethod
    def clear_lookup_caches():
        """Force clear all @st.cache_data lookup caches"""
        EdgewaterAPI._load_items.clear()
        EdgewaterAPI._load_item_types.clear()
        EdgewaterAPI._load_units.clear()
        EdgewaterAPI._load_unit_categories.clear()
        EdgewaterAPI._load_locations.clear()
        EdgewaterAPI._load_suppliers.clear()
        EdgewaterAPI._load_shippers.clear()
        EdgewaterAPI._load_brokers.clear()
        EdgewaterAPI._load_growing_seasons.clear()
        EdgewaterAPI._load_order_item_types.clear()
        EdgewaterAPI._load_order_notes.clear()
        logger.info("All lookup caches cleared")

    # ===== TIER 2.5: FILTERED WORKING SETS =====
    # Pages store their filtered subset in session_state so card expansions
    # only search the filtered data, not the full view.

    @staticmethod
    def set_working_set(page_key: str, df: pd.DataFrame) -> None:
        """Store a filtered working set for a page"""
        st.session_state[f"_working_{page_key}"] = df

    @staticmethod
    def get_working_set(page_key: str) -> Optional[pd.DataFrame]:
        """Get the filtered working set for a page"""
        return st.session_state.get(f"_working_{page_key}")

    # Legacy compatibility — reset_cache still works but pages should migrate
    def reset_cache(self, target_cache: str, get_method: Callable) -> None:
        """
        Legacy cache reset. For view caches, use refresh_view_cache() instead.
        For lookup caches, they auto-refresh via TTL.
        """
        try:
            result = get_method()
            setattr(self, f"_{target_cache}", result)
            logger.info(f"Successfully cached {target_cache} (legacy)")
        except Exception as e:
            logger.error(f"Failed to cache data for {target_cache}: {e}")
            setattr(self, f"_{target_cache}", pd.DataFrame())

    def action_and_cache(
        self, action: Callable, target_cache: str, get_method: Callable
    ) -> None:
        """Execute an action then refresh the relevant cache"""
        try:
            action()
            self.reset_cache(target_cache=target_cache, get_method=get_method)
        except Exception as e:
            print(
                f"error with action and cache function {action}, {target_cache}, {get_method} produce: {e}"
            )

    # ==================== GENERIC CRUD ====================

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
    Individual Table cache fillers (GET)
    """

    # ========= GET =========
    def df_get_by_id(cache_data: pd.DataFrame, id_column: str, id: int) -> pd.DataFrame:
        return cache_data[cache_data[id_column] == id].copy()

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

    def get_location_full(self) -> pd.DataFrame:
        """
        Get full location data
        """
        from models import Location

        try:
            result = self._get_all(model_class=Location)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Location List: {e}")
            return pd.DataFrame()

    def get_user_full(self) -> pd.DataFrame:
        """
        Get full users data
        """
        from models import Users

        try:
            result = self._get_all(model_class=Users)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Users List: {e}")
            return pd.DataFrame()

    def get_seasonal_notes_full(self) -> pd.DataFrame:
        """
        Get full seasonal notes data
        """
        from models import SeasonalNotes

        try:
            result = self._get_all(model_class=SeasonalNotes)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Seasonal Notes List: {e}")
            return pd.DataFrame()

    def get_order_item_destination_full(self) -> pd.DataFrame:
        """
        Get full order item destination data
        """
        from models import OrderItemDestination

        try:
            result = self._get_all(model_class=OrderItemDestination)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Order Item Destination List: {e}")
            return pd.DataFrame()

    """
    Multi Table cache fillers (GET, views)
    """

    def get_inventory_view_full(self) -> pd.DataFrame:
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

    def get_plantings_view_full(self) -> pd.DataFrame:
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

    def get_orders_view_full(self) -> pd.DataFrame:
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

    def get_label_view_full(self) -> pd.DataFrame:
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

    def get_pitch_view(self) -> pd.DataFrame:
        """
        Get full pitch from SQL view
        """
        from models import PitchFullView

        try:
            result = self._get_all(model_class=PitchFullView)
            return result
        except Exception as e:
            logger.error(f"Error retrieving Label Data: {e}")
            return pd.DataFrame()

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

    # =========== MAJOR WORKFLOW METHODS =============
    """
    Serving Inventory Manager

    - data routing from view
    - permission checks
    - routes edits to appropriate admin-level action
    """

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
    Serving Plantings Tracker

    - data routing from view
    - permission checks
    - routes edits to appropriate admin-level action
    """

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
    Serving Label Generation:

    - data routing from view
    - permission checks
    - routes edits to appropriate admin-level action
    """

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
    Serving Order Tracker

    - data routing from view
    - permission checks
    - routes edits to appropriate admin-level action
    """

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
    Admin Level Actions (POST, UPDATE, DELETE) 
    """

    # ========== POST ========
    def table_add_inventory(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: float,
        DateCounted: Optional[datetime] = None,
        InventoryComments: Optional[str] = None,
        LocationID: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add new inventory record"""
        try:
            p: InventoryPayload = {
                "InventoryID": self._get_next_id(Inventory, "InventoryID"),
                "ItemID": ItemID,
                "UnitID": UnitID,
                "NumberOfUnits": str(NumberOfUnits),
                "DateCounted": DateCounted or datetime.now(),
                "InventoryComments": InventoryComments,
                "LocationID": LocationID,
            }
            result = self._create(model_class=Inventory, data=p)
            logger.info(f"Added inventory record {result['InventoryID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding inventory: {e}")
            raise

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

    def table_add_order_item_type(self, OrderItemTypeName: str) -> Dict[str, Any]:
        """Add new order item type record"""
        try:
            from models import OrderItemType as OIT

            p: OrderItemTypePayload = {
                "OrderItemTypeID": self._get_next_id(OIT, "OrderItemTypeID"),
                "OrderItemType": OrderItemTypeName,
            }
            result = self._create(model_class=OIT, data=p)
            logger.info(f"Added order item type record {result['OrderItemTypeID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order item type: {e}")
            raise

    def table_add_order_note(self, OrderNoteText: str) -> Dict[str, Any]:
        """Add new order note record"""
        try:
            from models import OrderNote as ON

            p: OrderNotePayload = {
                "OrderNoteID": self._get_next_id(ON, "OrderNoteID"),
                "OrderNote": OrderNoteText,
            }
            result = self._create(model_class=ON, data=p)
            logger.info(f"Added order note record {result['OrderNoteID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding order note: {e}")
            raise

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

    def table_add_planting(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DatePlanted: Optional[datetime] = None,
        PlantingComments: Optional[str] = None,
        LocationID: Optional[int] = None,
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
                "LocationID": LocationID,
            }
            result = self._create(model_class=Planting, data=p)
            logger.info(f"Added planting record {result['PlantingID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding planting: {e}")
            raise

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

    def table_add_shipper(
        self,
        ShipperName: str,
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
            from models import Shipper as SHP

            p: ShipperPayload = {
                "ShipperID": self._get_next_id(SHP, "ShipperID"),
                "Shipper": ShipperName,
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
            result = self._create(model_class=SHP, data=p)
            logger.info(f"Added shipper record {result['ShipperID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding shipper: {e}")
            raise

    def table_add_supplier(
        self,
        SupplierName: str,
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
            from models import Supplier as SUP

            p: SupplierPayload = {
                "SupplierID": self._get_next_id(SUP, "SupplierID"),
                "Supplier": SupplierName,
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
            result = self._create(model_class=SUP, data=p)
            logger.info(f"Added supplier record {result['SupplierID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding supplier: {e}")
            raise

    def table_add_unit_category(self, UnitCategoryName: str) -> Dict[str, Any]:
        """Add new unit category record"""
        try:
            from models import UnitCategory as UC

            p: UnitCategoryPayload = {
                "UnitCategoryID": self._get_next_id(UC, "UnitCategoryID"),
                "UnitCategory": UnitCategoryName,
            }
            result = self._create(model_class=UC, data=p)
            logger.info(f"Added unit category record {result['UnitCategoryID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding unit category: {e}")
            raise

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

    def table_add_location(self, Location: str) -> Dict[str, Any]:
        """Add new location record"""
        try:
            from models import Location as LOC
            from payloads import LocationPayload

            p: LocationPayload = {
                "LocationID": self._get_next_id(LOC, "LocationID"),
                "Location": Location,
            }
            result = self._create(model_class=LOC, data=p)
            logger.info(f"Added location record {result['LocationID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding location: {e}")
            raise

    def table_add_user(
        self,
        Role: str,
        Email: str,
        PermissionLevel: Optional[str] = None,
        Active: bool = True,
    ) -> Dict[str, Any]:
        """Add new user record"""
        try:
            from models import Users
            from payloads import UserPayload

            p: UserPayload = {
                "UserID": self._get_next_id(Users, "UserID"),
                "Role": Role,
                "PermissionLevel": PermissionLevel,
                "Email": Email,
                "Active": 1 if Active else 0,
                "CreatedAt": datetime.now(),
                "UpdatedAt": datetime.now(),
            }
            result = self._create(model_class=Users, data=p)
            logger.info(f"Added user record {result['UserID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            raise

    def table_add_seasonal_note(
        self,
        ItemID: int,
        GrowingSeasonID: int,
        Greenhouse: int,
        Note: str,
        LastUpdate: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Add new seasonal note record"""
        try:
            from models import SeasonalNotes
            from payloads import SeasonalNotesPayload

            p: SeasonalNotesPayload = {
                "NoteID": self._get_next_id(SeasonalNotes, "NoteID"),
                "ItemID": ItemID,
                "GrowingSeasonID": GrowingSeasonID,
                "Greenhouse": Greenhouse,
                "Note": Note,
                "LastUpdate": LastUpdate or datetime.now(),
            }
            result = self._create(model_class=SeasonalNotes, data=p)
            logger.info(f"Added seasonal note record {result['NoteID']}")
            return result
        except Exception as e:
            logger.error(f"Error adding seasonal note: {e}")
            raise

    def table_add_order_item_destination(
        self,
        OrderItemID: int,
        Count: int,
        UnitID: int,
        LocationID: int,
    ) -> Dict[str, Any]:
        """Add new order item destination record"""
        try:
            from models import OrderItemDestination
            from payloads import OrderItemDestinationPayload

            p: OrderItemDestinationPayload = {
                "OrderItemDestinationID": self._get_next_id(
                    OrderItemDestination, "OrderItemDestinationID"
                ),
                "OrderItemID": OrderItemID,
                "Count": Count,
                "UnitID": UnitID,
                "LocationID": LocationID,
            }
            result = self._create(model_class=OrderItemDestination, data=p)
            logger.info(
                f"Added order item destination record {result['OrderItemDestinationID']}"
            )
            return result
        except Exception as e:
            logger.error(f"Error adding order item destination: {e}")
            raise

    # ========== UPDATE ========

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
