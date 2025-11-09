-- ==============================================================
--  I_Campus Project - SQL Server Database Schema Setup Script
--  Author: Thilak A R
--  Description: Full base schema for I_Campus College Management System
--  Includes: Student, Roles, Institution, Branch, Course, Attendance,
--            RFID/Biometric, Modules, and supporting tables
-- ==============================================================

-- Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Thilak')
BEGIN
    CREATE DATABASE Thilak;
    PRINT('Database "Thilak" created successfully.');
END
ELSE
    PRINT('Database "Thilak" already exists.');

GO
USE Thilak;
GO

-- ==============================================================
-- Students Table
-- ==============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Students' AND xtype='U')
BEGIN
    CREATE TABLE Students (
        StudentID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20) UNIQUE NOT NULL,
        FullName NVARCHAR(100) NOT NULL,
        CourseCode NVARCHAR(10) NOT NULL,
        BatchYear INT NOT NULL,
        DOB DATE NOT NULL,
        Email NVARCHAR(100) UNIQUE NOT NULL,
        Password NVARCHAR(50) NOT NULL,
        AdmissionDate DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "Students" created successfully.');
END
GO

-- ==============================================================
-- User Roles
-- ==============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserRoles' AND xtype='U')
BEGIN
    CREATE TABLE UserRoles (
        RoleID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20) UNIQUE NOT NULL,
        RoleName NVARCHAR(50) NOT NULL DEFAULT 'student'
    );
    PRINT('Table "UserRoles" created successfully.');
END
GO

