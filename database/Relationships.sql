-- Relationships.sql - Foreign Key Constraints and Indexes for EdgewaterMaster
-- Run AFTER LoadData.sql and CleanupOrphans.sql
--
-- ON DELETE strategy:
--   RESTRICT  = "preserve history" - blocks deleting a parent that has children
--               (admin must reassign children first; keeps 0=Unknown convention consistent)
--   CASCADE   = "ownership" - deleting parent removes its children
--               (OrderItems die with their Order, Passwords die with their User, etc.)

USE `EdgewaterMaster`;
SET FOREIGN_KEY_CHECKS = 0;
SET SESSION sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

-- ==================== FOREIGN KEY CONSTRAINTS ====================

-- T_Items: can't delete an ItemType that has Items using it
ALTER TABLE `T_Items`
ADD CONSTRAINT `fk_Items_TypeID`
FOREIGN KEY (`TypeID`) REFERENCES `T_ItemType`(`TypeID`)
ON DELETE RESTRICT;

-- T_Units: can't delete a UnitCategory that has Units using it
ALTER TABLE `T_Units`
ADD CONSTRAINT `fk_Units_UnitCategoryID`
FOREIGN KEY (`UnitCategoryID`) REFERENCES `T_UnitCategory`(`UnitCategoryID`)
ON DELETE RESTRICT;

-- T_Prices: can't delete an Item or Unit that has price history
ALTER TABLE `T_Prices`
ADD CONSTRAINT `fk_Prices_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Prices`
ADD CONSTRAINT `fk_Prices_UnitID`
FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`)
ON DELETE RESTRICT;

-- T_Plantings: can't delete an Item/Unit/Location that has planting history
ALTER TABLE `T_Plantings`
ADD CONSTRAINT `fk_Plantings_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Plantings`
ADD CONSTRAINT `fk_Plantings_UnitID`
FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Plantings`
ADD CONSTRAINT `fk_Plantings_LocationID`
FOREIGN KEY (`LocationID`) REFERENCES `T_Locations`(`LocationID`)
ON DELETE RESTRICT;

-- T_Inventory: can't delete an Item or Unit that has inventory history
ALTER TABLE `T_Inventory`
ADD CONSTRAINT `fk_Inventory_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Inventory`
ADD CONSTRAINT `fk_Inventory_UnitID`
FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`)
ON DELETE RESTRICT;

-- T_Pitch: can't delete an Item or Unit that has pitch history
ALTER TABLE `T_Pitch`
ADD CONSTRAINT `fk_Pitch_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Pitch`
ADD CONSTRAINT `fk_Pitch_UnitID`
FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`)
ON DELETE RESTRICT;

