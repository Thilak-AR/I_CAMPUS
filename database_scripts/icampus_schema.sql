-- ==============================================================
--  I_Campus Project - SQL Server Database Schema Setup Script
--  Author: Thilak A R
--  Description: Base schema for I_Campus College Management System
--  Includes: Database creation + Student, Roles, Institution, Branch, Course tables
-- ==============================================================

-- Create database (run only once)
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
-- Table: Students
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
ELSE
    PRINT('Table "Students" already exists.');
GO

-- ==============================================================
-- Table: UserRoles
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
ELSE
    PRINT('Table "UserRoles" already exists.');
GO

-- ==============================================================
-- Multi-Branch Core Tables
-- ==============================================================

-- INSTITUTIONS
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Institutions' AND xtype='U')
BEGIN
    CREATE TABLE Institutions (
        InstitutionID INT IDENTITY(1,1) PRIMARY KEY,
        InstitutionName NVARCHAR(100) NOT NULL,
        InstitutionCode NVARCHAR(20) UNIQUE NOT NULL,
        EmailDomain NVARCHAR(50) DEFAULT 'nttf.co.in',
        CreatedOn DATETIME DEFAULT GETDATE()
    );
    PRINT('Table "Institutions" created.');
END
GO

-- BRANCHES
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
    PRINT('Table "Branches" created.');
END
GO

-- COURSES
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
    PRINT('Table "Courses" created.');
END
GO

-- DEPARTMENTS
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
    PRINT('Table "Departments" created.');
END
GO

-- ==============================================================
--  MODIFY STUDENTS TABLE TO LINK INSTITUTION, BRANCH, COURSE
-- ==============================================================

IF COL_LENGTH('Students', 'InstitutionID') IS NULL
    ALTER TABLE Students ADD InstitutionID INT NULL FOREIGN KEY REFERENCES Institutions(InstitutionID);
IF COL_LENGTH('Students', 'BranchID') IS NULL
    ALTER TABLE Students ADD BranchID INT NULL FOREIGN KEY REFERENCES Branches(BranchID);
IF COL_LENGTH('Students', 'CourseID') IS NULL
    ALTER TABLE Students ADD CourseID INT NULL FOREIGN KEY REFERENCES Courses(CourseID);
GO

-- ==============================================================
--  Sample Data
-- ==============================================================

-- Institution
IF NOT EXISTS (SELECT * FROM Institutions WHERE InstitutionCode = 'NTTF001')
    INSERT INTO Institutions (InstitutionName, InstitutionCode)
    VALUES ('NTTF', 'NTTF001');

-- Branch
IF NOT EXISTS (SELECT * FROM Branches WHERE BranchCode = 'NEC09')
    INSERT INTO Branches (InstitutionID, BranchName, BranchCode, City, State)
    VALUES (1, 'NEC', 'NEC09', 'Bangalore', 'Karnataka');

-- Course
IF NOT EXISTS (SELECT * FROM Courses WHERE CourseCode = 'CP09')
    INSERT INTO Courses (BranchID, CourseName, CourseCode, DurationYears)
    VALUES (1, 'Computer Programming', 'CP09', 3);

-- Student
IF NOT EXISTS (SELECT * FROM Students WHERE TokenNumber = 'NECCP0925001')
    INSERT INTO Students (TokenNumber, FullName, CourseCode, BatchYear, DOB, Email, Password, InstitutionID, BranchID, CourseID)
    VALUES ('NECCP0925001', 'Test Student', 'CP09', 2025, '2004-06-29', 'neccp0925001@nttf.co.in', '290604', 1, 1, 1);

-- User Role
IF NOT EXISTS (SELECT * FROM UserRoles WHERE TokenNumber = 'NECCP0925001')
    INSERT INTO UserRoles (TokenNumber, RoleName)
    VALUES ('NECCP0925001', 'student');

PRINT('Sample records inserted successfully.');
GO
