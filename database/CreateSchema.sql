-- SQL Dump of Edgewater Master.accdb
-- Optimized for MySQL - MIGRATION VERSION (No Foreign Key Constraints)

DROP DATABASE IF EXISTS `EdgewaterMaster`;
CREATE DATABASE `EdgewaterMaster`;
USE `EdgewaterMaster`;

SET NAMES 'UTF8';
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `T_ItemType`;
CREATE TABLE `T_ItemType` (
    `TypeID` INTEGER PRIMARY KEY,
    `Type` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_UnitCategory`;
CREATE TABLE `T_UnitCategory` (
    `UnitCategoryID` INTEGER PRIMARY KEY,
    `UnitCategory` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Units`
CREATE TABLE `T_Units` (
    `UnitID` INTEGER PRIMARY KEY,
    `UnitType` TEXT,
    `UnitSize` TEXT,
    `UnitCategory` INTEGER
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Brokers`;
CREATE TABLE `T_Brokers` (
    `BrokerID` INTEGER PRIMARY KEY,
    `Broker` TEXT,
    `BrokerComments` LONGTEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Shippers`;
CREATE TABLE `T_Shippers` (
    `ShipperID` INTEGER PRIMARY KEY,
    `Shipper` TEXT,
    `AccountNumber` TEXT,
    `Phone` TEXT,
    `ContactPerson` TEXT,
    `Address1` TEXT,
    `Address2` TEXT,
    `City` TEXT,
    `State` TEXT,
    `Zip` TEXT,
    `ShipperComments` LONGTEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Suppliers`;
CREATE TABLE `T_Suppliers` (
    `SupplierID` INTEGER PRIMARY KEY,
    `Supplier` TEXT,
    `AccountNumber` TEXT,
    `Phone` TEXT,
    `Fax` TEXT,
    `WebSite` TEXT,
    `Email` TEXT,
    `ContactPerson` TEXT,
    `Address1` TEXT,
    `Address2` TEXT,
    `City` TEXT,
    `State` TEXT,
    `Zip` TEXT,
    `SupplierComments` LONGTEXT,
    `SupplierType` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_GrowingSeason`;
CREATE TABLE `T_GrowingSeason` (
    `GrowingSeasonID` INTEGER PRIMARY KEY,
    `GrowingSeason` TEXT,
    `StartDate` DATETIME,
    `EndDate` DATETIME
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_OrderItemTypes`;
CREATE TABLE `T_OrderItemTypes` (
    `OrderItemTypeID` INTEGER PRIMARY KEY,
    `OrderItemType` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_OrderNotes`;
CREATE TABLE `T_OrderNotes` (
    `OrderNoteID` INTEGER PRIMARY KEY,
    `OrderNote` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Items`;
CREATE TABLE `T_Items` (
    `ItemID` INTEGER PRIMARY KEY,
    `Inactive` BOOLEAN DEFAULT FALSE,
    `Item` TEXT,
    `Variety` TEXT,
    `Color` TEXT,
    `ShouldStock` BOOLEAN DEFAULT FALSE,
    `TypeID` INTEGER,
    `LabelDescription` LONGTEXT,
    `Definition` LONGTEXT,
    `PictureLayout` TEXT,
    `PictureLink` TEXT,
    `SunConditions` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Export_Items`;
CREATE TABLE `T_Export_Items` (
    `ItemID` INTEGER PRIMARY KEY,
    `CombinedName` TEXT,
    `LabelDescription` LONGTEXT,
    `SunConditions` TEXT,
    `Inactive` BOOLEAN,
    `Item` TEXT,
    `Variety` TEXT,
    `Color` TEXT,
    `Type` TEXT,
    `Definition` LONGTEXT,
    `PictureLayout` TEXT,
    `PictureLink` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Prices`;
CREATE TABLE `T_Prices` (
    `PriceID` INTEGER PRIMARY KEY,
    `ItemID` INTEGER,
    `UnitID` INTEGER,
    `UnitPrice` DOUBLE,
    `Year` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Plantings`;
CREATE TABLE `T_Plantings` (
    `PlantingID` INTEGER PRIMARY KEY,
    `DatePlanted` DATETIME,
    `ItemID` INTEGER,
    `UnitID` INTEGER,
    `NumberOfUnits` TEXT,
    `PlantingComments` LONGTEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Inventory`;
CREATE TABLE `T_Inventory` (
    `InventoryID` INTEGER PRIMARY KEY,
    `DateCounted` DATETIME,
    `ItemID` INTEGER,
    `UnitID` INTEGER,
    `NumberOfUnits` TEXT,
    `InventoryComments` LONGTEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Pitch`;
CREATE TABLE `T_Pitch` (
    `PitchID` INTEGER PRIMARY KEY,
    `DatePitched` DATETIME,
    `ItemID` INTEGER,
    `UnitID` INTEGER,
    `NumberOfUnits` TEXT,
    `PitchComments` LONGTEXT,
    `PitchReason` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Orders`;
CREATE TABLE `T_Orders` (
    `OrderID` INTEGER PRIMARY KEY,
    `GrowingSeasonID` INTEGER,
    `DatePlaced` DATETIME,
    `DateDue` DATETIME,
    `DateReceived` DATETIME,
    `SupplierID` INTEGER,
    `OrderNumber` TEXT,
    `ShipperID` INTEGER,
    `TrackingNumber` TEXT,
    `OrderComments` LONGTEXT,
    `TotalCost` DOUBLE,
    `GrowingSeason` TEXT,
    `BrokerID` INTEGER
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_OrderItems`;
CREATE TABLE `T_OrderItems` (
    `OrderItemID` INTEGER PRIMARY KEY,
    `OrderID` INTEGER,
    `ItemID` INTEGER,
    `ItemCode` TEXT,
    `OrderItemTypeID` INTEGER,
    `Unit` TEXT,
    `UnitPrice` DOUBLE,
    `NumberOfUnits` TEXT,
    `Received` BOOLEAN DEFAULT FALSE,
    `OrderNote` INTEGER,
    `OrderComments` LONGTEXT,
    `Leftover` TEXT,
    `ToOrder` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

-- Sun lookup table (standalone - no FK relationships enforced as per diagram)

DROP TABLE IF EXISTS `T_Sun`;
CREATE TABLE `T_Sun` (
    `SunConditionPic` TEXT PRIMARY KEY,
    `SunConditionName` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

LOAD DATA LOCAL INFILE './datasource/ItemTypes.csv' 
INTO TABLE `T_ItemType` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/UnitCategories.csv' 
INTO TABLE `T_UnitCategory` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Units.csv' 
INTO TABLE `T_Units` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Brokers.csv' 
INTO TABLE `T_Brokers` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Shippers.csv' 
INTO TABLE `T_Shippers` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Suppliers.csv' 
INTO TABLE `T_Suppliers` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/GrowingSeasons.csv' 
INTO TABLE `T_GrowingSeason` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/OrderItemTypes.csv' 
INTO TABLE `T_OrderItemTypes` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/OrderNotes.csv' 
INTO TABLE `T_OrderNotes` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Items.csv' 
INTO TABLE `T_Items` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Prices.csv' 
INTO TABLE `T_Prices` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Plantings.csv' 
INTO TABLE `T_Plantings` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Inventory.csv' 
INTO TABLE `T_Inventory` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Pitch.csv' 
INTO TABLE `T_Pitch` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Orders.csv' 
INTO TABLE `T_Orders` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/OrderItems.csv' 
INTO TABLE `T_OrderItems` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

LOAD DATA LOCAL INFILE './datasource/Sun.csv' 
INTO TABLE `T_Sun` 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;


ALTER TABLE `T_Items` ADD FOREIGN KEY (`TypeID`) REFERENCES `T_ItemType`(`TypeID`);
ALTER TABLE `T_Items` ADD FOREIGN KEY (`UnitCategory`) REFERENCES `T_UnitCategory`(`UnitCategoryID`);
ALTER TABLE `T_Prices` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Prices` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);
ALTER TABLE `T_Plantings` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Plantings` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);
ALTER TABLE `T_Inventory` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Inventory` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);
ALTER TABLE `T_Pitch` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_Pitch` ADD FOREIGN KEY (`UnitID`) REFERENCES `T_Units`(`UnitID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`GrowingSeasonID`) REFERENCES `T_GrowingSeason`(`GrowingSeasonID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`SupplierID`) REFERENCES `T_Suppliers`(`SupplierID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`ShipperID`) REFERENCES `T_Shippers`(`ShipperID`);
ALTER TABLE `T_Orders` ADD FOREIGN KEY (`BrokerID`) REFERENCES `T_Brokers`(`BrokerID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderID`) REFERENCES `T_Orders`(`OrderID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`ItemID`) REFERENCES `T_Items`(`ItemID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderItemTypeID`) REFERENCES `T_OrderItemTypes`(`OrderItemTypeID`);
ALTER TABLE `T_OrderItems` ADD FOREIGN KEY (`OrderNote`) REFERENCES `T_OrderNotes`(`OrderNoteID`);

-- Indexes for performance (keeping  these for query optimization)
CREATE INDEX `ix_Items_TypeID` ON `T_Items`(`TypeID`);
CREATE INDEX `ix_Units_UnitCategory` ON `T_Units`(`UnitCategory`);
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
CREATE INDEX `ix_OrderItems_TypeID` ON `T_OrderItems`(`OrderItemTypeID`);
CREATE INDEX `ix_OrderItems_OrderNote` ON `T_OrderItems`(`OrderNote`);

SET FOREIGN_KEY_CHECKS = 1;