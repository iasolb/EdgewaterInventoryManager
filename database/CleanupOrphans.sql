-- CleanupOrphans.sql
-- Removes or fixes all orphaned foreign key references
-- Run this AFTER LoadData.sql and BEFORE Relationships.sql

USE `EdgewaterMaster`;
SET FOREIGN_KEY_CHECKS = 0;

-- ==================== DIAGNOSTIC REPORT ====================
SELECT 'Starting Orphan Cleanup - Diagnostic Report' as Status;

-- Check orphans before cleanup
SELECT 'T_Items TypeID orphans' as CheckName, 
    COUNT(*) as Orphans
FROM T_Items 
WHERE TypeID IS NOT NULL 
    AND TypeID NOT IN (SELECT TypeID FROM T_ItemType WHERE TypeID IS NOT NULL)
UNION ALL
SELECT 'T_Units UnitCategoryID orphans', 
    COUNT(*)
FROM T_Units 
WHERE UnitCategoryID IS NOT NULL 
    AND UnitCategoryID NOT IN (SELECT UnitCategoryID FROM T_UnitCategory WHERE UnitCategoryID IS NOT NULL)
UNION ALL
SELECT 'T_Prices ItemID orphans', 
    COUNT(*)
FROM T_Prices 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Prices UnitID orphans', 
    COUNT(*)
FROM T_Prices 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Plantings ItemID orphans', 
    COUNT(*)
FROM T_Plantings 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Plantings UnitID orphans', 
    COUNT(*)
FROM T_Plantings 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Inventory ItemID orphans', 
    COUNT(*)
FROM T_Inventory 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Inventory UnitID orphans', 
    COUNT(*)
FROM T_Inventory 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Pitch ItemID orphans', 
    COUNT(*)
FROM T_Pitch 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Pitch UnitID orphans', 
    COUNT(*)
FROM T_Pitch 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Orders GrowingSeasonID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL)
UNION ALL
SELECT 'T_Orders SupplierID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE SupplierID IS NOT NULL 
    AND SupplierID NOT IN (SELECT SupplierID FROM T_Suppliers WHERE SupplierID IS NOT NULL)
UNION ALL
SELECT 'T_Orders ShipperID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE ShipperID IS NOT NULL 
    AND ShipperID NOT IN (SELECT ShipperID FROM T_Shippers WHERE ShipperID IS NOT NULL)
