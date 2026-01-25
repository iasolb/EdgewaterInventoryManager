-- LoadData.sql - Loads CSV data into EdgewaterMaster database

USE `EdgewaterMaster`;
SET FOREIGN_KEY_CHECKS = 0;

-- Load lookup and reference tables first
LOAD DATA INFILE '/var/lib/mysql-files/ItemType.csv'
INTO TABLE `T_ItemType`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(TypeID, Type);

LOAD DATA INFILE '/var/lib/mysql-files/UnitCategory.csv'
INTO TABLE `T_UnitCategory`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(UnitCategoryID, UnitCategory);

LOAD DATA INFILE '/var/lib/mysql-files/Units.csv'
INTO TABLE `T_Units`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(UnitID, UnitType, UnitSize, @UnitCategoryID)
SET UnitCategoryID = NULLIF(@UnitCategoryID, '');

LOAD DATA INFILE '/var/lib/mysql-files/Brokers.csv'
INTO TABLE `T_Brokers`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(BrokerID, Broker, @BrokerComments)
SET BrokerComments = NULLIF(@BrokerComments, '');

LOAD DATA INFILE '/var/lib/mysql-files/Shippers.csv'
INTO TABLE `T_Shippers`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(ShipperID, Shipper, @AccountNumber, @Phone, @ContactPerson, @Address1, @Address2, @City, @State, @Zip, @ShipperComments)
SET 
    AccountNumber = NULLIF(@AccountNumber, ''),
    Phone = NULLIF(@Phone, ''),
    ContactPerson = NULLIF(@ContactPerson, ''),
    Address1 = NULLIF(@Address1, ''),
    Address2 = NULLIF(@Address2, ''),
    City = NULLIF(@City, ''),
    State = NULLIF(@State, ''),
    Zip = NULLIF(@Zip, ''),
    ShipperComments = NULLIF(@ShipperComments, '');

LOAD DATA INFILE '/var/lib/mysql-files/Suppliers.csv'
INTO TABLE `T_Suppliers`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(SupplierID, Supplier, @AccountNumber, @Phone, @Fax, @WebSite, @Email, @ContactPerson, @Address1, @Address2, @City, @State, @Zip, @SupplierComments, @SupplierType)
SET 
    AccountNumber = NULLIF(@AccountNumber, ''),
    Phone = NULLIF(@Phone, ''),
    Fax = NULLIF(@Fax, ''),
    WebSite = NULLIF(@WebSite, ''),
    Email = NULLIF(@Email, ''),
    ContactPerson = NULLIF(@ContactPerson, ''),
    Address1 = NULLIF(@Address1, ''),
    Address2 = NULLIF(@Address2, ''),
    City = NULLIF(@City, ''),
    State = NULLIF(@State, ''),
    Zip = NULLIF(@Zip, ''),
    SupplierComments = NULLIF(@SupplierComments, ''),
    SupplierType = NULLIF(@SupplierType, '');

LOAD DATA INFILE '/var/lib/mysql-files/GrowingSeason.csv'
INTO TABLE `T_GrowingSeason`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(GrowingSeasonID, GrowingSeason, @StartDate, @EndDate)
SET 
    StartDate = NULLIF(@StartDate, ''),
    EndDate = NULLIF(@EndDate, '');

LOAD DATA INFILE '/var/lib/mysql-files/OrderItemTypes.csv'
INTO TABLE `T_OrderItemTypes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderItemTypeID, OrderItemType);

LOAD DATA INFILE '/var/lib/mysql-files/OrderNotes.csv'
INTO TABLE `T_OrderNotes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderNoteID, OrderNote);

-- Load T_Locations before T_OrderItemDestination (dependency)
LOAD DATA INFILE '/var/lib/mysql-files/Locations.csv'
INTO TABLE `T_Locations`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@LocationID, @Location)
SET Location = NULLIF(@Location, '');

-- Load item data
LOAD DATA INFILE '/var/lib/mysql-files/Items.csv'
INTO TABLE `T_Items`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(ItemID, @Inactive, @Item, @Variety, @Color, @ShouldStock, @TypeID, @LabelDescription, @Definition, @PictureLayout, @PictureLink, @SunConditions)
SET 
    Inactive = IF(@Inactive IN ('True', 'TRUE', '1', 'true'), 1, 0),
    Item = NULLIF(@Item, ''),
    Variety = NULLIF(@Variety, ''),
    Color = NULLIF(@Color, ''),
    ShouldStock = IF(@ShouldStock IN ('True', 'TRUE', '1', 'true'), 1, 0),
    TypeID = NULLIF(@TypeID, ''),
    LabelDescription = NULLIF(@LabelDescription, ''),
    Definition = NULLIF(@Definition, ''),
    PictureLayout = NULLIF(@PictureLayout, ''),
    PictureLink = NULLIF(@PictureLink, ''),
    SunConditions = NULLIF(@SunConditions, '');

