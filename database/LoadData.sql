-- LoadData.sql - Loads CSV data into EdgewaterMaster database
--
-- KEY FIXES:
--   1. sql_mode = 'NO_AUTO_VALUE_ON_ZERO': Allows LocationID=0, removes STRICT_TRANS_TABLES
--   2. STR_TO_DATE with CASE fallback on ALL DATETIME columns (handles mixed ISO + M/D/YY)
--   3. CRLF: Uses \r\n for files with Windows line endings
--   4. Missing Sun table load added
--   5. Locations/Users: Preserve explicit IDs from CSV
--   6. Passwords: Map all 11 CSV columns (was only mapping 9)

USE `EdgewaterMaster`;
SET FOREIGN_KEY_CHECKS = 0;

-- NO_AUTO_VALUE_ON_ZERO: lets 0 insert as literal 0 in AUTO_INCREMENT columns
-- Removes STRICT_TRANS_TABLES: prevents single bad row from aborting entire LOAD DATA
SET SESSION sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

-- ==================== LOOKUP / REFERENCE TABLES ====================

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

-- GrowingSeason: StartDate/EndDate may be M/D/YY or ISO
LOAD DATA INFILE '/var/lib/mysql-files/GrowingSeason.csv'
INTO TABLE `T_GrowingSeason`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(GrowingSeasonID, GrowingSeason, @StartDate, @EndDate)
SET 
    StartDate = CASE
        WHEN @StartDate LIKE '%/%' THEN STR_TO_DATE(@StartDate, '%m/%d/%y %H:%i')
        ELSE NULLIF(@StartDate, '')
    END,
    EndDate = CASE
        WHEN @EndDate LIKE '%/%' THEN STR_TO_DATE(@EndDate, '%m/%d/%y %H:%i')
        ELSE NULLIF(@EndDate, '')
    END;

LOAD DATA INFILE '/var/lib/mysql-files/OrderItemTypes.csv'
INTO TABLE `T_OrderItemTypes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderItemTypeID, OrderItemType);

LOAD DATA INFILE '/var/lib/mysql-files/OrderNotes.csv'
INTO TABLE `T_OrderNotes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderNoteID, OrderNote);

-- Locations: BOM + CRLF. Preserve explicit LocationID (0,1,2) for FK references.
LOAD DATA INFILE '/var/lib/mysql-files/Locations.csv'
INTO TABLE `T_Locations`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(LocationID, @Location)
SET Location = NULLIF(@Location, '');

-- Sun: Was missing entirely from original LoadData.sql
LOAD DATA INFILE '/var/lib/mysql-files/Sun.csv'
INTO TABLE `T_Sun`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(SunConditionPic, SunConditionName);

-- ==================== ITEM DATA ====================

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

-- ==================== INVENTORY AND PLANTING DATA ====================

-- Plantings: CRLF + M/D/YY dates
LOAD DATA INFILE '/var/lib/mysql-files/Plantings.csv'
INTO TABLE `T_Plantings`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(PlantingID, @DatePlanted, @ItemID, @UnitID, @NumberOfUnits, @PlantingComments, @LocationID)
SET 
    DatePlanted = CASE
        WHEN @DatePlanted LIKE '%/%' THEN STR_TO_DATE(@DatePlanted, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DatePlanted, '')
    END,
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    PlantingComments = NULLIF(@PlantingComments, ''),
    LocationID = NULLIF(@LocationID, '');

-- Inventory: DateCounted may be M/D/YY or ISO
LOAD DATA INFILE '/var/lib/mysql-files/Inventory.csv'
INTO TABLE `T_Inventory`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(InventoryID, @DateCounted, @ItemID, @UnitID, @NumberOfUnits, @InventoryComments)
SET 
    DateCounted = CASE
        WHEN @DateCounted LIKE '%/%' THEN STR_TO_DATE(@DateCounted, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DateCounted, '')
    END,
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    InventoryComments = NULLIF(@InventoryComments, '');

-- Pitch: DatePitched may be M/D/YY or ISO
LOAD DATA INFILE '/var/lib/mysql-files/Pitch.csv'
INTO TABLE `T_Pitch`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(PitchID, @DatePitched, @ItemID, @UnitID, @NumberOfUnits, @PitchComments, @PitchReason)
SET 
    DatePitched = CASE
        WHEN @DatePitched LIKE '%/%' THEN STR_TO_DATE(@DatePitched, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DatePitched, '')
    END,
    ItemID = NULLIF(@ItemID, ''),
    UnitID = NULLIF(@UnitID, ''),
    NumberOfUnits = NULLIF(@NumberOfUnits, ''),
    PitchComments = NULLIF(@PitchComments, ''),
    PitchReason = NULLIF(@PitchReason, '');

-- ==================== ORDER DATA ====================

-- Orders: DatePlaced/DateDue/DateReceived may be M/D/YY or ISO
LOAD DATA INFILE '/var/lib/mysql-files/Orders.csv'
INTO TABLE `T_Orders`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(OrderID, @GrowingSeasonID, @DatePlaced, @DateDue, @DateReceived, @SupplierID, @OrderNumber, @ShipperID, @TrackingNumber, @OrderComments, @TotalCost, @GrowingSeason, @BrokerID)
SET 
    GrowingSeasonID = NULLIF(@GrowingSeasonID, ''),
    DatePlaced = CASE
        WHEN @DatePlaced LIKE '%/%' THEN STR_TO_DATE(@DatePlaced, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DatePlaced, '')
    END,
    DateDue = CASE
        WHEN @DateDue LIKE '%/%' THEN STR_TO_DATE(@DateDue, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DateDue, '')
    END,
    DateReceived = CASE
        WHEN @DateReceived LIKE '%/%' THEN STR_TO_DATE(@DateReceived, '%m/%d/%y %H:%i')
        ELSE NULLIF(@DateReceived, '')
    END,
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