-- ==============================================================
-- Institutions, Branches, Courses, Departments
-- ==============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Institutions' AND xtype='U')
BEGIN
    CREATE TABLE Institutions (
        InstitutionID INT IDENTITY(1,1) PRIMARY KEY,
        InstitutionName NVARCHAR(100) NOT NULL,
        InstitutionCode NVARCHAR(20) UNIQUE NOT NULL,
        EmailDomain NVARCHAR(50) DEFAULT 'nttf.co.in',
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Branches' AND xtype='U')
BEGIN
    CREATE TABLE Branches (
        BranchID INT IDENTITY(1,1) PRIMARY KEY,
        InstitutionID INT FOREIGN KEY REFERENCES Institutions(InstitutionID),
        BranchName NVARCHAR(100) NOT NULL,
        BranchCode NVARCHAR(10) UNIQUE NOT NULL,
        Address NVARCHAR(200),
        City NVARCHAR(100),
        State NVARCHAR(100),
        ContactEmail NVARCHAR(100),
        ContactNumber NVARCHAR(20),
        ModulesEnabled NVARCHAR(MAX) DEFAULT 'All',
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Courses' AND xtype='U')
BEGIN
    CREATE TABLE Courses (
        CourseID INT IDENTITY(1,1) PRIMARY KEY,
        BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
        CourseName NVARCHAR(100) NOT NULL,
        CourseCode NVARCHAR(10) NOT NULL,
        DurationYears INT DEFAULT 3,
        IsActive BIT DEFAULT 1
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Departments' AND xtype='U')
BEGIN
    CREATE TABLE Departments (
        DepartmentID INT IDENTITY(1,1) PRIMARY KEY,
        BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
        DeptName NVARCHAR(100) NOT NULL,
        DeptCode NVARCHAR(10),
        HeadName NVARCHAR(100),
        IsActive BIT DEFAULT 1
    );
END
GO

-- ==============================================================
-- Modify Students table to link Institution, Branch, Course
-- ==============================================================
IF COL_LENGTH('Students', 'InstitutionID') IS NULL
    ALTER TABLE Students ADD InstitutionID INT NULL FOREIGN KEY REFERENCES Institutions(InstitutionID);
IF COL_LENGTH('Students', 'BranchID') IS NULL
    ALTER TABLE Students ADD BranchID INT NULL FOREIGN KEY REFERENCES Branches(BranchID);
IF COL_LENGTH('Students', 'CourseID') IS NULL
    ALTER TABLE Students ADD CourseID INT NULL FOREIGN KEY REFERENCES Courses(CourseID);
GO

-- ==============================================================
-- Modules and BranchModules
-- ==============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Modules' AND xtype='U')
BEGIN
    CREATE TABLE Modules (
        ModuleID INT IDENTITY(1,1) PRIMARY KEY,
        ModuleName NVARCHAR(100) UNIQUE NOT NULL,
        Description NVARCHAR(200),
        IsCore BIT DEFAULT 0
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='BranchModules' AND xtype='U')
BEGIN
    CREATE TABLE BranchModules (
        BranchModuleID INT IDENTITY(1,1) PRIMARY KEY,
        BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
        ModuleID INT FOREIGN KEY REFERENCES Modules(ModuleID),
        IsEnabled BIT DEFAULT 1,
        LastModified DATETIME DEFAULT GETDATE(),
        ModifiedBy NVARCHAR(50)
    );
END
GO

-- ==============================================================
-- Attendance System: ClassSchedule, RFID_Logs, Biometric_Logs, Attendance
-- ==============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ClassSchedule' AND xtype='U')
BEGIN
    CREATE TABLE ClassSchedule (
        ScheduleID INT IDENTITY(1,1) PRIMARY KEY,
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        SubjectName NVARCHAR(100),
        TeacherToken NVARCHAR(20),
        StartTime TIME,
        EndTime TIME,
        DayOfWeek NVARCHAR(10)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RFID_Logs' AND xtype='U')
BEGIN
    CREATE TABLE RFID_Logs (
        RFIDLogID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        ReaderLocation NVARCHAR(50),
        ScanTime DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Biometric_Logs' AND xtype='U')
BEGIN
    CREATE TABLE Biometric_Logs (
        BioLogID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        DeviceLocation NVARCHAR(50),
        ScanTime DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Attendance' AND xtype='U')
BEGIN
    CREATE TABLE Attendance (
        AttendanceID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        ScheduleID INT FOREIGN KEY REFERENCES ClassSchedule(ScheduleID),
        AttendanceDate DATE DEFAULT GETDATE(),
        Status NVARCHAR(20) DEFAULT 'Pending',
        RFIDDetected BIT DEFAULT 0,
        BiometricDetected BIT DEFAULT 0,
        FlagReason NVARCHAR(100),
        VerifiedBy NVARCHAR(20),
        LastUpdated DATETIME DEFAULT GETDATE()
    );
END
GO

-- ==============================================================
-- Sample Data
-- ==============================================================
IF NOT EXISTS (SELECT * FROM Institutions WHERE InstitutionCode = 'NTTF001')
    INSERT INTO Institutions (InstitutionName, InstitutionCode)
    VALUES ('NTTF', 'NTTF001');

IF NOT EXISTS (SELECT * FROM Branches WHERE BranchCode = 'NEC09')
    INSERT INTO Branches (InstitutionID, BranchName, BranchCode, City, State)
    VALUES (1, 'NEC', 'NEC09', 'Bangalore', 'Karnataka');

IF NOT EXISTS (SELECT * FROM Courses WHERE CourseCode = 'CP09')
    INSERT INTO Courses (BranchID, CourseName, CourseCode, DurationYears)
    VALUES (1, 'Computer Programming', 'CP09', 3);

IF NOT EXISTS (SELECT * FROM Students WHERE TokenNumber = 'NECCP0925001')
    INSERT INTO Students (TokenNumber, FullName, CourseCode, BatchYear, DOB, Email, Password, InstitutionID, BranchID, CourseID)
    VALUES ('NECCP0925001', 'Test Student', 'CP09', 2025, '2004-06-29', 'neccp0925001@nttf.co.in', '290604', 1, 1, 1);

IF NOT EXISTS (SELECT * FROM UserRoles WHERE TokenNumber = 'NECCP0925001')
    INSERT INTO UserRoles (TokenNumber, RoleName)
    VALUES ('NECCP0925001', 'student');

PRINT('Base setup completed successfully.');
GO