LOAD DATA INFILE '/var/lib/mysql-files/Prices.csv'
INTO TABLE `T_Prices`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(PriceID, @ItemID, @UnitID, @UnitPrice, @Year)
SET 
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    UnitPrice = NULLIF(@UnitPrice, ''),
    Year = NULLIF(@Year, '');

-- Load inventory and planting data
LOAD DATA INFILE '/var/lib/mysql-files/Plantings.csv'
INTO TABLE `T_Plantings`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(PlantingID, @DatePlanted, @ItemID, @UnitID, @NumberOfUnits, @PlantingComments)
SET 
    DatePlanted = NULLIF(@DatePlanted, ''),
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    PlantingComments = NULLIF(@PlantingComments, '');

LOAD DATA INFILE '/var/lib/mysql-files/Inventory.csv'
INTO TABLE `T_Inventory`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(InventoryID, @DateCounted, @ItemID, @UnitID, @NumberOfUnits, @InventoryComments)
SET 
    DateCounted = NULLIF(@DateCounted, ''),
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    InventoryComments = NULLIF(@InventoryComments, '');

LOAD DATA INFILE '/var/lib/mysql-files/Pitch.csv'
INTO TABLE `T_Pitch`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(PitchID, @DatePitched, @ItemID, @UnitID, @NumberOfUnits, @PitchComments, @PitchReason)
SET 
    DatePitched = NULLIF(@DatePitched, ''),
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    PitchComments = NULLIF(@PitchComments, ''),
    PitchReason = NULLIF(@PitchReason, '');

-- Load order data
LOAD DATA INFILE '/var/lib/mysql-files/Orders.csv'
INTO TABLE `T_Orders`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderID, @GrowingSeasonID, @DatePlaced, @DateDue, @DateReceived, @SupplierID, @OrderNumber, @ShipperID, @TrackingNumber, @OrderComments, @TotalCost, @GrowingSeason, @BrokerID)
SET 
    GrowingSeasonID = NULLIF(@GrowingSeasonID, ''),
    DatePlaced = NULLIF(@DatePlaced, ''),
    DateDue = NULLIF(@DateDue, ''),
    DateReceived = NULLIF(@DateReceived, ''),
    SupplierID = NULLIF(@SupplierID, ''),
    OrderNumber = NULLIF(@OrderNumber, ''),
    ShipperID = NULLIF(@ShipperID, ''),
    TrackingNumber = NULLIF(@TrackingNumber, ''),
    OrderComments = NULLIF(@OrderComments, ''),
    TotalCost = NULLIF(@TotalCost, ''),
    GrowingSeason = NULLIF(@GrowingSeason, ''),
    BrokerID = NULLIF(@BrokerID, '');

LOAD DATA INFILE '/var/lib/mysql-files/OrderItems.csv'
INTO TABLE `T_OrderItems`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderItemID, @OrderID, @ItemID, @ItemCode, @OrderItemTypeID, @Unit, @UnitPrice, @NumberOfUnits, @Received, @OrderNote, @OrderComments, @Leftover, @ToOrder)
SET 
    OrderID = NULLIF(@OrderID, ''),
    ItemID = NULLIF(@ItemID, ''),
    ItemCode = NULLIF(@ItemCode, ''),
    OrderItemTypeID = NULLIF(@OrderItemTypeID, ''),
    Unit = NULLIF(@Unit, ''),
    UnitPrice = NULLIF(@UnitPrice, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    Received = IF(@Received IN ('True', 'TRUE', '1', 'true'), 1, 0),
    OrderNote = NULLIF(@OrderNote, ''),
    OrderComments = NULLIF(@OrderComments, ''),
    Leftover = NULLIF(@Leftover, ''),
    ToOrder = NULLIF(@ToOrder, '');

-- Load AUTO_INCREMENT tables (skip primary key column)
LOAD DATA INFILE '/var/lib/mysql-files/Users.csv'
INTO TABLE `T_Users`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@UserID, @Role, @PermissionLevel, @Email, @Active)
SET 
    Role = NULLIF(@Role, ''),
    PermissionLevel = NULLIF(@PermissionLevel, ''),
    Email = NULLIF(@Email, ''),
    Active = IF(@Active IN ('True', 'TRUE', '1', 'true'), 1, 0);

