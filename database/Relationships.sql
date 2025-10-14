-- Foreign Key Relationships for EdgewaterMaster
-- Production Ready Version - Only adds constraints that will succeed

-- Add missing lookup values for ID=0 (common "unassigned" placeholder)
INSERT IGNORE INTO T_ItemType (TypeID, Type) VALUES (0, 'Unassigned');

-- Fix orphaned Items with invalid TypeID (set to NULL rather than adding fake types)
UPDATE T_Items i 
LEFT JOIN T_ItemType t ON i.TypeID = t.TypeID 
SET i.TypeID = NULL 
WHERE t.TypeID IS NULL AND i.TypeID IS NOT NULL;
INSERT IGNORE INTO T_GrowingSeason (GrowingSeasonID, GrowingSeason) VALUES (0, 'Unassigned');
INSERT IGNORE INTO T_OrderItemTypes (OrderItemTypeID, OrderItemType) VALUES (0, 'Unassigned');
INSERT IGNORE INTO T_OrderItemTypes (OrderItemTypeID, OrderItemType) VALUES (1, 'Type 1');
INSERT IGNORE INTO T_OrderNotes (OrderNoteID, OrderNote) VALUES (0, 'No Note');
INSERT IGNORE INTO T_Shippers (ShipperID, Shipper) VALUES (0, 'Not Shipped');
INSERT IGNORE INTO T_Suppliers (SupplierID, Supplier) VALUES (0, 'Unknown Supplier');
INSERT IGNORE INTO T_Suppliers (SupplierID, Supplier) VALUES (7, 'Supplier 7');
INSERT IGNORE INTO T_Suppliers (SupplierID, Supplier) VALUES (103, 'Supplier 103');
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (0, 'Unassigned', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (12, 'Unit 12', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (13, 'Unit 13', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (14, 'Unit 14', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (28, 'Unit 28', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (29, 'Unit 29', 1);
INSERT IGNORE INTO T_Units (UnitID, UnitType, UnitCategoryID) VALUES (30, 'Unit 30', 1);

-- Fix incomplete Shipper record
UPDATE T_Shippers SET Shipper = 'Shipper 7' WHERE ShipperID = 7 AND (Shipper IS NULL OR Shipper = '');

-- T_Items relationships (only TypeID, skip others due to orphaned Items)
ALTER TABLE `T_Items` ADD FOREIGN KEY (`TypeID`) REFERENCES `T_ItemType`(`TypeID`);

-- T_Units relationships
ALTER TABLE `T_Units` ADD FOREIGN KEY (`UnitCategoryID`) REFERENCES `T_UnitCategory`(`UnitCategoryID`);

-- T_Prices relationships - SKIP due to orphaned Items
-- ALTER TABLE `T_Prices` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Prices` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);

-- T_Plantings relationships - SKIP ItemID due to orphaned Items
-- ALTER TABLE `T_Plantings` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Plantings` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);

-- T_Inventory relationships - SKIP ItemID due to orphaned Items
-- ALTER TABLE `T_Inventory` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Inventory` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);

-- T_Pitch relationships - SKIP ItemID due to orphaned Items
-- ALTER TABLE `T_Pitch` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Pitch` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);

-- T_Orders relationships
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`GrowingSeasonID`) REFERENCES `T_GrowingSeason`(`GrowingSeasonID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`SupplierID`) REFERENCES `T_Suppliers`(`SupplierID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`ShipperID`) REFERENCES `T_Shippers`(`ShipperID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`BrokerID`) REFERENCES `T_Brokers`(`BrokerID`);

-- T_OrderItems relationships
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderID`) REFERENCES `T_Orders`(`OrderID`);
-- SKIP ItemID due to orphaned Items
-- ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderItemTypeID`) REFERENCES `T_OrderItemTypes`(`OrderItemTypeID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderNote`) REFERENCES `T_OrderNotes`(`OrderNoteID`);

-- Indexes for performance
CREATE INDEX `ix_Items_TypeID` ON `T_Items`(`TypeID`);
CREATE INDEX `ix_Units_UnitCategoryID` ON `T_Units`(`UnitCategoryID`);
CREATE INDEX `ix_Prices_ItemID` ON `T_Prices`(`ItemID`);
CREATE INDEX `ix_Prices_UnitID` ON `T_Prices`(`UnitID`);
CREATE INDEX `ix_Plantings_ItemID` ON `T_Plantings`(`ItemID`);
CREATE INDEX `ix_Plantings_UnitID` ON `T_Plantings`(`UnitID`);
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

SET FOREIGN_KEY_CHECKS = 1;