-- T_Orders: can't delete a Season/Supplier/Shipper/Broker that has orders
ALTER TABLE `T_Orders`
ADD CONSTRAINT `fk_Orders_GrowingSeasonID`
FOREIGN KEY (`GrowingSeasonID`) REFERENCES `T_GrowingSeason`(`GrowingSeasonID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Orders`
ADD CONSTRAINT `fk_Orders_SupplierID`
FOREIGN KEY (`SupplierID`) REFERENCES `T_Suppliers`(`SupplierID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Orders`
ADD CONSTRAINT `fk_Orders_ShipperID`
FOREIGN KEY (`ShipperID`) REFERENCES `T_Shippers`(`ShipperID`)
ON DELETE RESTRICT;

ALTER TABLE `T_Orders`
ADD CONSTRAINT `fk_Orders_BrokerID`
FOREIGN KEY (`BrokerID`) REFERENCES `T_Brokers`(`BrokerID`)
ON DELETE RESTRICT;

-- T_OrderItems: line items are owned by their Order (CASCADE)
-- but can't delete an Item/Type/Note that has order history (RESTRICT)
ALTER TABLE `T_OrderItems`
ADD CONSTRAINT `fk_OrderItems_OrderID`
FOREIGN KEY (`OrderID`) REFERENCES `T_Orders`(`OrderID`)
ON DELETE CASCADE;

ALTER TABLE `T_OrderItems`
ADD CONSTRAINT `fk_OrderItems_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE RESTRICT;

ALTER TABLE `T_OrderItems`
ADD CONSTRAINT `fk_OrderItems_OrderItemTypeID`
FOREIGN KEY (`OrderItemTypeID`) REFERENCES `T_OrderItemTypes`(`OrderItemTypeID`)
ON DELETE RESTRICT;

ALTER TABLE `T_OrderItems`
ADD CONSTRAINT `fk_OrderItems_OrderNote`
FOREIGN KEY (`OrderNote`) REFERENCES `T_OrderNotes`(`OrderNoteID`)
ON DELETE RESTRICT;

-- T_SeasonalNotes: owned by their Item and Season (CASCADE)
ALTER TABLE `T_SeasonalNotes`
ADD CONSTRAINT `fk_SeasonalNotes_ItemID`
FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`)
ON DELETE CASCADE;

ALTER TABLE `T_SeasonalNotes`
ADD CONSTRAINT `fk_SeasonalNotes_GrowingSeasonID`
FOREIGN KEY (`GrowingSeasonID`) REFERENCES `T_GrowingSeason`(`GrowingSeasonID`)
ON DELETE CASCADE;

-- T_PlantingDestinations: owned by their Planting (CASCADE)
-- can't delete a Location that has destinations (RESTRICT)
ALTER TABLE `T_PlantingDestinations`
ADD CONSTRAINT `fk_PlantingDestinations_PlantingID`
FOREIGN KEY (`PlantingID`) REFERENCES `T_Plantings`(`PlantingID`)
ON DELETE CASCADE;

ALTER TABLE `T_PlantingDestinations`
ADD CONSTRAINT `fk_PlantingDestinations_LocationID`
FOREIGN KEY (`LocationID`) REFERENCES `T_Locations`(`LocationID`)
ON DELETE RESTRICT;

-- T_OrderItemDestination: owned by their OrderItem (CASCADE)
-- can't delete a Unit/Location that has destinations (RESTRICT)
ALTER TABLE `T_OrderItemDestination`
ADD CONSTRAINT `fk_OrderItemDest_OrderItemID`
FOREIGN KEY (`OrderItemID`) REFERENCES `T_OrderItems`(`OrderItemID`)
ON DELETE CASCADE;

ALTER TABLE `T_OrderItemDestination`
ADD CONSTRAINT `fk_OrderItemDest_UnitID`
FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`)
ON DELETE RESTRICT;

ALTER TABLE `T_OrderItemDestination`
ADD CONSTRAINT `fk_OrderItemDest_LocationID`
FOREIGN KEY (`LocationID`) REFERENCES `T_Locations`(`LocationID`)
ON DELETE RESTRICT;

-- T_Passwords: owned by their User (CASCADE)
ALTER TABLE `T_Passwords`
ADD CONSTRAINT `fk_Passwords_UserID`
FOREIGN KEY (`UserID`) REFERENCES `T_Users`(`UserID`)
ON DELETE CASCADE;

-- ==================== INDEXES FOR PERFORMANCE ====================

CREATE INDEX `ix_Items_TypeID` ON `T_Items`(`TypeID`);
CREATE INDEX `ix_Units_UnitCategoryID` ON `T_Units`(`UnitCategoryID`);
CREATE INDEX `ix_Prices_ItemID` ON `T_Prices`(`ItemID`);
CREATE INDEX `ix_Prices_UnitID` ON `T_Prices`(`UnitID`);
CREATE INDEX `ix_Plantings_ItemID` ON `T_Plantings`(`ItemID`);
CREATE INDEX `ix_Plantings_UnitID` ON `T_Plantings`(`UnitID`);
CREATE INDEX `ix_Plantings_LocationID` ON `T_Plantings`(`LocationID`);
CREATE INDEX `ix_PlantingDestinations_PlantingID` ON `T_PlantingDestinations`(`PlantingID`);
CREATE INDEX `ix_PlantingDestinations_LocationID` ON `T_PlantingDestinations`(`LocationID`);
CREATE INDEX `ix_Inventory_ItemID` ON `T_Inventory`(`ItemID`);
CREATE INDEX `ix_Inventory_UnitID` ON `T_Inventory`(`UnitID`);
CREATE INDEX `ix_Pitch_ItemID` ON `T_Pitch`(`ItemID`);
CREATE INDEX `ix_Pitch_UnitID` ON `T_Pitch`(`UnitID`);
CREATE INDEX `ix_Orders_GrowingSeasonID` ON `T_Orders`(`GrowingSeasonID`);
CREATE INDEX `ix_Orders_SupplierID` ON `T_Orders`(`SupplierID`);
CREATE INDEX `ix_Orders_ShipperID` ON `T_Orders`(`ShipperID`);
CREATE INDEX `ix_Orders_BrokerID` ON `T_Orders`(`BrokerID`);
CREATE INDEX `ix_OrderItems_OrderID` ON `T_OrderItems`(`OrderID`);
CREATE INDEX `ix_OrderItems_ItemID` ON `T_OrderItems`(`ItemID`);
CREATE INDEX `ix_OrderItems_OrderItemTypeID` ON `T_OrderItems`(`OrderItemTypeID`);
CREATE INDEX `ix_OrderItems_OrderNote` ON `T_OrderItems`(`OrderNote`);
CREATE INDEX `ix_SeasonalNotes_ItemID` ON `T_SeasonalNotes`(`ItemID`);
CREATE INDEX `ix_SeasonalNotes_GrowingSeasonID` ON `T_SeasonalNotes`(`GrowingSeasonID`);
CREATE INDEX `ix_OrderItemDestination_OrderItemID` ON `T_OrderItemDestination`(`OrderItemID`);
CREATE INDEX `ix_OrderItemDestination_UnitID` ON `T_OrderItemDestination`(`UnitID`);
CREATE INDEX `ix_OrderItemDestination_LocationID` ON `T_OrderItemDestination`(`LocationID`);
CREATE INDEX `ix_Passwords_UserID` ON `T_Passwords`(`UserID`);
CREATE UNIQUE INDEX `ix_Users_Email` ON `T_Users`(`Email`(255));

SET FOREIGN_KEY_CHECKS = 1;

-- ==================== VERIFICATION ====================
SELECT 'All Foreign Keys and Indexes Created Successfully!' as Status;

SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'EdgewaterMaster'
AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, CONSTRAINT_NAME;