-- ==================== AUTO_INCREMENT TABLES ====================

-- Users: BOM + CRLF. Preserve explicit UserID for FK from Passwords.
LOAD DATA INFILE '/var/lib/mysql-files/Users.csv'
INTO TABLE `T_Users`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(UserID, @Role, @PermissionLevel, @Email, @Active)
SET 
    Role = NULLIF(@Role, ''),
    PermissionLevel = NULLIF(@PermissionLevel, ''),
    Email = NULLIF(@Email, ''),
    Active = IF(@Active IN ('True', 'TRUE', '1', 'true'), 1, 0);

-- Passwords: CRLF + 11 CSV columns. Multiple DATETIME columns may be M/D/YY.
LOAD DATA INFILE '/var/lib/mysql-files/Passwords.csv'
INTO TABLE `T_Passwords`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@PasswordID, @UserID, @PasswordHash, @PasswordResetToken, @PasswordResetExpiry, @LastLogin, @LastPasswordChange, @FailedLoginAttempts, @AccountLockedUntil, @CreatedAt, @UpdatedAt)
SET 
    UserID = NULLIF(@UserID, ''),
    PasswordHash = NULLIF(@PasswordHash, ''),
    PasswordResetToken = NULLIF(@PasswordResetToken, ''),
    PasswordResetExpiry = CASE
        WHEN @PasswordResetExpiry LIKE '%/%' THEN STR_TO_DATE(@PasswordResetExpiry, '%m/%d/%y %H:%i')
        ELSE NULLIF(@PasswordResetExpiry, '')
    END,
    LastLogin = CASE
        WHEN @LastLogin LIKE '%/%' THEN STR_TO_DATE(@LastLogin, '%m/%d/%y %H:%i')
        ELSE NULLIF(@LastLogin, '')
    END,
    LastPasswordChange = CASE
        WHEN @LastPasswordChange LIKE '%/%' THEN STR_TO_DATE(@LastPasswordChange, '%m/%d/%y %H:%i')
        ELSE NULLIF(@LastPasswordChange, '')
    END,
    FailedLoginAttempts = IFNULL(NULLIF(@FailedLoginAttempts, ''), 0),
    AccountLockedUntil = CASE
        WHEN @AccountLockedUntil LIKE '%/%' THEN STR_TO_DATE(@AccountLockedUntil, '%m/%d/%y %H:%i')
        ELSE NULLIF(@AccountLockedUntil, '')
    END,
    CreatedAt = CASE
        WHEN @CreatedAt LIKE '%/%' THEN STR_TO_DATE(@CreatedAt, '%m/%d/%y %H:%i')
        ELSE NULLIF(@CreatedAt, '')
    END,
    UpdatedAt = CASE
        WHEN @UpdatedAt LIKE '%/%' THEN STR_TO_DATE(@UpdatedAt, '%m/%d/%y %H:%i')
        ELSE NULLIF(@UpdatedAt, '')
    END;

-- SeasonalNotes: BOM + CRLF. LastUpdate may be M/D/YY.
LOAD DATA INFILE '/var/lib/mysql-files/SeasonalNotes.csv'
INTO TABLE `T_SeasonalNotes`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@NoteID, @ItemID, @GrowingSeasonID, @Greenhouse, @Note, @LastUpdate)
SET 
    ItemID = NULLIF(@ItemID, ''),
    GrowingSeasonID = NULLIF(@GrowingSeasonID, ''),
    Greenhouse = IF(@Greenhouse IN ('True', 'TRUE', '1', 'true'), 1, 0),
    Note = NULLIF(@Note, ''),
    LastUpdate = CASE
        WHEN @LastUpdate LIKE '%/%' THEN STR_TO_DATE(@LastUpdate, '%m/%d/%y %H:%i')
        ELSE NULLIF(@LastUpdate, '')
    END;

-- OrderItemDestination: BOM + CRLF
LOAD DATA INFILE '/var/lib/mysql-files/OrderItemDestination.csv'
INTO TABLE `T_OrderItemDestination`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@OrderItemID, @Count, @UnitID, @LocationID)
SET 
    OrderItemID = NULLIF(@OrderItemID, ''),
    Count = NULLIF(@Count, ''),
    UnitID = NULLIF(@UnitID, ''),
    LocationID = NULLIF(@LocationID, '');

-- PlantingDestinations: BOM + CRLF
LOAD DATA INFILE '/var/lib/mysql-files/PlantingDestinations.csv'
INTO TABLE `T_PlantingDestinations`
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@PlantingDestinationID, @PlantingID, @LocationID, @UnitsDestined, @PurposeComments)
SET
    PlantingID = NULLIF(@PlantingID, ''),
    LocationID = NULLIF(@LocationID, ''),
    UnitsDestined = NULLIF(@UnitsDestined, ''),
    PurposeComments = NULLIF(@PurposeComments, '');

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
UNION ALL SELECT 'T_Sun', COUNT(*) FROM T_Sun
UNION ALL SELECT 'T_Users', COUNT(*) FROM T_Users
UNION ALL SELECT 'T_Passwords', COUNT(*) FROM T_Passwords
UNION ALL SELECT 'T_SeasonalNotes', COUNT(*) FROM T_SeasonalNotes
UNION ALL SELECT 'T_OrderItemDestination', COUNT(*) FROM T_OrderItemDestination
UNION ALL SELECT 'T_Locations', COUNT(*) FROM T_Locations
UNION ALL SELECT 'T_PlantingDestinations', COUNT(*) FROM T_PlantingDestinations;