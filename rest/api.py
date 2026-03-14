"""
Edgewater Farm API for Inventory Management System
Author: Ian Solberg
Date: 10-16-2025

Refactored: Consolidated duplicate loader/getter/add patterns into generic helpers.
All public endpoints (properties, methods, signatures) are preserved.
"""

import base64
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Text,
    Tuple,
    TypedDict,
)

import pandas as pd
import streamlit as st
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from database import get_db_session
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


# ============================================================
# Helper: SQLAlchemy row -> dict
# ============================================================


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a SQLAlchemy model instance to a plain dict, stripping internal state."""
    return {k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"}


def _rows_to_dataframe(rows) -> pd.DataFrame:
    """Convert a list of SQLAlchemy model instances to a DataFrame."""
    return pd.DataFrame([_row_to_dict(r) for r in rows])


# ============================================================
# Helper: Generic cached table loader (used by @st.cache_data stubs)
# ============================================================


def _load_table(model_class, label: str) -> pd.DataFrame:
    """
    Shared implementation for all Tier-1 cached loaders.
    Each @st.cache_data stub delegates here so Streamlit still sees
    distinct function identities for cache keying.
    """
    try:
        with get_db_session() as session:
            results = session.query(model_class).all()
            df = _rows_to_dataframe(results)
            logger.info(f"Loaded {len(df)} {label} (cached)")
            return df
    except Exception as e:
        logger.error(f"Error loading {label}: {e}")
        return pd.DataFrame()


# ============================================================
# Tier 1: Cached lookup loaders
# ============================================================
# Each must be a distinct function so @st.cache_data keys them separately.
# They are module-level statics; the class exposes them via properties.


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_items():
    return _load_table(Item, "items")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_item_types():
    return _load_table(ItemType, "item types")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_units():
    return _load_table(Unit, "units")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_unit_categories():
    return _load_table(UnitCategory, "unit categories")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_locations():
    return _load_table(Location, "locations")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_suppliers():
    return _load_table(Supplier, "suppliers")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_shippers():
    return _load_table(Shipper, "shippers")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_brokers():
    return _load_table(Broker, "brokers")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_growing_seasons():
    return _load_table(GrowingSeason, "growing seasons")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_order_item_types():
    return _load_table(OrderItemType, "order item types")


@st.cache_data(ttl=600, show_spinner=False)
def _cached_load_order_notes():
    return _load_table(OrderNote, "order notes")


# Lookup for programmatic cache-clearing
_CACHED_LOADERS = [
    _cached_load_items,
    _cached_load_item_types,
    _cached_load_units,
    _cached_load_unit_categories,
    _cached_load_locations,
    _cached_load_suppliers,
    _cached_load_shippers,
    _cached_load_brokers,
    _cached_load_growing_seasons,
    _cached_load_order_item_types,
    _cached_load_order_notes,
]


class EdgewaterAPI:
    """Class to interact with Edgewater API"""

    def __init__(self):
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

    # ================================================================
    # UI helpers (consider moving to a separate theming module)
    # ================================================================

    @staticmethod
    def _get_base64_image(image_path) -> Optional[str]:
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
        Set background image using CSS with optional filters.

        Args:
            image_path: Path to the background image
            black_and_white: If True, applies grayscale filter to background
            overlay_opacity: Opacity of white overlay (0.0 to 1.0). Default 0.85
            blur: Blur amount in pixels. Default 0 (no blur)
        """
        base64_image = self._get_base64_image(image_path)
        if not base64_image:
            return

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

    # ================================================================
    # Cache Management — Two-tier system
    #
    # Tier 1: Lookup tables (@st.cache_data with TTL)
    #     Small, rarely-changing reference data (items, units, types, etc.)
    #     Auto-expires after TTL, shared across sessions.
    #
    # Tier 2: View caches (st.session_state)
    #     Large view data (inventory, plantings, orders). Loaded once per
    #     session, explicit refresh via refresh button. Pages derive
    #     filtered working sets from these.
    # ================================================================

    # ===== TIER 1: PROPERTY ACCESSORS =====
    # Pages use these just like before: api.item_cache, api.unit_cache, etc.

    @property
    def item_cache(self):
        return _cached_load_items()

    @property
    def item_type_cache(self):
        return _cached_load_item_types()

    @property
    def unit_cache(self):
        return _cached_load_units()

    @property
    def unit_category_cache(self):
        return _cached_load_unit_categories()

    @property
    def location_cache(self):
        return _cached_load_locations()

    @property
    def supplier_cache(self):
        return _cached_load_suppliers()

    @property
    def shipper_cache(self):
        return _cached_load_shippers()

    @property
    def broker_cache(self):
        return _cached_load_brokers()

    @property
    def growing_season_cache(self):
        return _cached_load_growing_seasons()

    @property
    def order_item_type_cache(self):
        return _cached_load_order_item_types()

    @property
    def order_note_cache(self):
        return _cached_load_order_notes()

    # ===== TIER 2: SESSION-STATE VIEW CACHES =====

    def _get_session_cache(self, key: str, loader: Callable) -> pd.DataFrame:
        """Get a view cache from session_state, loading if not present."""
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
        """Force refresh a view cache in session_state."""
        try:
            result = loader()
            st.session_state[key] = result
            logger.info(f"Refreshed {key} ({len(result)} rows)")
            return result
        except Exception as e:
            logger.error(f"Failed to refresh {key}: {e}")
            st.session_state[key] = pd.DataFrame()
            return pd.DataFrame()

    # -- View caches --

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

    # -- Single-table caches (admin pages) --

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

    # -- Cache management --

    _VIEW_MAP = {
        "inventory": ("_inv_view", "get_inventory_view_full"),
        "plantings": ("_plant_view", "get_plantings_view_full"),
        "orders": ("_order_view", "get_orders_view_full"),
        "labels": ("_label_view", "get_label_view_full"),
        "pitch": ("_pitch_view", "get_pitch_view"),
        "inventory_table": ("_inv_table", "get_inventory_full"),
        "planting_table": ("_plant_table", "get_planting_full"),
        "pitch_table": ("_pitch_table", "get_pitch_full"),
        "order_table": ("_order_table", "get_order_full"),
        "order_item_table": ("_order_item_table", "get_order_item_full"),
        "price_table": ("_price_table", "get_price_full"),
        "seasonal_notes_table": ("_seasonal_notes_table", "get_seasonal_notes_full"),
        "oid_table": ("_oid_table", "get_order_item_destination_full"),
        "user_table": ("_user_table", "get_user_full"),
    }

    def refresh_view_cache(self, view_name: str) -> None:
        """Refresh a specific view or table cache. Call from page refresh buttons.

        Args:
            view_name: One of 'inventory', 'plantings', 'orders', 'labels', 'pitch',
                       'inventory_table', 'planting_table', 'pitch_table', 'order_table',
                       'order_item_table', 'price_table', 'seasonal_notes_table',
                       'oid_table', 'user_table', 'all'
        """
        if view_name == "all":
            for key, method_name in self._VIEW_MAP.values():
                self._refresh_session_cache(key, getattr(self, method_name))
        elif view_name in self._VIEW_MAP:
            key, method_name = self._VIEW_MAP[view_name]
            self._refresh_session_cache(key, getattr(self, method_name))
        else:
            logger.warning(f"Unknown view cache: {view_name}")

    @staticmethod
    def clear_lookup_caches():
        """Force clear all @st.cache_data lookup caches."""
        for loader in _CACHED_LOADERS:
            loader.clear()
        logger.info("All lookup caches cleared")

    # ===== TIER 2.5: FILTERED WORKING SETS =====

    @staticmethod
    def set_working_set(page_key: str, df: pd.DataFrame) -> None:
        """Store a filtered working set for a page."""
        st.session_state[f"_working_{page_key}"] = df

    @staticmethod
    def get_working_set(page_key: str) -> Optional[pd.DataFrame]:
        """Get the filtered working set for a page."""
        return st.session_state.get(f"_working_{page_key}")

    # Legacy compatibility
    def reset_cache(self, target_cache: str, get_method: Callable) -> None:
        """Legacy cache reset. For view caches, use refresh_view_cache() instead."""
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
        """Execute an action then refresh the relevant cache."""
        try:
            action()
            self.reset_cache(target_cache=target_cache, get_method=get_method)
        except Exception as e:
            logger.error(
                f"action_and_cache failed: action={action}, "
                f"cache={target_cache}: {e}"
            )

    # ================================================================
    # Generic CRUD
    # ================================================================

    def _get_all(self, model_class, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Generic method to get all records from a table."""
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
                return _rows_to_dataframe(results)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving records: {e}")
            raise

    def _get_by_id(
        self, model_class, id_column: str, id_value: Any
    ) -> Optional[Dict[str, Any]]:
        """Generic method to get a single record by ID."""
        try:
            with get_db_session() as session:
                result = (
                    session.query(model_class)
                    .filter(getattr(model_class, id_column) == id_value)
                    .first()
                )
                if result:
                    result_dict = _row_to_dict(result)
                    logger.info(f"Found record with {id_column}={id_value}")
                    return result_dict
                else:
                    logger.warning(f"No record found with {id_column}={id_value}")
                    return None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving record: {e}")
            raise

    def _create(self, model_class, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to create a new record with proper type conversion."""
        try:
            from sqlalchemy import Text, String, Integer, Float, Boolean, DateTime

            with get_db_session() as session:
                new_record = model_class()

                _TYPE_COERCIONS = {
                    (Text, String): str,
                    (Integer,): int,
                    (Float,): float,
                    (Boolean,): bool,
                }

                for key, value in data.items():
                    if not hasattr(new_record, key):
                        continue
                    if value is None:
                        setattr(new_record, key, None)
                        continue

                    column = getattr(model_class, key)
                    column_type = column.property.columns[0].type

                    coerced = False
                    for type_group, coerce_fn in _TYPE_COERCIONS.items():
                        if isinstance(column_type, type_group):
                            setattr(new_record, key, coerce_fn(value))
                            coerced = True
                            break
                    if not coerced:
                        # DateTime and anything else — pass through
                        setattr(new_record, key, value)

                session.add(new_record)
                session.commit()
                session.refresh(new_record)

                result_dict = _row_to_dict(new_record)
                logger.info(f"Created new record in {model_class.__tablename__}")
                return result_dict

        except SQLAlchemyError as e:
            logger.error(f"Error creating record: {e}")
            raise

    def _update(
        self, model_class, id_column: str, id_value: Any, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generic method to update a record."""
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

                for column, value in updates.items():
                    if hasattr(record, column):
                        setattr(record, column, value)
                    else:
                        logger.warning(
                            f"Column '{column}' does not exist on {model_class.__name__}"
                        )

                session.commit()
                result_dict = _row_to_dict(record)
                logger.info(
                    f"Updated record {id_column}={id_value} in {model_class.__tablename__}"
                )
                return result_dict

        except SQLAlchemyError as e:
            logger.error(f"Error updating record: {e}")
            raise

    def _delete(self, model_class, id_column: str, id_value: Any) -> bool:
        """Generic method to delete a record."""
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

    # ================================================================
    # Table getters (GET)
    # ================================================================
    # These all follow the same pattern, consolidated via _get_table.

    def _get_table(
        self,
        model_class,
        label: str,
        sort_by: Optional[List[str]] = None,
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        Generic single-table getter. Replaces all the individual get_*_full methods
        that had identical structure.
        """
        try:
            result = self._get_all(model_class=model_class)
            if sort_by and not result.empty:
                result = result.sort_values(by=sort_by, ascending=ascending)
            return result
        except Exception as e:
            logger.error(f"Error retrieving {label}: {e}")
            return pd.DataFrame()

    def get_inventory_full(self) -> pd.DataFrame:
        return self._get_table(Inventory, "Inventory List", sort_by=["DateCounted"])

    def get_broker_full(self) -> pd.DataFrame:
        return self._get_table(Broker, "Brokers List")

    def get_growing_season_full(self) -> pd.DataFrame:
        return self._get_table(GrowingSeason, "Growing Season List")

    def get_item_full(self) -> pd.DataFrame:
        return self._get_table(Item, "Items List")

    def get_item_type_full(self) -> pd.DataFrame:
        return self._get_table(ItemType, "Item Type List")

    def get_order_full(self) -> pd.DataFrame:
        return self._get_table(Order, "Orders List")

    def get_order_item_full(self) -> pd.DataFrame:
        return self._get_table(OrderItem, "Order Items List")

    def get_order_item_type_full(self) -> pd.DataFrame:
        return self._get_table(OrderItemType, "Order Item Type List")

    def get_order_note_full(self) -> pd.DataFrame:
        return self._get_table(OrderNote, "Order Notes List")

    def get_pitch_full(self) -> pd.DataFrame:
        return self._get_table(Pitch, "Pitch List")

    def get_planting_full(self) -> pd.DataFrame:
        return self._get_table(Planting, "Plantings List")

    def get_price_full(self) -> pd.DataFrame:
        return self._get_table(Price, "Prices List")

    def get_shipper_full(self) -> pd.DataFrame:
        return self._get_table(Shipper, "Shippers List")

    def get_supplier_full(self) -> pd.DataFrame:
        return self._get_table(Supplier, "Suppliers List")

    def get_unit_category_full(self) -> pd.DataFrame:
        return self._get_table(UnitCategory, "Unit Category List")

    def get_unit_full(self) -> pd.DataFrame:
        return self._get_table(Unit, "Units List")

    def get_location_full(self) -> pd.DataFrame:
        return self._get_table(Location, "Location List")

    def get_user_full(self) -> pd.DataFrame:
        return self._get_table(Users, "Users List")

    def get_seasonal_notes_full(self) -> pd.DataFrame:
        return self._get_table(SeasonalNotes, "Seasonal Notes List")

    def get_order_item_destination_full(self) -> pd.DataFrame:
        return self._get_table(OrderItemDestination, "Order Item Destination List")

    # ================================================================
    # Multi-table view getters
    # ================================================================

    def get_inventory_view_full(self) -> pd.DataFrame:
        from models import InventoryFullView

        return self._get_table(
            InventoryFullView, "Inventory View", sort_by=["DateCounted"]
        )

    def get_plantings_view_full(self) -> pd.DataFrame:
        from models import PlantingsFullView

        return self._get_table(
            PlantingsFullView,
            "Plantings View",
            sort_by=["DatePlanted", "PlantingID"],
        )

    def get_orders_view_full(self) -> pd.DataFrame:
        from models import OrdersFullView

        return self._get_table(
            OrdersFullView, "Orders View", sort_by=["DatePlaced", "DateDue"]
        )

    def get_label_view_full(self) -> pd.DataFrame:
        from models import LabelDataFullView

        return self._get_table(LabelDataFullView, "Label Data View")

    def get_pitch_view(self) -> pd.DataFrame:
        from models import PitchFullView

        return self._get_table(PitchFullView, "Pitch View")

    # ================================================================
    # Misc toolbox
    # ================================================================

    def decode_type(self, type_name: str) -> int:
        """
        Retrieve the numerical TypeID for a given type name.
        Queries the item_type_cache instead of relying on a hardcoded mapping.
        Falls back to 0 if the type name is not found.
        """
        cache = self.item_type_cache
        if cache.empty:
            return 0
        match = cache.loc[cache["Type"] == type_name, "TypeID"]
        return int(match.iloc[0]) if not match.empty else 0

    def get_sun_conditions(self) -> List:
        """Get list of sun conditions for dropdowns."""
        return self.item_cache["SunConditions"].unique().tolist()

    def get_item_types(self) -> pd.DataFrame:
        """Get list of item types for dropdowns."""
        return self.item_type_cache.copy()

    def _get_next_id(self, model_class, id_column: str) -> int:
        """
        Get next available ID for a table.

        NOTE: This is not concurrency-safe. If your database supports
        auto-increment / IDENTITY columns, prefer letting the DB assign IDs
        and remove this method. For single-user Streamlit apps this is fine.
        """
        df = self._get_all(model_class=model_class)
        if df.empty:
            return 1
        return int(df[id_column].max()) + 1

    def df_get_by_id(
        self, cache_data: pd.DataFrame, id_column: str, id: int
    ) -> pd.DataFrame:
        return cache_data[cache_data[id_column] == id].copy()

    # ================================================================
    # Display methods (workflow layer)
    # ================================================================

    def get_inventory_view_display(self) -> pd.DataFrame:
        try:
            return self.inventory_view_cache[
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
        except Exception as e:
            logger.error(f"Error Inventory Display Subset: {e}")
            return pd.DataFrame()

    def get_plantings_display(self) -> pd.DataFrame:
        try:
            return self.planting_view_cache[
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
        except Exception as e:
            logger.error(f"Error retrieving plantings subset: {e}")
            return pd.DataFrame()

    def get_label_display(
        self, item_id: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
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
            return label_data, label_data["SunConditions"]
        except Exception as e:
            logger.error(f"Error getting label subset: {e}")
            return pd.DataFrame(), pd.Series()

    def get_orders_display(self) -> pd.DataFrame:
        try:
            return self.order_view_cache[
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
        except Exception as e:
            logger.error(f"Error getting Order data subset: {e}")
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
            return summary.sort_values(by="DatePlaced", ascending=False)
        except Exception as e:
            logger.error(f"Error getting orders summary: {e}")
            return pd.DataFrame()

    # ================================================================
    # Admin-level actions: CREATE (POST)
    # ================================================================
    # Consolidated via _table_add helper. Each public method keeps its
    # exact original signature so callers don't need to change.

    def _table_add(
        self,
        model_class,
        id_column: str,
        payload: Dict[str, Any],
        label: str,
    ) -> Dict[str, Any]:
        """
        Shared create-record implementation.
        Generates the next ID, creates the record, logs it, and returns it.
        """
        try:
            payload[id_column] = self._get_next_id(model_class, id_column)
            result = self._create(model_class=model_class, data=payload)
            logger.info(f"Added {label} record {result[id_column]}")
            return result
        except Exception as e:
            logger.error(f"Error adding {label}: {e}")
            raise

    def table_add_inventory(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DateCounted: Optional[datetime] = None,
        InventoryComments: Optional[str] = None,
        LocationID: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add new inventory record."""
        payload: InventoryPayload = {
            "ItemID": ItemID,
            "UnitID": UnitID,
            "NumberOfUnits": NumberOfUnits,
            "DateCounted": DateCounted or datetime.now(),
            "InventoryComments": InventoryComments,
            "LocationID": LocationID,
        }
        return self._table_add(Inventory, "InventoryID", payload, "inventory")

    def table_add_broker(
        self, BrokerName: str, BrokerComments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add new broker record."""
        payload: BrokerPayload = {
            "Broker": BrokerName,
            "BrokerComments": BrokerComments,
        }
        return self._table_add(Broker, "BrokerID", payload, "broker")

    def table_add_growing_season(
        self,
        GrowingSeasonYear: str,
        StartDate: datetime,
        EndDate: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Add new growing season record."""
        payload: GrowingSeasonPayload = {
            "GrowingSeason": GrowingSeasonYear,
            "StartDate": StartDate,
            "EndDate": EndDate,
        }
        return self._table_add(
            GrowingSeason, "GrowingSeasonID", payload, "growing season"
        )

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
        """Add new item record."""
        from models import Item as ItemModel

        payload: ItemPayload = {
            "Item": Item,
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
        return self._table_add(ItemModel, "ItemID", payload, "item")

    def table_add_item_type(self, Type: str) -> Dict[str, Any]:
        """Add new item type record."""
        payload: ItemTypePayload = {"Type": Type}
        return self._table_add(ItemType, "TypeID", payload, "item type")

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
        """Add new order record."""
        payload: OrderPayload = {
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
        return self._table_add(Order, "OrderID", payload, "order")

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
        """Add new order item record."""
        payload: OrderItemPayload = {
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
        return self._table_add(OrderItem, "OrderItemID", payload, "order item")

    def table_add_order_item_type(self, OrderItemTypeName: str) -> Dict[str, Any]:
        """Add new order item type record."""
        payload: OrderItemTypePayload = {"OrderItemType": OrderItemTypeName}
        return self._table_add(
            OrderItemType, "OrderItemTypeID", payload, "order item type"
        )

    def table_add_order_note(self, OrderNoteText: str) -> Dict[str, Any]:
        """Add new order note record."""
        payload: OrderNotePayload = {"OrderNote": OrderNoteText}
        return self._table_add(OrderNote, "OrderNoteID", payload, "order note")

    def table_add_pitch(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DatePitched: Optional[datetime] = None,
        PitchComments: Optional[str] = None,
        PitchReason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new pitch record."""
        payload: PitchPayload = {
            "DatePitched": DatePitched or datetime.now(),
            "ItemID": ItemID,
            "UnitID": UnitID,
            "NumberOfUnits": NumberOfUnits,
            "PitchComments": PitchComments,
            "PitchReason": PitchReason,
        }
        return self._table_add(Pitch, "PitchID", payload, "pitch")

    def table_add_planting(
        self,
        ItemID: int,
        UnitID: int,
        NumberOfUnits: str,
        DatePlanted: Optional[datetime] = None,
        PlantingComments: Optional[str] = None,
        LocationID: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add new planting record."""
        payload: PlantingPayload = {
            "DatePlanted": DatePlanted or datetime.now(),
            "ItemID": ItemID,
            "UnitID": UnitID,
            "NumberOfUnits": NumberOfUnits,
            "PlantingComments": PlantingComments,
            "LocationID": LocationID,
        }
        return self._table_add(Planting, "PlantingID", payload, "planting")

    def table_add_price(
        self,
        ItemID: int,
        UnitID: int,
        UnitPrice: float,
        Year: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add new price record."""
        payload: PricePayload = {
            "ItemID": ItemID,
            "UnitID": UnitID,
            "UnitPrice": UnitPrice,
            "Year": Year,
        }
        return self._table_add(Price, "PriceID", payload, "price")

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
        """Add new shipper record."""
        payload: ShipperPayload = {
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
        return self._table_add(Shipper, "ShipperID", payload, "shipper")

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
        """Add new supplier record."""
        payload: SupplierPayload = {
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
        return self._table_add(Supplier, "SupplierID", payload, "supplier")

    def table_add_unit_category(self, UnitCategoryName: str) -> Dict[str, Any]:
        """Add new unit category record."""
        payload: UnitCategoryPayload = {"UnitCategory": UnitCategoryName}
        return self._table_add(UnitCategory, "UnitCategoryID", payload, "unit category")

    def table_add_unit(
        self,
        UnitType: str,
        UnitSize: str,
        UnitCategoryID: int,
    ) -> Dict[str, Any]:
        """Add new unit record."""
        payload: UnitPayload = {
            "UnitType": UnitType,
            "UnitSize": UnitSize,
            "UnitCategoryID": UnitCategoryID,
        }
        return self._table_add(Unit, "UnitID", payload, "unit")

    def table_add_location(self, Location: str) -> Dict[str, Any]:
        """Add new location record."""
        from models import Location as LocationModel

        payload: LocationPayload = {"Location": Location}
        return self._table_add(LocationModel, "LocationID", payload, "location")

    def table_add_user(
        self,
        Role: str,
        Email: str,
        PermissionLevel: Optional[str] = None,
        Active: bool = True,
    ) -> Dict[str, Any]:
        """Add new user record."""
        payload: UserPayload = {
            "Role": Role,
            "PermissionLevel": PermissionLevel,
            "Email": Email,
            "Active": 1 if Active else 0,
            "CreatedAt": datetime.now(),
            "UpdatedAt": datetime.now(),
        }
        return self._table_add(Users, "UserID", payload, "user")

    def table_add_seasonal_note(
        self,
        ItemID: int,
        GrowingSeasonID: int,
        Greenhouse: int,
        Note: str,
        LastUpdate: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Add new seasonal note record."""
        payload: SeasonalNotesPayload = {
            "ItemID": ItemID,
            "GrowingSeasonID": GrowingSeasonID,
            "Greenhouse": Greenhouse,
            "Note": Note,
            "LastUpdate": LastUpdate or datetime.now(),
        }
        return self._table_add(SeasonalNotes, "NoteID", payload, "seasonal note")

    def table_add_order_item_destination(
        self,
        OrderItemID: int,
        Count: int,
        UnitID: int,
        LocationID: int,
    ) -> Dict[str, Any]:
        """Add new order item destination record."""
        payload: OrderItemDestinationPayload = {
            "OrderItemID": OrderItemID,
            "Count": Count,
            "UnitID": UnitID,
            "LocationID": LocationID,
        }
        return self._table_add(
            OrderItemDestination,
            "OrderItemDestinationID",
            payload,
            "order item destination",
        )

    # ================================================================
    # UPDATE
    # ================================================================

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
        Generic update with field filtering and preprocessing.

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

            # Filter to allowed fields
            filtered_updates = {}
            rejected_fields = []

            for column, value in updates.items():
                if allowed_fields is not None and column not in allowed_fields:
                    rejected_fields.append(column)
                    if strict:
                        raise ValueError(
                            f"Cannot update field '{column}' — it's read-only or from a joined table"
                        )
                    continue
                filtered_updates[column] = value

            if rejected_fields:
                logger.warning(f"Filtered out read-only fields: {rejected_fields}")

            if not filtered_updates:
                logger.warning("No valid fields to update after filtering")
                return existing

            # Apply preprocessors
            processed_updates = {}
            for column, value in filtered_updates.items():
                if preprocessors and column in preprocessors:
                    try:
                        processed_updates[column] = preprocessors[column](value)
                        logger.debug(
                            f"Preprocessed {column}: {value} -> {processed_updates[column]}"
                        )
                    except Exception as e:
                        logger.error(f"Error preprocessing {column}: {e}")
                        raise ValueError(f"Invalid value for {column}: {value}")
                else:
                    processed_updates[column] = value

            return self._update(
                model_class=model_class,
                id_column=id_column,
                id_value=id_value,
                updates=processed_updates,
            )

        except Exception as e:
            logger.error(
                f"generic_update failed for {id_column}={id_value}: {e} | "
                f"updates={updates}, allowed_fields={allowed_fields}"
            )
            return None
