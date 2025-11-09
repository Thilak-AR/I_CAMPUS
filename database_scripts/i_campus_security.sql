USE Thilak;
GO

-- ==============================================================
-- Security & Access Control Schema
-- ==============================================================

-- 1) SystemRoles (detailed role metadata)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SystemRoles' AND xtype='U')
BEGIN
    CREATE TABLE SystemRoles (
        RoleID INT IDENTITY(1,1) PRIMARY KEY,
        RoleKey NVARCHAR(50) UNIQUE NOT NULL,   -- e.g., super_admin, admin, accounts
        DisplayName NVARCHAR(100),
        Description NVARCHAR(200),
        IsActive BIT DEFAULT 1,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 2) RolePermissions (optional mapping to granular permissions)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RolePermissions' AND xtype='U')
BEGIN
    CREATE TABLE RolePermissions (
        RP_ID INT IDENTITY(1,1) PRIMARY KEY,
        RoleID INT FOREIGN KEY REFERENCES SystemRoles(RoleID),
        PermissionKey NVARCHAR(100),  -- e.g., adm:toggle_module, fin:pay
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 3) SystemModules (register all modules and default state)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SystemModules' AND xtype='U')
BEGIN
    CREATE TABLE SystemModules (
        ModuleID INT IDENTITY(1,1) PRIMARY KEY,
        ModuleKey NVARCHAR(100) UNIQUE NOT NULL, -- e.g., "attendance", "lms", "finance"
        ModuleName NVARCHAR(150),
        Description NVARCHAR(250),
        IsCore BIT DEFAULT 0,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 4) BranchModuleToggles (per-branch enable/disable, stores who changed)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='BranchModuleToggles' AND xtype='U')
BEGIN
    CREATE TABLE BranchModuleToggles (
        ToggleID INT IDENTITY(1,1) PRIMARY KEY,
        BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
        ModuleID INT FOREIGN KEY REFERENCES SystemModules(ModuleID),
        IsEnabled BIT DEFAULT 1,
        ModifiedBy NVARCHAR(50),
        ModifiedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 5) SystemAuditLogs (comprehensive app-level audit)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SystemAuditLogs' AND xtype='U')
BEGIN
    CREATE TABLE SystemAuditLogs (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        ActorToken NVARCHAR(50),       -- who performed action (token or username)
        ActorRole NVARCHAR(50),
        ActionKey NVARCHAR(100),       -- e.g., "module:toggle", "student:create"
        ResourceType NVARCHAR(50),     -- e.g., "Module", "Student", "Bill"
        ResourceID NVARCHAR(100),      -- e.g., "ModuleID:3" or TokenNumber
        Details NVARCHAR(MAX),         -- JSON details / reason
        IPAddress NVARCHAR(50),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 6) SuperAdmins (list of allowed super-admin accounts; max 5 as per your rule)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SuperAdmins' AND xtype='U')
BEGIN
    CREATE TABLE SuperAdmins (
        SAID INT IDENTITY(1,1) PRIMARY KEY,
        ActorToken NVARCHAR(50) UNIQUE,
        FullName NVARCHAR(100),
        Email NVARCHAR(150),
        AddedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 7) RoleHierarchy (higher -> lower mapping to enforce "only high-to-low toggles")
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RoleHierarchy' AND xtype='U')
BEGIN
    CREATE TABLE RoleHierarchy (
        RHID INT IDENTITY(1,1) PRIMARY KEY,
        HigherRoleKey NVARCHAR(50),
        LowerRoleKey NVARCHAR(50)
    );
END
GO

-- 8) Seed common modules & roles (only if not present)
IF NOT EXISTS (SELECT * FROM SystemModules WHERE ModuleKey='attendance')
BEGIN
    INSERT INTO SystemModules (ModuleKey, ModuleName, Description, IsCore) VALUES
    ('attendance','Attendance','Attendance and scanning module',1),
    ('lms','LMS','Learning Management System',1),
    ('finance','Finance','Fees and payments',1),
    ('library','Library','Library & inventory',0),
    ('placement','Placement','Placement & internships',0),
    ('hostel','Hostel','Hostel management',0),
    ('transport','Transport','Transport management',0),
    ('exams','Exams','Examination & marks',1),
    ('events','Events','Event management',0),
    ('iot','IoT','IoT gateway integrations',0);
END
GO

IF NOT EXISTS (SELECT * FROM SystemRoles WHERE RoleKey='super_admin')
BEGIN
    INSERT INTO SystemRoles (RoleKey, DisplayName, Description, IsActive) VALUES
    ('super_admin','Super Admin','Top-level super admin',1),
    ('admin','Admin','Branch level admin',1),
    ('accounts','Accounts','Account staff',1),
    ('librarian','Librarian','Library incharge',1),
    ('placement_admin','Placement Admin','Placement team',1),
    ('hostel_admin','Hostel Admin','Hostel team',1),
    ('transport_admin','Transport Admin','Transport team',1),
    ('hod','HoD','Head of Department',1),
    ('teacher','Teacher','Faculty',1),
    ('student','Student','Student',1);
END
GO

PRINT('✅ Security & Access control tables created/seeded.');
GO