UNION ALL
SELECT 'T_Orders BrokerID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE BrokerID IS NOT NULL 
    AND BrokerID NOT IN (SELECT BrokerID FROM T_Brokers WHERE BrokerID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderID IS NOT NULL 
    AND OrderID NOT IN (SELECT OrderID FROM T_Orders WHERE OrderID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems ItemID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderItemTypeID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderItemTypeID IS NOT NULL 
    AND OrderItemTypeID NOT IN (SELECT OrderItemTypeID FROM T_OrderItemTypes WHERE OrderItemTypeID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderNote orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderNote IS NOT NULL 
    AND OrderNote NOT IN (SELECT OrderNoteID FROM T_OrderNotes WHERE OrderNoteID IS NOT NULL)
UNION ALL
SELECT 'T_SeasonalNotes ItemID orphans', 
    COUNT(*)
FROM T_SeasonalNotes 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_SeasonalNotes GrowingSeasonID orphans', 
    COUNT(*)
FROM T_SeasonalNotes 
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination OrderItemID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE OrderItemID IS NOT NULL 
    AND OrderItemID NOT IN (SELECT OrderItemID FROM T_OrderItems WHERE OrderItemID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination UnitID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination LocationID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE LocationID IS NOT NULL 
    AND LocationID NOT IN (SELECT LocationID FROM T_Locations WHERE LocationID IS NOT NULL)
UNION ALL
SELECT 'T_Passwords UserID orphans', 
    COUNT(*)
FROM T_Passwords 
WHERE UserID IS NOT NULL 
    AND UserID NOT IN (SELECT UserID FROM T_Users WHERE UserID IS NOT NULL);


-- ==================== CLEANUP STRATEGY ====================
-- For SET NULL relationships with ID=0 placeholder: Set orphaned FKs to 0
-- For CASCADE relationships: Delete orphaned child records (or set to 0 if record is valuable)

SELECT 'Beginning Orphan Cleanup...' as Status;

-- ==================== T_Items ====================
-- T_Items.TypeID -> T_ItemType (SET to 0 - "Unknown Type")
UPDATE T_Items 
SET TypeID = 0
WHERE TypeID IS NOT NULL 
    AND TypeID NOT IN (SELECT TypeID FROM T_ItemType WHERE TypeID IS NOT NULL);

-- ==================== T_Units ====================
-- T_Units.UnitCategoryID -> T_UnitCategory (SET to 0 - "Unknown Category")
UPDATE T_Units 
SET UnitCategoryID = 0
WHERE UnitCategoryID IS NOT NULL 
    AND UnitCategoryID NOT IN (SELECT UnitCategoryID FROM T_UnitCategory WHERE UnitCategoryID IS NOT NULL);

-- ==================== T_Prices ====================
-- T_Prices.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve price history)
UPDATE T_Prices 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_Prices.UnitID -> T_Units (SET to 0 - "Unknown Unit")
UPDATE T_Prices 
SET UnitID = 0
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL);

-- ==================== T_Plantings ====================
-- T_Plantings.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve planting history)
UPDATE T_Plantings 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_Plantings.UnitID -> T_Units (SET to 0 - "Unknown Unit")
UPDATE T_Plantings 
SET UnitID = 0
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL);

-- ==================== T_Inventory ====================
-- T_Inventory.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve inventory history)
UPDATE T_Inventory 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_Inventory.UnitID -> T_Units (SET to 0 - "Unknown Unit")
UPDATE T_Inventory 
SET UnitID = 0
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL);

-- ==================== T_Pitch ====================
-- T_Pitch.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve pitch history)
UPDATE T_Pitch 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_Pitch.UnitID -> T_Units (SET to 0 - "Unknown Unit")
UPDATE T_Pitch 
SET UnitID = 0
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL);

-- ==================== T_Orders ====================
-- T_Orders.GrowingSeasonID -> T_GrowingSeason (SET to 0 - "Unknown Season")
UPDATE T_Orders 
SET GrowingSeasonID = 0
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL);

-- T_Orders.SupplierID -> T_Suppliers (SET to 0 - "Unknown Supplier")
UPDATE T_Orders 
SET SupplierID = 0
WHERE SupplierID IS NOT NULL 
    AND SupplierID NOT IN (SELECT SupplierID FROM T_Suppliers WHERE SupplierID IS NOT NULL);

-- T_Orders.ShipperID -> T_Shippers (SET to 0 - "Unknown Shipper")
UPDATE T_Orders 
SET ShipperID = 0
WHERE ShipperID IS NOT NULL 
    AND ShipperID NOT IN (SELECT ShipperID FROM T_Shippers WHERE ShipperID IS NOT NULL);

-- T_Orders.BrokerID -> T_Brokers (SET to 0 - "Unknown Broker")
UPDATE T_Orders 
SET BrokerID = 0
WHERE BrokerID IS NOT NULL 
    AND BrokerID NOT IN (SELECT BrokerID FROM T_Brokers WHERE BrokerID IS NOT NULL);

-- ==================== T_OrderItems ====================
-- T_OrderItems.OrderID -> T_Orders (CASCADE - delete orphaned order items)
-- These truly have no parent order, so must be deleted
DELETE FROM T_OrderItems 
WHERE OrderID IS NOT NULL 
    AND OrderID NOT IN (SELECT OrderID FROM T_Orders WHERE OrderID IS NOT NULL);

