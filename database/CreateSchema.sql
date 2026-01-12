-- SQL Dump of Edgewater Master.accdb
-- Optimized for MySQL - MIGRATION VERSION (No Foreign Key Constraints)
-- UPDATED: Separate T_Passwords table for authentication data

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

DROP TABLE IF EXISTS `T_Units`;
CREATE TABLE `T_Units` (
    `UnitID` INTEGER PRIMARY KEY,
    `UnitType` TEXT,
    `UnitSize` TEXT,
    `UnitCategoryID` INTEGER
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
    `SunConditionID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `SunConditionPic` LONGBLOB,
    `SunConditionName` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_SeasonalNotes`;
CREATE TABLE `T_SeasonalNotes` (
    `NoteID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `ItemID` INTEGER,
    `GrowingSeasonID` INTEGER,
    `Greenhouse` BOOLEAN,
    `Note` TEXT,
    `LastUpdate` DATETIME
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_OrderItemDestination`;
CREATE TABLE `T_OrderItemDestination` (
    `OrderItemDestinationID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `OrderItemID` INTEGER,
    `Count` INTEGER,
    `UnitID` INTEGER,
    `LocationID` INTEGER
) ENGINE=InnoDB CHARACTER SET UTF8;

-- User profile and permission data (no authentication data)
DROP TABLE IF EXISTS `T_Users`;
CREATE TABLE `T_Users` (
    `UserID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `Role` TEXT,
    `PermissionLevel` TEXT,
    `Email` VARCHAR(255) NOT NULL,
    `Active` BOOLEAN DEFAULT TRUE,
    `CreatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET UTF8;

-- Separate table for authentication and security data
DROP TABLE IF EXISTS `T_Passwords`;
CREATE TABLE `T_Passwords` (
    `PasswordID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `UserID` INTEGER NOT NULL UNIQUE,
    `PasswordHash` VARCHAR(255) NOT NULL,
    `PasswordResetToken` VARCHAR(255),
    `PasswordResetExpiry` DATETIME,
    `LastLogin` DATETIME,
    `LastPasswordChange` DATETIME,
    `FailedLoginAttempts` INTEGER DEFAULT 0,
    `AccountLockedUntil` DATETIME,
    `CreatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `UpdatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET UTF8;

DROP TABLE IF EXISTS `T_Locations`;
CREATE TABLE `T_Locations` (
    `LocationID` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `Location` TEXT
) ENGINE=InnoDB CHARACTER SET UTF8;