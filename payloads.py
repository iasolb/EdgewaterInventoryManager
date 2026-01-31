"""
TypedDict payload definitions for Edgewater API
Provides autocomplete support for database operations
"""

from typing import TypedDict
from datetime import datetime


class BrokerPayload(TypedDict, total=False):
    BrokerID: int
    Broker: str
    BrokerComments: str


class GrowingSeasonPayload(TypedDict, total=False):
    GrowingSeasonID: int
    GrowingSeason: str
    StartDate: datetime
    EndDate: datetime


class InventoryPayload(TypedDict, total=False):
    InventoryID: int
    DateCounted: datetime
    ItemID: int
    UnitID: int
    NumberOfUnits: str
    InventoryComments: str


class ItemPayload(TypedDict, total=False):
    ItemID: int
    Inactive: bool
    Item: str
    Variety: str
    Color: str
    ShouldStock: bool
    TypeID: int
    LabelDescription: str
    Definition: str
    PictureLayout: str
    PictureLink: str
    SunConditions: str


class ItemTypePayload(TypedDict, total=False):
    TypeID: int
    Type: str


class OrderPayload(TypedDict, total=False):
    OrderID: int
    GrowingSeasonID: int
    DatePlaced: datetime
    DateDue: datetime
    DateReceived: datetime
    SupplierID: int
    OrderNumber: str
    ShipperID: int
    TrackingNumber: str
    OrderComments: str
    TotalCost: float
    GrowingSeason: str
    BrokerID: int


class OrderItemPayload(TypedDict, total=False):
    OrderItemID: int
    OrderID: int
    ItemID: int
    ItemCode: str
    OrderItemTypeID: int
    Unit: str
    UnitPrice: float
    NumberOfUnits: str
    Received: bool
    OrderNote: int
    OrderComments: str
    Leftover: str
    ToOrder: str


class OrderItemTypePayload(TypedDict, total=False):
    OrderItemTypeID: int
    OrderItemType: str


class OrderNotePayload(TypedDict, total=False):
    OrderNoteID: int
    OrderNote: str


class PitchPayload(TypedDict, total=False):
    PitchID: int
    DatePitched: datetime
    ItemID: int
    UnitID: int
    NumberOfUnits: str
    PitchComments: str
    PitchReason: str


class PlantingPayload(TypedDict, total=False):
    PlantingID: int
    DatePlanted: datetime
    ItemID: int
    UnitID: int
    NumberOfUnits: str
    PlantingComments: str


class PricePayload(TypedDict, total=False):
    PriceID: int
    ItemID: int
    UnitID: int
    UnitPrice: float
    Year: str


class ShipperPayload(TypedDict, total=False):
    ShipperID: int
    Shipper: str
    AccountNumber: str
    Phone: str
    ContactPerson: str
    Address1: str
    Address2: str
    City: str
    State: str
    Zip: str
    ShipperComments: str


class SupplierPayload(TypedDict, total=False):
    SupplierID: int
    Supplier: str
    AccountNumber: str
    Phone: str
    Fax: str
    WebSite: str
    Email: str
    ContactPerson: str
    Address1: str
    Address2: str
    City: str
    State: str
    Zip: str
    SupplierComments: str
    SupplierType: str


class UnitPayload(TypedDict, total=False):
    UnitID: int
    UnitType: str
    UnitSize: str
    UnitCategoryID: int


class UnitCategoryPayload(TypedDict, total=False):
    UnitCategoryID: int
    UnitCategory: str


class UserPayload(TypedDict, total=False):
    UserID: int
    Role: str
    PermissionLevel: str
    Email: str
    Active: bool


class PasswordPayload(TypedDict, total=False):
    PasswordID: int
    UserID: int
    PasswordHash: str
    PasswordResetToken: str
    PasswordResetExpiry: datetime
    LastLogin: datetime
    LastPasswordChange: datetime
    FailedLoginAttempts: int
    AccountLockedUntil: datetime
    CreatedAt: datetime
    UpdatedAt: datetime


class SeasonalNotesPayload(TypedDict, total=False):
    NoteID: int
    ItemId: int
    GrowingSeasonID: int
    Greenhouse: bool
    Note: str
    LastUpdate: datetime


class OrderItemDestinationPayload(TypedDict, total=False):
    OrderItemID: int
    Count: float
    UnitID: int
    LocationID: int


class LocationPayload(TypedDict, total=False):
    LocationID: int
    Location: str