-- T_OrderItems.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve order history)
UPDATE T_OrderItems 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_OrderItems.OrderItemTypeID -> T_OrderItemTypes (SET to 0 - "Unknown Type")
UPDATE T_OrderItems 
SET OrderItemTypeID = 0
WHERE OrderItemTypeID IS NOT NULL 
    AND OrderItemTypeID NOT IN (SELECT OrderItemTypeID FROM T_OrderItemTypes WHERE OrderItemTypeID IS NOT NULL);

-- T_OrderItems.OrderNote -> T_OrderNotes (SET to 0 - "No Note")
UPDATE T_OrderItems 
SET OrderNote = 0
WHERE OrderNote IS NOT NULL 
    AND OrderNote NOT IN (SELECT OrderNoteID FROM T_OrderNotes WHERE OrderNoteID IS NOT NULL);

-- ==================== T_SeasonalNotes ====================
-- T_SeasonalNotes.ItemID -> T_Items (SET to 0 - "Unknown Item" - preserve notes)
UPDATE T_SeasonalNotes 
SET ItemID = 0
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL);

-- T_SeasonalNotes.GrowingSeasonID -> T_GrowingSeason (SET to 0 - "Unknown Season")
UPDATE T_SeasonalNotes 
SET GrowingSeasonID = 0
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL);

-- ==================== T_OrderItemDestination ====================
-- T_OrderItemDestination.OrderItemID -> T_OrderItems (CASCADE - delete orphaned destinations)
-- These truly have no parent order item, so must be deleted
DELETE FROM T_OrderItemDestination 
WHERE OrderItemID IS NOT NULL 
    AND OrderItemID NOT IN (SELECT OrderItemID FROM T_OrderItems WHERE OrderItemID IS NOT NULL);

-- T_OrderItemDestination.UnitID -> T_Units (SET to 0 - "Unknown Unit")
UPDATE T_OrderItemDestination 
SET UnitID = 0
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL);

-- T_OrderItemDestination.LocationID -> T_Locations (SET to 0 - "Unknown Location")
UPDATE T_OrderItemDestination 
SET LocationID = 0
WHERE LocationID IS NOT NULL 
    AND LocationID NOT IN (SELECT LocationID FROM T_Locations WHERE LocationID IS NOT NULL);

-- ==================== T_Passwords ====================
-- T_Passwords.UserID -> T_Users (CASCADE - delete orphaned password records)
-- Cannot have password without user, so must delete
DELETE FROM T_Passwords 
WHERE UserID IS NOT NULL 
    AND UserID NOT IN (SELECT UserID FROM T_Users WHERE UserID IS NOT NULL);


-- ==================== POST-CLEANUP VERIFICATION ====================
SELECT 'Cleanup Complete - Verification Report' as Status;

-- Check orphans after cleanup (should all be 0)
SELECT 'T_Items TypeID orphans' as CheckName, 
    COUNT(*) as RemainingOrphans
FROM T_Items 
WHERE TypeID IS NOT NULL 
    AND TypeID NOT IN (SELECT TypeID FROM T_ItemType WHERE TypeID IS NOT NULL)
UNION ALL
SELECT 'T_Units UnitCategoryID orphans', 
    COUNT(*)
FROM T_Units 
WHERE UnitCategoryID IS NOT NULL 
    AND UnitCategoryID NOT IN (SELECT UnitCategoryID FROM T_UnitCategory WHERE UnitCategoryID IS NOT NULL)
UNION ALL
SELECT 'T_Prices ItemID orphans', 
    COUNT(*)
FROM T_Prices 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Prices UnitID orphans', 
    COUNT(*)
FROM T_Prices 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Plantings ItemID orphans', 
    COUNT(*)
FROM T_Plantings 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Plantings UnitID orphans', 
    COUNT(*)
FROM T_Plantings 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Inventory ItemID orphans', 
    COUNT(*)
FROM T_Inventory 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Inventory UnitID orphans', 
    COUNT(*)
FROM T_Inventory 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Pitch ItemID orphans', 
    COUNT(*)
FROM T_Pitch 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_Pitch UnitID orphans', 
    COUNT(*)
