"""
SQLAlchemy models for Edgewater database tables
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from database import Base


class ItemType(Base):
    """T_ItemType - Item type lookup table"""

    __tablename__ = "T_ItemType"

    TypeID = Column(Integer, primary_key=True)
    Type = Column(Text)

    # Relationships
    items = relationship("Item", back_populates="item_type")


class UnitCategory(Base):
    """T_UnitCategory - Unit category lookup table"""

    __tablename__ = "T_UnitCategory"

    UnitCategoryID = Column(Integer, primary_key=True)
    UnitCategory = Column(Text)

    # Relationships
    units = relationship("Unit", back_populates="unit_category")


class Unit(Base):
    """T_Units - Unit of measurement"""

    __tablename__ = "T_Units"

    UnitID = Column(Integer, primary_key=True)
    UnitType = Column(Text)
    UnitSize = Column(Text)
    UnitCategoryID = Column(Integer, ForeignKey("T_UnitCategory.UnitCategoryID"))

    # Relationships
    unit_category = relationship("UnitCategory", back_populates="units")
    prices = relationship("Price", back_populates="unit")
    plantings = relationship("Planting", back_populates="unit")
    inventory = relationship("Inventory", back_populates="unit")
    pitch = relationship("Pitch", back_populates="unit")


class Broker(Base):
    """T_Brokers - Broker information"""

    __tablename__ = "T_Brokers"

    BrokerID = Column(Integer, primary_key=True)
    Broker = Column(Text)
    BrokerComments = Column(Text)

    # Relationships
    orders = relationship("Order", back_populates="broker")


class Shipper(Base):
    """T_Shippers - Shipping company information"""

    __tablename__ = "T_Shippers"

    ShipperID = Column(Integer, primary_key=True)
    Shipper = Column(Text)
    AccountNumber = Column(Text)
    Phone = Column(Text)
    ContactPerson = Column(Text)
    Address1 = Column(Text)
    Address2 = Column(Text)
    City = Column(Text)
    State = Column(Text)
    Zip = Column(Text)
    ShipperComments = Column(Text)

    # Relationships
    orders = relationship("Order", back_populates="shipper")


class Supplier(Base):
    """T_Suppliers - Supplier information"""

    __tablename__ = "T_Suppliers"

    SupplierID = Column(Integer, primary_key=True)
    Supplier = Column(Text)
    AccountNumber = Column(Text)
    Phone = Column(Text)
    Fax = Column(Text)
    WebSite = Column(Text)
    Email = Column(Text)
    ContactPerson = Column(Text)
    Address1 = Column(Text)
    Address2 = Column(Text)
    City = Column(Text)
    State = Column(Text)
    Zip = Column(Text)
    SupplierComments = Column(Text)
    SupplierType = Column(Text)

    # Relationships
    orders = relationship("Order", back_populates="supplier")


class GrowingSeason(Base):
    """T_GrowingSeason - Growing season definitions"""

    __tablename__ = "T_GrowingSeason"

    GrowingSeasonID = Column(Integer, primary_key=True)
    GrowingSeason = Column(Text)
    StartDate = Column(DateTime)
    EndDate = Column(DateTime)

    # Relationships
    orders = relationship("Order", back_populates="growing_season")


class OrderItemType(Base):
    """T_OrderItemTypes - Order item type lookup"""

    __tablename__ = "T_OrderItemTypes"

    OrderItemTypeID = Column(Integer, primary_key=True)
    OrderItemType = Column(Text)

    # Relationships
    order_items = relationship("OrderItem", back_populates="order_item_type")


class OrderNote(Base):
    """T_OrderNotes - Order note templates"""

    __tablename__ = "T_OrderNotes"

    OrderNoteID = Column(Integer, primary_key=True)
    OrderNote = Column(Text)

    # Relationships
    order_items = relationship("OrderItem", back_populates="order_note")


class Item(Base):
    """T_Items - Main inventory items"""

    __tablename__ = "T_Items"

    ItemID = Column(Integer, primary_key=True)
    Inactive = Column(Boolean, default=False)
    Item = Column(Text)
    Variety = Column(Text)
    Color = Column(Text)
    ShouldStock = Column(Boolean, default=False)
    TypeID = Column(Integer, ForeignKey("T_ItemType.TypeID"))
    LabelDescription = Column(Text)
    Definition = Column(Text)
    PictureLayout = Column(Text)
    PictureLink = Column(Text)
    SunConditions = Column(Text)

    # Relationships
    item_type = relationship("ItemType", back_populates="items")
    prices = relationship("Price", back_populates="item")
    plantings = relationship("Planting", back_populates="item")
    inventory = relationship("Inventory", back_populates="item")
    pitch = relationship("Pitch", back_populates="item")
    order_items = relationship("OrderItem", back_populates="item")


class Price(Base):
    """T_Prices - Historical pricing information"""

    __tablename__ = "T_Prices"

    PriceID = Column(Integer, primary_key=True)
    ItemID = Column(Integer, ForeignKey("T_Items.ItemID"))
    UnitID = Column(Integer, ForeignKey("T_Units.UnitID"))
    UnitPrice = Column(Float)
    Year = Column(Text)

    # Relationships
    item = relationship("Item", back_populates="prices")
    unit = relationship("Unit", back_populates="prices")


class Planting(Base):
    """T_Plantings - Planting records"""

    __tablename__ = "T_Plantings"

    PlantingID = Column(Integer, primary_key=True)
    DatePlanted = Column(DateTime)
    ItemID = Column(Integer, ForeignKey("T_Items.ItemID"))
    UnitID = Column(Integer, ForeignKey("T_Units.UnitID"))
    NumberOfUnits = Column(Text)
    PlantingComments = Column(Text)

    # Relationships
    item = relationship("Item", back_populates="plantings")
    unit = relationship("Unit", back_populates="plantings")


class Inventory(Base):
    """T_Inventory - Inventory count records"""

    __tablename__ = "T_Inventory"

    InventoryID = Column(Integer, primary_key=True)
    DateCounted = Column(DateTime)
    ItemID = Column(Integer, ForeignKey("T_Items.ItemID"))
    UnitID = Column(Integer, ForeignKey("T_Units.UnitID"))
    NumberOfUnits = Column(Text)
    InventoryComments = Column(Text)

    # Relationships
    item = relationship("Item", back_populates="inventory")
    unit = relationship("Unit", back_populates="inventory")


class Pitch(Base):
    """T_Pitch - Discarded items"""

    __tablename__ = "T_Pitch"

    PitchID = Column(Integer, primary_key=True)
    DatePitched = Column(DateTime)
    ItemID = Column(Integer, ForeignKey("T_Items.ItemID"))
    UnitID = Column(Integer, ForeignKey("T_Units.UnitID"))
    NumberOfUnits = Column(Text)
    PitchComments = Column(Text)
    PitchReason = Column(Text)

    # Relationships
    item = relationship("Item", back_populates="pitch")
    unit = relationship("Unit", back_populates="pitch")


class Order(Base):
    """T_Orders - Order headers"""

    __tablename__ = "T_Orders"

    OrderID = Column(Integer, primary_key=True)
    GrowingSeasonID = Column(Integer, ForeignKey("T_GrowingSeason.GrowingSeasonID"))
    DatePlaced = Column(DateTime)
    DateDue = Column(DateTime)
    DateReceived = Column(DateTime)
    SupplierID = Column(Integer, ForeignKey("T_Suppliers.SupplierID"))
    OrderNumber = Column(Text)
    ShipperID = Column(Integer, ForeignKey("T_Shippers.ShipperID"))
    TrackingNumber = Column(Text)
    OrderComments = Column(Text)
    TotalCost = Column(Float)
    GrowingSeason = Column(Text)
    BrokerID = Column(Integer, ForeignKey("T_Brokers.BrokerID"))

    # Relationships
    growing_season = relationship("GrowingSeason", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    shipper = relationship("Shipper", back_populates="orders")
    broker = relationship("Broker", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """T_OrderItems - Order line items"""

    __tablename__ = "T_OrderItems"

    OrderItemID = Column(Integer, primary_key=True)
    OrderID = Column(Integer, ForeignKey("T_Orders.OrderID"))
    ItemID = Column(Integer, ForeignKey("T_Items.ItemID"))
    ItemCode = Column(Text)
    OrderItemTypeID = Column(Integer, ForeignKey("T_OrderItemTypes.OrderItemTypeID"))
    Unit = Column(Text)
    UnitPrice = Column(Float)
    NumberOfUnits = Column(Text)
    Received = Column(Boolean, default=False)
    OrderNote = Column(Integer, ForeignKey("T_OrderNotes.OrderNoteID"))
    OrderComments = Column(Text)
    Leftover = Column(Text)
    ToOrder = Column(Text)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    item = relationship("Item", back_populates="order_items")
    order_item_type = relationship("OrderItemType", back_populates="order_items")
    order_note = relationship("OrderNote", back_populates="order_items")


class SeasonalNotes(Base):
    __tablename__ = "T_SeasonalNotes"

    NoteID = Column(Integer, primary_key=True, autoincrement=True)
    ItemID = Column(Integer, nullable=False)
    GrowingSeason = Column(Integer, nullable=False)
    Greenhouse = Column(Integer, nullable=False)
    Note = Column(Text, nullable=False)
    LastUpdate = Column(DateTime, nullable=False)


class Users(Base):
    __tablename__ = "T_Users"
    UserID = Column(Integer, primary_key=True)
    Role = Column(Text)
    PermissionLevel = Column(Text)
    Email = Column(String(255))
    Active = Column(TINYINT)
    CreatedAt = Column(DateTime)
    UpdatedAt = Column(DateTime)


class Passwords(Base):
    __tablename__ = "T_Passwords"

    PasswordID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    PasswordResetToken = Column(String(255), nullable=True)
    PasswordResetExpiry = Column(DateTime, nullable=True)
    LastLogin = Column(DateTime, nullable=True)
    LastPasswordChange = Column(DateTime, nullable=True)
    FailedLoginAttempts = Column(Integer, default=0)
    AccountLockedUntil = Column(DateTime, nullable=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    UpdatedAt = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class OrderItemDestination(Base):
    __tablename__ = "T_OrderItemDestination"

    OrderItemDestinationID = Column(Integer, primary_key=True, autoincrement=True)
    OrderItemID = Column(Integer, nullable=False)
    Count = Column(Integer, nullable=False)
    UnitID = Column(Integer, nullable=False)
    LocationID = Column(Integer, nullable=False)


class Location(Base):
    __tablename__ = "T_Locations"

    LocationID = Column(Integer, primary_key=True)
    Location = Column(Text)


class InventoryFullView(Base):
    """v_inventory_full - SQL View for complete inventory data"""

    __tablename__ = "v_inventory_full"

    # Primary key (required for SQLAlchemy)
    InventoryID = Column(Integer, primary_key=True)

    # Inventory fields
    DateCounted = Column(DateTime)
    NumberOfUnits = Column(Text)
    InventoryComments = Column(Text)

    # Item fields
    ItemID = Column(Integer)
    Item = Column(Text)
    Variety = Column(Text)
    Color = Column(Text)
    Inactive = Column(Boolean)
    ShouldStock = Column(Boolean)
    LabelDescription = Column(Text)
    Definition = Column(Text)
    PictureLink = Column(Text)
    SunConditions = Column(Text)
    TypeID = Column(Integer)

    # ItemType fields
    Type = Column(Text)

    # Unit fields
    UnitID = Column(Integer)
    UnitType = Column(Text)
    UnitSize = Column(Text)
    UnitCategoryID = Column(Integer)

    # UnitCategory fields
    UnitCategory = Column(Text)


class PlantingsFullView(Base):
    """v_plantings_full - SQL View for complete plantings data"""

    __tablename__ = "v_plantings_full"

    # Primary key
    PlantingID = Column(Integer, primary_key=True)

    # Planting fields
    DatePlanted = Column(DateTime)
    NumberOfUnits = Column(Text)
    PlantingComments = Column(Text)

    # Item fields
    ItemID = Column(Integer)
    Item = Column(Text)
    Variety = Column(Text)
    Color = Column(Text)
    Inactive = Column(Boolean)
    SunConditions = Column(Text)
    TypeID = Column(Integer)

    # Unit fields
    UnitID = Column(Integer)
    UnitType = Column(Text)
    UnitSize = Column(Text)
    UnitCategoryID = Column(Integer)

    # UnitCategory fields
    UnitCategory = Column(Text)


class LabelDataFullView(Base):
    """v_label_data_full - SQL View for label data"""

    __tablename__ = "v_label_data_full"

    # Primary key
    ItemID = Column(Integer, primary_key=True)

    # Item fields
    Item = Column(Text)
    Variety = Column(Text)
    Color = Column(Text)
    SunConditions = Column(Text)
    LabelDescription = Column(Text)
    Definition = Column(Text)
    TypeID = Column(Integer)

    # ItemType fields
    Type = Column(Text)

    # Price fields
    PriceID = Column(Integer)
    UnitID = Column(Integer)
    UnitPrice = Column(Float)
    Year = Column(Text)


class OrdersFullView(Base):
    """v_orders_full - SQL View for complete orders data"""

    __tablename__ = "v_orders_full"

    # Primary key
    OrderItemID = Column(Integer, primary_key=True)

    # OrderItem fields
    ItemCode = Column(Text)
    Unit = Column(Text)
    UnitPrice = Column(Float)
    NumberOfUnits = Column(Text)
    Received = Column(Boolean)
    OrderNoteCode = Column(Integer)
    OrderItemComments = Column(Text)
    Leftover = Column(Text)
    ToOrder = Column(Text)
    ItemID = Column(Integer)

    # Order fields
    OrderID = Column(Integer)
    DatePlaced = Column(DateTime)
    DateReceived = Column(DateTime)
    OrderNumber = Column(Text)
    TrackingNumber = Column(Text)
    OrderComments = Column(Text)
    GrowingSeason = Column(Text)
    GrowingSeasonID = Column(Integer)
    DateDue = Column(DateTime)
    TotalCost = Column(Float)

    # OrderItemType fields
    OrderItemType = Column(Text)
    OrderItemTypeID = Column(Integer)

    # OrderNote fields
    OrderNoteID = Column(Integer)
    OrderNoteDecode = Column(Text)

    # Broker fields
    BrokerID = Column(Integer)
    Broker = Column(Text)
    BrokerComments = Column(Text)

    # Shipper fields
    ShipperID = Column(Integer)
    Shipper = Column(Text)
    ShipperAccountNumber = Column(Text)
    ShipperContactPerson = Column(Text)
    ShipperAddress1 = Column(Text)
    ShipperAddress2 = Column(Text)
    ShipperCity = Column(Text)
    ShipperState = Column(Text)
    ShipperZip = Column(Text)
    ShipperPhone = Column(Text)
    ShipperComments = Column(Text)

    # Supplier fields
    SupplierID = Column(Integer)
    Supplier = Column(Text)
    SupplierAccountNumber = Column(Text)
    SupplierPhone = Column(Text)
    SupplierFax = Column(Text)
    WebSite = Column(Text)
    Email = Column(Text)
    SupplierContactPerson = Column(Text)
    SupplierAddress1 = Column(Text)
    SupplierAddress2 = Column(Text)
    SupplierCity = Column(Text)
    SupplierState = Column(Text)
    SupplierZip = Column(Text)
    SupplierComments = Column(Text)
    SupplierType = Column(Text)