class InventoryFullViewPayload(TypedDict, total=False):
    """Payload for v_inventory_full view"""

    InventoryID: int
    DateCounted: datetime
    NumberOfUnits: str
    InventoryComments: str
    # Item fields
    ItemID: int
    Item: str
    Variety: str
    Color: str
    Inactive: bool
    ShouldStock: bool
    LabelDescription: str
    Definition: str
    PictureLink: str
    PictureLayout: str
    SunConditions: str
    TypeID: int
    # ItemType fields
    Type: str
    # Unit fields
    UnitID: int
    UnitType: str
    UnitSize: str
    UnitCategoryID: int
    # UnitCategory fields
    UnitCategory: str


class PlantingsFullViewPayload(TypedDict, total=False):
    """Payload for v_plantings_full view"""

    PlantingID: int
    DatePlanted: datetime
    NumberOfUnits: str
    PlantingComments: str
    # Item fields
    ItemID: int
    Item: str
    Variety: str
    Color: str
    Inactive: bool
    ShouldStock: bool
    SunConditions: str
    TypeID: int
    Definition: str
    LabelDescription: str
    # ItemType fields
    Type: str
    # Unit fields
    UnitID: int
    UnitType: str
    UnitSize: str
    UnitCategoryID: int
    # UnitCategory fields
    UnitCategory: str
    # SeasonalNotes fields
    NoteID: int
    GrowingSeasonID: int
    Greenhouse: bool
    SeasonalNote: str
    NoteLastUpdate: datetime


class OrdersFullViewPayload(TypedDict, total=False):
    """Payload for v_orders_full view"""

    OrderItemID: int
    ItemCode: str
    Unit: str
    UnitPrice: float
    NumberOfUnits: str
    Received: bool
    OrderNoteCode: int  # Integer ID from T_OrderItems.OrderNote
    OrderItemComments: str
    Leftover: str
    ToOrder: str
    ItemID: int
    # Item fields
    Item: str
    Variety: str
    Color: str
    ItemTypeName: str
    # OrderItemDestination fields
    OrderItemDestinationID: int
    DestinationCount: int
    DestinationUnitID: int
    DestinationUnitType: str
    DestinationUnitSize: str
    # Location fields
    LocationID: int
    LocationName: str
    # Order fields
    OrderID: int
    DatePlaced: datetime
    DateReceived: datetime
    DateDue: datetime
    OrderNumber: str
    TrackingNumber: str
    OrderComments: str
    TotalCost: float
    GrowingSeason: str
    GrowingSeasonID: int
    # GrowingSeason fields
    SeasonStartDate: datetime
    SeasonEndDate: datetime
    # OrderItemType fields
    OrderItemType: str
    OrderItemTypeID: int
    # OrderNote fields
    OrderNoteID: int
    OrderNoteDecode: str  # Actual text from T_OrderNotes.OrderNote
    # Broker fields
    BrokerID: int
    Broker: str
    BrokerComments: str
    # Shipper fields
    ShipperID: int
    Shipper: str
    ShipperAccountNumber: str
    ShipperContactPerson: str
    ShipperAddress1: str
    ShipperAddress2: str
    ShipperCity: str
    ShipperState: str
    ShipperZip: str
    ShipperPhone: str
    ShipperComments: str
    # Supplier fields
    SupplierID: int
    Supplier: str
    SupplierAccountNumber: str
    SupplierPhone: str
    SupplierFax: str
    WebSite: str
    Email: str
    SupplierContactPerson: str
    SupplierAddress1: str
    SupplierAddress2: str
    SupplierCity: str
    SupplierState: str
    SupplierZip: str
    SupplierComments: str
    SupplierType: str


class LabelDataFullViewPayload(TypedDict, total=False):
    """Payload for v_label_data_full view"""

    ItemID: int
    Item: str
    Variety: str
    Color: str
    SunConditions: str
    LabelDescription: str
    Definition: str
    PictureLink: str
    PictureLayout: str
    Inactive: bool
    ShouldStock: bool
    TypeID: int
    # ItemType fields
    Type: str
    # Price fields
    PriceID: int
    UnitID: int
    UnitPrice: float
    Year: str
    # Unit fields
    UnitType: str
    UnitSize: str
    UnitCategoryID: int
    # UnitCategory fields
    UnitCategory: str


class PitchFullViewPayload(TypedDict, total=False):
    """Payload for v_pitch_full view"""

    PitchID: int
    DatePitched: datetime
    NumberOfUnits: str
    PitchComments: str
    PitchReason: str
    # Item fields
    ItemID: int
    Item: str
    Variety: str
    Color: str
    ItemTypeName: str
    ShouldStock: bool
    # Unit fields
    UnitID: int
    UnitType: str
    UnitSize: str
    # UnitCategory fields
    UnitCategory: str
