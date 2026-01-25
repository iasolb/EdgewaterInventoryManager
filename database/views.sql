-- views.sql
-- SQL Views for Edgewater Farm Inventory Management System

USE `EdgewaterMaster`;

-- ==================== INVENTORY VIEW ====================
DROP VIEW IF EXISTS `v_inventory_full`;
CREATE VIEW `v_inventory_full` AS
SELECT 
    -- Inventory fields
    inv.InventoryID,
    inv.DateCounted,
    inv.NumberOfUnits,
    inv.InventoryComments,
    
    -- Item fields
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.Inactive,
    i.ShouldStock,
    i.LabelDescription,
    i.Definition,
    i.PictureLink,
    i.SunConditions,
    i.TypeID,
    
    -- ItemType fields
    it.Type,
    
    -- Unit fields
    u.UnitID,
    u.UnitType,
    u.UnitSize,
    u.UnitCategoryID,
    
    -- UnitCategory fields
    uc.UnitCategory
    
FROM T_Inventory inv
LEFT JOIN T_Items i ON inv.ItemID = i.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Units u ON inv.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID;


-- ==================== PLANTINGS VIEW ====================
DROP VIEW IF EXISTS `v_plantings_full`;
CREATE VIEW `v_plantings_full` AS
SELECT 
    -- Planting fields
    p.PlantingID,
    p.DatePlanted,
    p.NumberOfUnits,
    p.PlantingComments,
    
    -- Item fields
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.Inactive,
    i.SunConditions,
    i.TypeID,
    
    -- Unit fields
    u.UnitID,
    u.UnitType,
    u.UnitSize,
    u.UnitCategoryID,
    
    -- UnitCategory fields
    uc.UnitCategory
    
FROM T_Plantings p
LEFT JOIN T_Items i ON p.ItemID = i.ItemID
LEFT JOIN T_Units u ON p.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID;


-- ==================== LABELS VIEW ====================
DROP VIEW IF EXISTS `v_label_data_full`;
CREATE VIEW `v_label_data_full` AS
SELECT 
    -- Item fields
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.SunConditions,
    i.LabelDescription,
    i.Definition,
    i.TypeID,
    
    -- ItemType fields
    it.Type,
    
    -- Price fields
    pr.PriceID,
    pr.UnitID,
    pr.UnitPrice,
    pr.Year
    
FROM T_Items i
LEFT JOIN T_Prices pr ON i.ItemID = pr.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID;


-- ==================== ORDERS VIEW ====================
DROP VIEW IF EXISTS `v_orders_full`;
CREATE VIEW `v_orders_full` AS
SELECT 
    -- OrderItem fields
    oi.OrderItemID,
    oi.ItemCode,
    oi.Unit,
    oi.UnitPrice,
    oi.NumberOfUnits,
    oi.Received,
    oi.OrderNote AS OrderNoteCode,
    oi.OrderComments AS OrderItemComments,
    oi.Leftover,
    oi.ToOrder,

    -- Order item destination fields

    od.OrderItemDestinationID,
    od.Count,
    od.LocationID,
    
    -- Order fields
    o.OrderID,
    o.DatePlaced,
    o.DateReceived,
    o.OrderNumber,
    o.TrackingNumber,
    o.OrderComments AS OrderComments,
    o.GrowingSeason,
    o.GrowingSeasonID,
    o.DateDue,
    o.TotalCost,
    
    -- OrderItemType fields
    oit.OrderItemType,
    oit.OrderItemTypeID,
    
    -- OrderNote fields
    onote.OrderNoteID,
    onote.OrderNote AS OrderNoteDecode,
    
    -- Broker fields
    b.BrokerID,
    b.Broker,
    b.BrokerComments,
    
    -- Shipper fields
    s.ShipperID,
    s.Shipper,
    s.AccountNumber AS ShipperAccountNumber,
    s.ContactPerson AS ShipperContactPerson,
    s.Address1 AS ShipperAddress1,
    s.Address2 AS ShipperAddress2,
    s.City AS ShipperCity,
    s.State AS ShipperState,
    s.Zip AS ShipperZip,
    s.Phone AS ShipperPhone,
    s.ShipperComments,
    
    -- Supplier fields
    sup.SupplierID,
    sup.Supplier,
    sup.AccountNumber AS SupplierAccountNumber,
    sup.Phone AS SupplierPhone,
    sup.Fax AS SupplierFax,
    sup.WebSite,
    sup.Email,
    sup.ContactPerson AS SupplierContactPerson,
    sup.Address1 AS SupplierAddress1,
    sup.Address2 AS SupplierAddress2,
    sup.City AS SupplierCity,
    sup.State AS SupplierState,
    sup.Zip AS SupplierZip,
    sup.SupplierComments,
    sup.SupplierType,
    
    -- Item reference
    oi.ItemID
    
FROM T_OrderItems oi
LEFT JOIN T_Orders o ON oi.OrderID = o.OrderID
LEFT JOIN T_OrderItemTypes oit ON oi.OrderItemTypeID = oit.OrderItemTypeID
LEFT JOIN T_OrderNotes onote ON oi.OrderNote = onote.OrderNoteID
LEFT JOIN T_Brokers b ON o.BrokerID = b.BrokerID
LEFT JOIN T_Shippers s ON o.ShipperID = s.ShipperID
LEFT JOIN T_Suppliers sup ON o.SupplierID = sup.SupplierID
LEFT JOIN T_OrderItemDestination od ON oi.OrderItemID = od.OrderItemID; 
-- Display created views
SELECT 'SQL Views Created Successfully!' as Status;
SHOW FULL TABLES WHERE Table_type = 'VIEW';