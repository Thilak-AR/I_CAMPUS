USE Thilak;
GO

-- ==============================================================
--  Library & Inventory Management Tables
-- ==============================================================

-- LIBRARY BOOK MASTER
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LibraryBooks' AND xtype='U')
BEGIN
    CREATE TABLE LibraryBooks (
        BookID INT IDENTITY(1,1) PRIMARY KEY,
        ISBN NVARCHAR(20) UNIQUE NOT NULL,
        Title NVARCHAR(200) NOT NULL,
        Author NVARCHAR(150),
        Publisher NVARCHAR(150),
        Edition NVARCHAR(50),
        Category NVARCHAR(100),
        Quantity INT DEFAULT 1,
        Available INT DEFAULT 1,
        AddedOn DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "LibraryBooks" created successfully.');
END
GO

-- BOOK TRANSACTIONS (ISSUE/RETURN)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='BookTransactions' AND xtype='U')
BEGIN
    CREATE TABLE BookTransactions (
        TransactionID INT IDENTITY(1,1) PRIMARY KEY,
        BookID INT FOREIGN KEY REFERENCES LibraryBooks(BookID),
        TokenNumber NVARCHAR(20) NOT NULL,
        IssueDate DATE DEFAULT GETDATE(),
        DueDate DATE NOT NULL,
        ReturnDate DATE NULL,
        FineAmount DECIMAL(10,2) DEFAULT 0,
        Status NVARCHAR(20) DEFAULT 'Issued' -- Issued / Returned / Overdue
    );
    PRINT('Table "BookTransactions" created successfully.');
END
GO

-- LIBRARY FINES RECORD
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LibraryFines' AND xtype='U')
BEGIN
    CREATE TABLE LibraryFines (
        FineID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        TransactionID INT FOREIGN KEY REFERENCES BookTransactions(TransactionID),
        FineAmount DECIMAL(10,2),
        Reason NVARCHAR(200),
        PaidStatus NVARCHAR(20) DEFAULT 'Pending',
        PaidOn DATETIME NULL
    );
    PRINT('Table "LibraryFines" created successfully.');
END
GO

-- INVENTORY (for lab items, tools, etc.)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='InventoryItems' AND xtype='U')
BEGIN
    CREATE TABLE InventoryItems (
        ItemID INT IDENTITY(1,1) PRIMARY KEY,
        ItemName NVARCHAR(150),
        Category NVARCHAR(100),
        Quantity INT DEFAULT 1,
        Location NVARCHAR(100),
        AssignedTo NVARCHAR(20) NULL,
        LastChecked DATETIME DEFAULT GETDATE(),
        Status NVARCHAR(50) DEFAULT 'Available'
    );
    PRINT('Table "InventoryItems" created successfully.');
END
GO

-- INVENTORY TRANSACTIONS
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='InventoryTransactions' AND xtype='U')
BEGIN
    CREATE TABLE InventoryTransactions (
        InvTransID INT IDENTITY(1,1) PRIMARY KEY,
        ItemID INT FOREIGN KEY REFERENCES InventoryItems(ItemID),
        TokenNumber NVARCHAR(20),
        Action NVARCHAR(20), -- Issued / Returned / Damaged
        Quantity INT DEFAULT 1,
        ActionDate DATETIME DEFAULT GETDATE(),
        Remarks NVARCHAR(200)
    );
    PRINT('Table "InventoryTransactions" created successfully.');
END
GO

-- SAMPLE BOOKS
IF NOT EXISTS (SELECT * FROM LibraryBooks WHERE ISBN='978-81-920')
BEGIN
    INSERT INTO LibraryBooks (ISBN, Title, Author, Publisher, Edition, Category, Quantity, Available)
    VALUES ('978-81-920', 'Programming in Python', 'Guido van Rossum', 'NTTF Press', '1st', 'Programming', 10, 10);
    PRINT('Sample book inserted.');
END
GO

-- SAMPLE INVENTORY ITEM
IF NOT EXISTS (SELECT * FROM InventoryItems WHERE ItemName='Oscilloscope')
BEGIN
    INSERT INTO InventoryItems (ItemName, Category, Quantity, Location, Status)
    VALUES ('Oscilloscope', 'Electronics Lab', 3, 'Lab-2', 'Available');
    PRINT('Sample inventory item inserted.');
END
GO

PRINT('✅ Library & Inventory Management tables created successfully.');
GO
