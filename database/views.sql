-- views.sql
-- SQL Views for Edgewater Farm Inventory Management System
-- Building one at a time to identify errors

USE `EdgewaterMaster`;

-- ==================== VIEW 1: INVENTORY ====================
DROP VIEW IF EXISTS `v_inventory_full`;
CREATE VIEW `v_inventory_full` AS
SELECT 
    inv.InventoryID,
    inv.DateCounted,
    inv.NumberOfUnits,
    inv.InventoryComments,
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.Inactive,
    i.ShouldStock,
    i.LabelDescription,
    i.Definition,
    i.PictureLink,
    i.PictureLayout,
    i.SunConditions,
    i.TypeID,
    it.Type,
    u.UnitID,
    u.UnitType,
    u.UnitSize,
    u.UnitCategoryID,
    uc.UnitCategory
FROM T_Inventory inv
LEFT JOIN T_Items i ON inv.ItemID = i.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Units u ON inv.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID;

SELECT 'v_inventory_full created' AS Status;

-- ==================== VIEW 2: PLANTINGS ====================
DROP VIEW IF EXISTS `v_plantings_full`;
CREATE VIEW `v_plantings_full` AS
SELECT 
    p.PlantingID,
    p.DatePlanted,
    p.NumberOfUnits,
    p.PlantingComments,
    p.LocationID AS PlantingLocationID,
    ploc.Location AS PlantingLocation,
    pd.PlantingDestinationID,
    pd.LocationID AS DestinationLocationID,
    dloc.Location AS DestinationLocation,
    pd.UnitsDestined,
    pd.PurposeComments,
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.Inactive,
    i.ShouldStock,
    i.SunConditions,
    i.TypeID,
    i.Definition,
    i.LabelDescription,
    it.Type,
    u.UnitID,
    u.UnitType,
    u.UnitSize,
    u.UnitCategoryID,
    uc.UnitCategory,
    sn.NoteID,
    sn.GrowingSeasonID, 
    sn.Greenhouse,
    sn.Note AS SeasonalNote,
    sn.LastUpdate AS NoteLastUpdate
FROM T_Plantings p
LEFT JOIN T_Items i ON p.ItemID = i.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Units u ON p.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID
LEFT JOIN T_SeasonalNotes sn ON p.ItemID = sn.ItemID
LEFT JOIN T_Locations ploc ON p.LocationID = ploc.LocationID
LEFT JOIN T_PlantingDestinations pd ON p.PlantingID = pd.PlantingID
LEFT JOIN T_Locations dloc ON pd.LocationID = dloc.LocationID;

SELECT 'v_plantings_full created' AS Status;

-- ==================== VIEW 3: ORDERS ====================
DROP VIEW IF EXISTS `v_orders_full`;
CREATE VIEW `v_orders_full` AS
SELECT 
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
    oi.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    it.Type AS ItemTypeName,
    od.OrderItemDestinationID,
    od.Count AS DestinationCount,
    od.UnitID AS DestinationUnitID,
    du.UnitType AS DestinationUnitType,
    du.UnitSize AS DestinationUnitSize,
    loc.LocationID,
    loc.Location AS LocationName,
    o.OrderID,
    o.DatePlaced,
    o.DateReceived,
    o.DateDue,
    o.OrderNumber,
    o.TrackingNumber,
    o.OrderComments,
    o.TotalCost,
    o.GrowingSeason,
    o.GrowingSeasonID,
    gs.StartDate AS SeasonStartDate,
    gs.EndDate AS SeasonEndDate,
    oit.OrderItemType,
    oit.OrderItemTypeID,
    onote.OrderNoteID,
    onote.OrderNote AS OrderNoteDecode,
    b.BrokerID,
    b.Broker,
    b.BrokerComments,
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
    sup.SupplierType
FROM T_OrderItems oi
LEFT JOIN T_Items i ON oi.ItemID = i.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Orders o ON oi.OrderID = o.OrderID
LEFT JOIN T_GrowingSeason gs ON o.GrowingSeasonID = gs.GrowingSeasonID
LEFT JOIN T_OrderItemTypes oit ON oi.OrderItemTypeID = oit.OrderItemTypeID
LEFT JOIN T_OrderNotes onote ON oi.OrderNote = onote.OrderNoteID
LEFT JOIN T_Brokers b ON o.BrokerID = b.BrokerID
LEFT JOIN T_Shippers s ON o.ShipperID = s.ShipperID
LEFT JOIN T_Suppliers sup ON o.SupplierID = sup.SupplierID
LEFT JOIN T_OrderItemDestination od ON oi.OrderItemID = od.OrderItemID
LEFT JOIN T_Locations loc ON od.LocationID = loc.LocationID
LEFT JOIN T_Units du ON od.UnitID = du.UnitID;

SELECT 'v_orders_full created' AS Status;

-- ==================== VIEW 4: LABELS ====================
DROP VIEW IF EXISTS `v_label_data_full`;
CREATE VIEW `v_label_data_full` AS
SELECT 
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    i.SunConditions,
    i.LabelDescription,
    i.Definition,
    i.PictureLink,
    i.PictureLayout,
    i.Inactive,
    i.ShouldStock,
    i.TypeID,
    it.Type,
    pr.PriceID,
    pr.UnitID,
    pr.UnitPrice,
    pr.Year,
    u.UnitType,
    u.UnitSize,
    u.UnitCategoryID,
    uc.UnitCategory
FROM T_Items i
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Prices pr ON i.ItemID = pr.ItemID
LEFT JOIN T_Units u ON pr.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID;

SELECT 'v_label_data_full created' AS Status;

-- ==================== VIEW 5: PITCH ====================
DROP VIEW IF EXISTS `v_pitch_full`;
CREATE VIEW `v_pitch_full` AS
SELECT 
    pt.PitchID,
    pt.DatePitched,
    pt.NumberOfUnits,
    pt.PitchComments,
    pt.PitchReason,
    i.ItemID,
    i.Item,
    i.Variety,
    i.Color,
    it.Type AS ItemTypeName,
    i.ShouldStock,
    u.UnitID,
    u.UnitType,
    u.UnitSize,
    uc.UnitCategory
FROM T_Pitch pt
LEFT JOIN T_Items i ON pt.ItemID = i.ItemID
LEFT JOIN T_ItemType it ON i.TypeID = it.TypeID
LEFT JOIN T_Units u ON pt.UnitID = u.UnitID
LEFT JOIN T_UnitCategory uc ON u.UnitCategoryID = uc.UnitCategoryID;

SELECT 'v_pitch_full created' AS Status;

-- ==================== FINAL CHECK ====================
SELECT 'All views created successfully!' AS Status;
SHOW FULL TABLES WHERE Table_type = 'VIEW';