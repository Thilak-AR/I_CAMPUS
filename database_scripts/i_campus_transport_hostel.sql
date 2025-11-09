USE Thilak;
GO

-- ==============================================================
-- TRANSPORT: Buses, Routes, Stops, Assignments
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TransportBuses' AND xtype='U')
BEGIN
    CREATE TABLE TransportBuses (
        BusID INT IDENTITY(1,1) PRIMARY KEY,
        BusNumber NVARCHAR(50) UNIQUE,
        Capacity INT,
        DriverName NVARCHAR(100),
        DriverContact NVARCHAR(30),
        RouteID INT NULL,
        IsActive BIT DEFAULT 1,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TransportRoutes' AND xtype='U')
BEGIN
    CREATE TABLE TransportRoutes (
        RouteID INT IDENTITY(1,1) PRIMARY KEY,
        RouteName NVARCHAR(150),
        StartPoint NVARCHAR(150),
        EndPoint NVARCHAR(150),
        EstimatedTime NVARCHAR(50),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TransportStops' AND xtype='U')
BEGIN
    CREATE TABLE TransportStops (
        StopID INT IDENTITY(1,1) PRIMARY KEY,
        RouteID INT FOREIGN KEY REFERENCES TransportRoutes(RouteID),
        StopName NVARCHAR(150),
        SequenceNo INT,
        GPSLat DECIMAL(10,6) NULL,
        GPSLon DECIMAL(10,6) NULL
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TransportAssignments' AND xtype='U')
BEGIN
    CREATE TABLE TransportAssignments (
        AssignmentID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        BusID INT FOREIGN KEY REFERENCES TransportBuses(BusID),
        RouteID INT FOREIGN KEY REFERENCES TransportRoutes(RouteID),
        StopID INT FOREIGN KEY REFERENCES TransportStops(StopID),
        AssignedOn DATETIME DEFAULT GETDATE(),
        IsActive BIT DEFAULT 1
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TransportAttendance' AND xtype='U')
BEGIN
    CREATE TABLE TransportAttendance (
        TransAttendID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        BusID INT,
        RouteID INT,
        StopID INT,
        ScanTime DATETIME DEFAULT GETDATE(),
        ReaderID NVARCHAR(50),
        Method NVARCHAR(20) -- RFID / Manual / App
    );
END
GO

-- ==============================================================
-- HOSTEL: Blocks, Rooms, Allocations, Mess Billing, Guests, Complaints
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelBlocks' AND xtype='U')
BEGIN
    CREATE TABLE HostelBlocks (
        BlockID INT IDENTITY(1,1) PRIMARY KEY,
        BlockName NVARCHAR(100),
        Address NVARCHAR(200),
        ContactNumber NVARCHAR(30),
        Capacity INT,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelRooms' AND xtype='U')
BEGIN
    CREATE TABLE HostelRooms (
        RoomID INT IDENTITY(1,1) PRIMARY KEY,
        BlockID INT FOREIGN KEY REFERENCES HostelBlocks(BlockID),
        RoomNumber NVARCHAR(50),
        BedCount INT DEFAULT 1,
        Occupied INT DEFAULT 0,
        RoomType NVARCHAR(50), -- Single / Double / Triple
        Status NVARCHAR(20) DEFAULT 'Available' -- Available / Occupied / Maintenance
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelAllocations' AND xtype='U')
BEGIN
    CREATE TABLE HostelAllocations (
        AllocationID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        BlockID INT FOREIGN KEY REFERENCES HostelBlocks(BlockID),
        RoomID INT FOREIGN KEY REFERENCES HostelRooms(RoomID),
        BedNumber INT NULL,
        AllocatedOn DATETIME DEFAULT GETDATE(),
        CheckoutOn DATETIME NULL,
        Status NVARCHAR(20) DEFAULT 'Active' -- Active / CheckedOut
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelMessBills' AND xtype='U')
BEGIN
    CREATE TABLE HostelMessBills (
        MessBillID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        MonthYear NVARCHAR(20), -- e.g., '2025-11'
        Amount DECIMAL(10,2),
        Status NVARCHAR(20) DEFAULT 'Pending', -- Pending / Paid
        GeneratedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelGuests' AND xtype='U')
BEGIN
    CREATE TABLE HostelGuests (
        GuestID INT IDENTITY(1,1) PRIMARY KEY,
        HostToken NVARCHAR(20), -- student hosting guest
        GuestName NVARCHAR(150),
        GuestContact NVARCHAR(30),
        FromDate DATE,
        ToDate DATE,
        ApprovedBy NVARCHAR(50),
        Status NVARCHAR(20) DEFAULT 'Pending' -- Pending / Approved / Rejected
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelComplaints' AND xtype='U')
BEGIN
    CREATE TABLE HostelComplaints (
        ComplaintID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        BlockID INT,
        RoomID INT,
        ComplaintText NVARCHAR(500),
        RaisedOn DATETIME DEFAULT GETDATE(),
        Status NVARCHAR(50) DEFAULT 'Open', -- Open / InProgress / Resolved
        ActionTaken NVARCHAR(500)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HostelAccessLogs' AND xtype='U')
BEGIN
    CREATE TABLE HostelAccessLogs (
        AccessID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        BlockID INT,
        Event NVARCHAR(50), -- Entry / Exit / GateScan
        TimeStamp DATETIME DEFAULT GETDATE(),
        ReaderID NVARCHAR(50)
    );
END
GO

-- ==============================================================
-- SAMPLE DATA (optional)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM TransportRoutes WHERE RouteName='Main Route A')
BEGIN
    INSERT INTO TransportRoutes (RouteName, StartPoint, EndPoint, EstimatedTime)
    VALUES ('Main Route A', 'Yelahanka', 'NEC Campus', '45 mins');
END
GO

IF NOT EXISTS (SELECT * FROM TransportBuses WHERE BusNumber='KA-05-0001')
BEGIN
    INSERT INTO TransportBuses (BusNumber, Capacity, DriverName, DriverContact, RouteID)
    VALUES ('KA-05-0001', 40, 'Ramesh', '+91-900000001', 1);
END
GO

IF NOT EXISTS (SELECT * FROM HostelBlocks WHERE BlockName='Block A')
BEGIN
    INSERT INTO HostelBlocks (BlockName, Address, ContactNumber, Capacity)
    VALUES ('Block A', 'NEC Campus Hostels', '+91-900000002', 120);
END
GO

PRINT('✅ Transport & Hostel schema created successfully.');
GO
