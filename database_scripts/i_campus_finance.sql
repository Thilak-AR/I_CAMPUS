-- ==============================================================
-- I_Campus Project – Finance & Fee Automation Module
-- Author: Thilak A R
-- Description: Complete schema for student financials, payments,
-- receipts, billing, and integration with other modules.
-- ==============================================================

USE Thilak;
GO

-- ==============================================================
-- 1️⃣ FEE COMPONENT MASTER (Tuition, Hostel, Canteen, etc.)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FeeComponents' AND xtype='U')
BEGIN
    CREATE TABLE FeeComponents (
        ComponentID INT IDENTITY(1,1) PRIMARY KEY,
        ComponentName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(200),
        DefaultAmount DECIMAL(10,2) NOT NULL,
        IsRecurring BIT DEFAULT 1,
        IsMandatory BIT DEFAULT 1,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "FeeComponents" created.');
END
GO

-- ==============================================================
-- 2️⃣ STUDENT FEE STRUCTURE (Per Course/Semester Customization)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudentFeeStructure' AND xtype='U')
BEGIN
    CREATE TABLE StudentFeeStructure (
        FeeStructureID INT IDENTITY(1,1) PRIMARY KEY,
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        Semester NVARCHAR(10),
        ComponentID INT FOREIGN KEY REFERENCES FeeComponents(ComponentID),
        Amount DECIMAL(10,2) NOT NULL,
        IsEditable BIT DEFAULT 1,
        EffectiveFrom DATE DEFAULT GETDATE()
    );
    PRINT('Table "StudentFeeStructure" created.');
END
GO

-- ==============================================================
-- 3️⃣ STUDENT BILLING RECORD (Dynamic Monthly + Ad-hoc)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudentBills' AND xtype='U')
BEGIN
    CREATE TABLE StudentBills (
        BillID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        ComponentID INT FOREIGN KEY REFERENCES FeeComponents(ComponentID),
        Description NVARCHAR(200),
        BillDate DATE DEFAULT GETDATE(),
        DueDate DATE,
        Amount DECIMAL(10,2) NOT NULL,
        Status NVARCHAR(20) DEFAULT 'Pending',
        AddedBy NVARCHAR(50),
        SourceModule NVARCHAR(50), -- e.g., "Canteen", "Hostel", "Manual"
        CreatedOn DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "StudentBills" created.');
END
GO

-- ==============================================================
-- 4️⃣ PAYMENT TRANSACTIONS
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Payments' AND xtype='U')
BEGIN
    CREATE TABLE Payments (
        PaymentID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        TotalAmount DECIMAL(10,2),
        PaymentMode NVARCHAR(50),  -- e.g., UPI, Card, Cash
        TransactionID NVARCHAR(100),
        PaymentStatus NVARCHAR(20) DEFAULT 'Pending',
        PaymentDate DATETIME DEFAULT GETDATE(),
        VerifiedBy NVARCHAR(50),
        Remarks NVARCHAR(200)
    );
    PRINT('Table "Payments" created.');
END
GO

-- ==============================================================
-- 5️⃣ PAYMENT DETAILS (Per component level tracking)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PaymentDetails' AND xtype='U')
BEGIN
    CREATE TABLE PaymentDetails (
        PaymentDetailID INT IDENTITY(1,1) PRIMARY KEY,
        PaymentID INT FOREIGN KEY REFERENCES Payments(PaymentID),
        BillID INT FOREIGN KEY REFERENCES StudentBills(BillID),
        AmountPaid DECIMAL(10,2),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "PaymentDetails" created.');
END
GO

-- ==============================================================
-- 6️⃣ RECEIPTS
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Receipts' AND xtype='U')
BEGIN
    CREATE TABLE Receipts (
        ReceiptID INT IDENTITY(1,1) PRIMARY KEY,
        PaymentID INT FOREIGN KEY REFERENCES Payments(PaymentID),
        ReceiptNumber NVARCHAR(30) UNIQUE,
        GeneratedOn DATETIME DEFAULT GETDATE(),
        GeneratedBy NVARCHAR(50),
        FilePath NVARCHAR(200)
    );
    PRINT('Table "Receipts" created.');
END
GO

-- ==============================================================
-- 7️⃣ STUDENT LEDGER
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudentLedger' AND xtype='U')
BEGIN
    CREATE TABLE StudentLedger (
        LedgerID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        TransactionType NVARCHAR(20),  -- 'Credit' or 'Debit'
        Description NVARCHAR(200),
        Amount DECIMAL(10,2),
        LinkedPaymentID INT NULL FOREIGN KEY REFERENCES Payments(PaymentID),
        LinkedBillID INT NULL FOREIGN KEY REFERENCES StudentBills(BillID),
        TransactionDate DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "StudentLedger" created.');
END
GO

-- ==============================================================
-- 8️⃣ SAMPLE DATA
-- ==============================================================

IF NOT EXISTS (SELECT * FROM FeeComponents)
BEGIN
    INSERT INTO FeeComponents (ComponentName, Description, DefaultAmount)
    VALUES ('Tuition Fee', 'Semester tuition fee', 25000.00),
           ('Hostel Fee', 'Hostel accommodation charges', 10000.00),
           ('Transport Fee', 'College transport fee', 5000.00),
           ('Canteen', 'Monthly meal charges', 2000.00),
           ('Library Fine', 'Fine for late book return', 50.00);
    PRINT('Sample Fee Components added.');
END
GO

PRINT('✅ Finance & Fee Automation tables created successfully.');
GO