LOAD DATA INFILE '/var/lib/mysql-files/Passwords.csv'
INTO TABLE `T_Passwords`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@PasswordID, @UserID, @PasswordHash, @PasswordResetToken, @PasswordResetExpiry, @LastLogin, @LastPasswordChange, @FailedLoginAttempts, @AccountLockedUntil)
SET 
    UserID = NULLIF(@UserID, ''),
    PasswordHash = NULLIF(@PasswordHash, ''),
    PasswordResetToken = NULLIF(@PasswordResetToken, ''),
    PasswordResetExpiry = NULLIF(@PasswordResetExpiry, ''),
    LastLogin = NULLIF(@LastLogin, ''),
    LastPasswordChange = NULLIF(@LastPasswordChange, ''),
    FailedLoginAttempts = IFNULL(NULLIF(@FailedLoginAttempts, ''), 0),
    AccountLockedUntil = NULLIF(@AccountLockedUntil, '');

LOAD DATA INFILE '/var/lib/mysql-files/SeasonalNotes.csv'
INTO TABLE `T_SeasonalNotes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@NoteID, @ItemID, @GrowingSeasonID, @Greenhouse, @Note, @LastUpdate)
SET 
    ItemID = NULLIF(@ItemID, ''),
    GrowingSeasonID = NULLIF(@GrowingSeasonID, ''),
    Greenhouse = IF(@Greenhouse IN ('True', 'TRUE', '1', 'true'), 1, 0),
    Note = NULLIF(@Note, ''),
    LastUpdate = NULLIF(@LastUpdate, '');

LOAD DATA INFILE '/var/lib/mysql-files/OrderItemDestination.csv'
INTO TABLE `T_OrderItemDestination`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@OrderItemID, @Count, @UnitID, @LocationID)
SET 
    OrderItemID = NULLIF(@OrderItemID, ''),
    Count = NULLIF(@Count, ''),
    UnitID = NULLIF(@UnitID, ''),
    LocationID = NULLIF(@LocationID, '');


SET FOREIGN_KEY_CHECKS = 1;

-- Display load summary
SELECT 'Data Load Complete!' as Status;
SELECT 'T_ItemType' as TableName, COUNT(*) as RecordCount FROM T_ItemType
UNION ALL SELECT 'T_UnitCategory', COUNT(*) FROM T_UnitCategory
UNION ALL SELECT 'T_Units', COUNT(*) FROM T_Units
UNION ALL SELECT 'T_Brokers', COUNT(*) FROM T_Brokers
UNION ALL SELECT 'T_Shippers', COUNT(*) FROM T_Shippers
UNION ALL SELECT 'T_Suppliers', COUNT(*) FROM T_Suppliers
UNION ALL SELECT 'T_GrowingSeason', COUNT(*) FROM T_GrowingSeason
UNION ALL SELECT 'T_OrderItemTypes', COUNT(*) FROM T_OrderItemTypes
UNION ALL SELECT 'T_OrderNotes', COUNT(*) FROM T_OrderNotes
UNION ALL SELECT 'T_Items', COUNT(*) FROM T_Items
UNION ALL SELECT 'T_Prices', COUNT(*) FROM T_Prices
UNION ALL SELECT 'T_Plantings', COUNT(*) FROM T_Plantings
UNION ALL SELECT 'T_Inventory', COUNT(*) FROM T_Inventory
UNION ALL SELECT 'T_Pitch', COUNT(*) FROM T_Pitch
UNION ALL SELECT 'T_Orders', COUNT(*) FROM T_Orders
UNION ALL SELECT 'T_OrderItems', COUNT(*) FROM T_OrderItems
UNION ALL SELECT 'T_Users', COUNT(*) FROM T_Users
UNION ALL SELECT 'T_Passwords', COUNT(*) FROM T_Passwords
UNION ALL SELECT 'T_SeasonalNotes', COUNT(*) FROM T_SeasonalNotes
UNION ALL SELECT 'T_OrderItemDestination', COUNT(*) FROM T_OrderItemDestination
UNION ALL SELECT 'T_Locations', COUNT(*) FROM T_Locations;