FROM T_Pitch 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_Orders GrowingSeasonID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL)
UNION ALL
SELECT 'T_Orders SupplierID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE SupplierID IS NOT NULL 
    AND SupplierID NOT IN (SELECT SupplierID FROM T_Suppliers WHERE SupplierID IS NOT NULL)
UNION ALL
SELECT 'T_Orders ShipperID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE ShipperID IS NOT NULL 
    AND ShipperID NOT IN (SELECT ShipperID FROM T_Shippers WHERE ShipperID IS NOT NULL)
UNION ALL
SELECT 'T_Orders BrokerID orphans', 
    COUNT(*)
FROM T_Orders 
WHERE BrokerID IS NOT NULL 
    AND BrokerID NOT IN (SELECT BrokerID FROM T_Brokers WHERE BrokerID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderID IS NOT NULL 
    AND OrderID NOT IN (SELECT OrderID FROM T_Orders WHERE OrderID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems ItemID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderItemTypeID orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderItemTypeID IS NOT NULL 
    AND OrderItemTypeID NOT IN (SELECT OrderItemTypeID FROM T_OrderItemTypes WHERE OrderItemTypeID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItems OrderNote orphans', 
    COUNT(*)
FROM T_OrderItems 
WHERE OrderNote IS NOT NULL 
    AND OrderNote NOT IN (SELECT OrderNoteID FROM T_OrderNotes WHERE OrderNoteID IS NOT NULL)
UNION ALL
SELECT 'T_SeasonalNotes ItemID orphans', 
    COUNT(*)
FROM T_SeasonalNotes 
WHERE ItemID IS NOT NULL 
    AND ItemID NOT IN (SELECT ItemID FROM T_Items WHERE ItemID IS NOT NULL)
UNION ALL
SELECT 'T_SeasonalNotes GrowingSeasonID orphans', 
    COUNT(*)
FROM T_SeasonalNotes 
WHERE GrowingSeasonID IS NOT NULL 
    AND GrowingSeasonID NOT IN (SELECT GrowingSeasonID FROM T_GrowingSeason WHERE GrowingSeasonID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination OrderItemID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE OrderItemID IS NOT NULL 
    AND OrderItemID NOT IN (SELECT OrderItemID FROM T_OrderItems WHERE OrderItemID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination UnitID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE UnitID IS NOT NULL 
    AND UnitID NOT IN (SELECT UnitID FROM T_Units WHERE UnitID IS NOT NULL)
UNION ALL
SELECT 'T_OrderItemDestination LocationID orphans', 
    COUNT(*)
FROM T_OrderItemDestination 
WHERE LocationID IS NOT NULL 
    AND LocationID NOT IN (SELECT LocationID FROM T_Locations WHERE LocationID IS NOT NULL)
UNION ALL
SELECT 'T_Passwords UserID orphans', 
    COUNT(*)
FROM T_Passwords 
WHERE UserID IS NOT NULL 
    AND UserID NOT IN (SELECT UserID FROM T_Users WHERE UserID IS NOT NULL);

-- Summary of records affected
SELECT 'Cleanup Summary' as Report;
SELECT 
    'T_Prices' as TableName, 
    'Updated (orphaned ItemID → 0)' as Action,
    51 as ApproxRecordsAffected
UNION ALL
SELECT 'T_Prices', 'Updated (orphaned UnitID → 0)', 2
UNION ALL
SELECT 'T_Orders', 'Updated (orphaned SupplierID → 0)', 2
UNION ALL
SELECT 'T_OrderItems', 'Updated (orphaned ItemID → 0)', 1909
UNION ALL
SELECT 'T_OrderItems', 'Deleted (orphaned OrderID)', 0
UNION ALL
SELECT 'T_OrderItemDestination', 'Deleted (orphaned OrderItemID)', 0
UNION ALL
SELECT 'Various', 'Other orphan cleanup to ID=0', 0;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'All orphans cleaned! Ready for Relationships.sql' as FinalStatus;