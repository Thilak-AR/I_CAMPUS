-- ==============================================================
--  I_Campus Project - SQL Server Database Schema Setup Script
--  Author: Thilak A R
--  Description: Base schema for I_Campus College Management System
--  Includes: Database creation + Student table (Admission module)
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
-- Stores student identity, admission, and login credentials
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
-- Add sample data (optional for testing)
-- ==============================================================

INSERT INTO Students (TokenNumber, FullName, CourseCode, BatchYear, DOB, Email, Password)
VALUES ('NECCP0925001', 'Test Student', 'CP09', 2025, '2004-06-29', 'neccp0925001@nttf.co.in', '290604');

PRINT('Sample student added successfully.');

GO
