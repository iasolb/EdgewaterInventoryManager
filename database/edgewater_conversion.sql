PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

/* Lookup/parent tables first */
CREATE TABLE IF NOT EXISTS T_ItemType (
  TypeID       INTEGER PRIMARY KEY,
  Type         TEXT
);

CREATE TABLE IF NOT EXISTS T_UnitCategory (
  UnitCategoryID INTEGER PRIMARY KEY,
  UnitCategory   TEXT
);

CREATE TABLE IF NOT EXISTS T_Units (
  UnitID       INTEGER PRIMARY KEY,
  UnitType     TEXT,
  UnitSize     TEXT,
  UnitCategory INTEGER,
  FOREIGN KEY (UnitCategory)
    REFERENCES T_UnitCategory(UnitCategoryID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_Brokers (
  BrokerID       INTEGER PRIMARY KEY,
  Broker         TEXT,
  BrokerComments TEXT
);

CREATE TABLE IF NOT EXISTS T_Shippers (
  ShipperID       INTEGER PRIMARY KEY,
  Shipper         TEXT,
  AccountNumber   TEXT,
  Phone           TEXT,
  ContactPerson   TEXT,
  Address1        TEXT,
  Address2        TEXT,
  City            TEXT,
  State           TEXT,
  Zip             TEXT,
  ShipperComments TEXT
);

CREATE TABLE IF NOT EXISTS T_Suppliers (
  SupplierID      INTEGER PRIMARY KEY,
  Supplier        TEXT,
  AccountNumber   TEXT,
  Phone           TEXT,
  Fax             TEXT,
  WebSite         TEXT,
  Email           TEXT,
  ContactPerson   TEXT,
  Address1        TEXT,
  Address2        TEXT,
  City            TEXT,
  State           TEXT,
  Zip             TEXT,
  SupplierComments TEXT,
  SupplierType     TEXT
);

CREATE TABLE IF NOT EXISTS T_GrowingSeason (
  GrowingSeasonID INTEGER PRIMARY KEY,
  GrowingSeason   TEXT,
  StartDate       DATETIME,
  EndDate         DATETIME
);

/* Core entities */
CREATE TABLE IF NOT EXISTS T_Items (
  ItemID         INTEGER PRIMARY KEY,
  Inactive       BOOLEAN,
  Item           TEXT,
  Variety        TEXT,
  Color          TEXT,
  ShouldStock    BOOLEAN,
  TypeID         INTEGER,
  LabelDescription TEXT,
  Definition     TEXT,
  PictureLayout  TEXT,
  PictureLink    TEXT,
  SunConditions  TEXT,
  FOREIGN KEY (TypeID)
    REFERENCES T_ItemType(TypeID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

/* One-to-one export row per item (ItemID as PK + FK to T_Items) */
CREATE TABLE IF NOT EXISTS T_Export_Items (
  ItemID          INTEGER PRIMARY KEY,
  CombinedName    TEXT,
  LabelDescription TEXT,
  SunConditions   TEXT,
  Inactive        BOOLEAN,
  Item            TEXT,
  Variety         TEXT,
  Color           TEXT,
  Type            TEXT,
  Definition      TEXT,
  PictureLayout   TEXT,
  PictureLink     TEXT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_Prices (
  PriceID   INTEGER PRIMARY KEY,
  ItemID    INTEGER,
  UnitID    INTEGER,
  UnitPrice DOUBLE,
  Year      TEXT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (UnitID)
    REFERENCES T_Units(UnitID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_Plantings (
  PlantingID       INTEGER PRIMARY KEY,
  DatePlanted      DATETIME,
  ItemID           INTEGER,
  UnitID           INTEGER,
  NumberOfUnits    TEXT,
  PlantingComments TEXT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (UnitID)
    REFERENCES T_Units(UnitID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_Inventory (
  InventoryID      INTEGER PRIMARY KEY,
  DateCounted      DATETIME,
  ItemID           INTEGER,
  UnitID           INTEGER,
  NumberOfUnits    TEXT,
  InventoryComments TEXT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (UnitID)
    REFERENCES T_Units(UnitID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_Pitch (
  PitchID       INTEGER PRIMARY KEY,
  DatePitched   DATETIME,
  ItemID        INTEGER,
  UnitID        INTEGER,
  NumberOfUnits TEXT,
  PitchComments TEXT,
  PitchReason   TEXT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (UnitID)
    REFERENCES T_Units(UnitID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

/* Orders domain */
CREATE TABLE IF NOT EXISTS T_OrderItemTypes (
  OrderItemTypeID INTEGER PRIMARY KEY,
  OrderItemType   TEXT
);

CREATE TABLE IF NOT EXISTS T_OrderNotes (
  OrderNoteID INTEGER PRIMARY KEY,
  OrderNote   TEXT
);

CREATE TABLE IF NOT EXISTS T_Orders (
  OrderID        INTEGER PRIMARY KEY,
  GrowingSeasonID INTEGER,
  DatePlaced     DATETIME,
  DateDue        DATETIME,
  DateReceived   DATETIME,
  SupplierID     INTEGER,
  OrderNumber    TEXT,
  ShipperID      INTEGER,
  TrackingNumber TEXT,
  OrderComments  TEXT,
  TotalCost      DOUBLE,
  GrowingSeason  TEXT,
  BrokerID       INTEGER,
  FOREIGN KEY (GrowingSeasonID)
    REFERENCES T_GrowingSeason(GrowingSeasonID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (SupplierID)
    REFERENCES T_Suppliers(SupplierID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (ShipperID)
    REFERENCES T_Shippers(ShipperID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (BrokerID)
    REFERENCES T_Brokers(BrokerID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS T_OrderItems (
  OrderItemID     INTEGER PRIMARY KEY,
  OrderID         INTEGER,
  ItemID          INTEGER,
  ItemCode        TEXT,
  OrderItemTypeID INTEGER,
  Unit            TEXT,
  UnitPrice       DOUBLE,
  NumberOfUnits   TEXT,
  Received        BOOLEAN,
  OrderNote       INTEGER,
  OrderComments   TEXT,
  Leftover        TEXT,
  ToOrder         TEXT,
  FOREIGN KEY (OrderID)
    REFERENCES T_Orders(OrderID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (ItemID)
    REFERENCES T_Items(ItemID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (OrderItemTypeID)
    REFERENCES T_OrderItemTypes(OrderItemTypeID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (OrderNote)
    REFERENCES T_OrderNotes(OrderNoteID)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

/* Optional: Sun lookup. Not shown linked in your diagram, so no FK added.
   If you want to enforce SunConditions against this table, say so and we’ll add it. */
CREATE TABLE IF NOT EXISTS T_Sun (
  SunConditionPic  TEXT PRIMARY KEY,
  SunConditionName TEXT
);

COMMIT;
PRAGMA foreign_keys = ON;

/* Helpful indexes on foreign keys */
CREATE INDEX IF NOT EXISTS ix_Items_TypeID           ON T_Items(TypeID);
CREATE INDEX IF NOT EXISTS ix_Units_UnitCategory     ON T_Units(UnitCategory);
CREATE INDEX IF NOT EXISTS ix_Prices_ItemID          ON T_Prices(ItemID);
CREATE INDEX IF NOT EXISTS ix_Prices_UnitID          ON T_Prices(UnitID);
CREATE INDEX IF NOT EXISTS ix_Plantings_ItemID       ON T_Plantings(ItemID);
CREATE INDEX IF NOT EXISTS ix_Plantings_UnitID       ON T_Plantings(UnitID);
CREATE INDEX IF NOT EXISTS ix_Inventory_ItemID       ON T_Inventory(ItemID);
CREATE INDEX IF NOT EXISTS ix_Inventory_UnitID       ON T_Inventory(UnitID);
CREATE INDEX IF NOT EXISTS ix_Pitch_ItemID           ON T_Pitch(ItemID);
CREATE INDEX IF NOT EXISTS ix_Pitch_UnitID           ON T_Pitch(UnitID);
CREATE INDEX IF NOT EXISTS ix_Orders_GrowingSeasonID ON T_Orders(GrowingSeasonID);
CREATE INDEX IF NOT EXISTS ix_Orders_SupplierID      ON T_Orders(SupplierID);
CREATE INDEX IF NOT EXISTS ix_Orders_ShipperID       ON T_Orders(ShipperID);
CREATE INDEX IF NOT EXISTS ix_Orders_BrokerID        ON T_Orders(BrokerID);
CREATE INDEX IF NOT EXISTS ix_OrderItems_OrderID     ON T_OrderItems(OrderID);
CREATE INDEX IF NOT EXISTS ix_OrderItems_ItemID      ON T_OrderItems(ItemID);
CREATE INDEX IF NOT EXISTS ix_OrderItems_TypeID      ON T_OrderItems(OrderItemTypeID);
CREATE INDEX IF NOT EXISTS ix_OrderItems_OrderNote   ON T_OrderItems(OrderNote);