-- ==============================================================
--  I_Campus Project - SQL Server Database Schema Setup Script
--  Author: Thilak A R
--  Description: Full unified schema for I_Campus
-- ==============================================================

-- 1️⃣ DATABASE CREATION
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Thilak')
    CREATE DATABASE Thilak;
GO
USE Thilak;
GO

-- 2️⃣ CORE MASTER TABLES
-- (Students, UserRoles, Institutions, Branches, Courses, Departments)
-- [*Already in your script – unchanged*]

-- 3️⃣ MODULES + BRANCHMODULES
-- [*Already in your script – unchanged*]

-- 4️⃣ ATTENDANCE TABLES
-- [*Already in your script – unchanged*]

-- ==============================================================
-- 5️⃣  LATECOMER & LEAVE WORKFLOW
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LatecomerRules' AND xtype='U')
BEGIN
    CREATE TABLE LatecomerRules (
        RuleID INT IDENTITY(1,1) PRIMARY KEY,
        MaxExcuses INT DEFAULT 3,
        Warning1Limit INT DEFAULT 4,
        Warning2Limit INT DEFAULT 5,
        SuspensionLimit INT DEFAULT 6,
        ResetFrequency NVARCHAR(20) DEFAULT 'Semester',
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LatecomerRecords' AND xtype='U')
BEGIN
    CREATE TABLE LatecomerRecords (
        RecordID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        AttendanceID INT NULL FOREIGN KEY REFERENCES dbo.Attendance(AttendanceID),
        LateCount INT DEFAULT 1,
        WarningLevel NVARCHAR(20) DEFAULT 'None',
        LastUpdated DATETIME DEFAULT GETDATE(),
        HandledBy NVARCHAR(50)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LeaveRequests' AND xtype='U')
BEGIN
    CREATE TABLE LeaveRequests (
        LeaveID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        FromDate DATE NOT NULL,
        ToDate DATE NOT NULL,
        Reason NVARCHAR(200),
        Status NVARCHAR(20) DEFAULT 'Pending',
        CurrentApproverRole NVARCHAR(50),
        ApprovedBy NVARCHAR(50),
        RejectedBy NVARCHAR(50),
        Comments NVARCHAR(200),
        AppliedOn DATETIME DEFAULT GETDATE(),
        LastUpdated DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Notifications' AND xtype='U')
BEGIN
    CREATE TABLE Notifications (
        NotificationID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        Title NVARCHAR(100),
        Message NVARCHAR(300),
        RecipientRole NVARCHAR(50),
        SentDate DATETIME DEFAULT GETDATE(),
        IsRead BIT DEFAULT 0
    );
END
GO

-- ==============================================================
-- 6️⃣ EVENT MANAGEMENT
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EventCategories' AND xtype='U')
BEGIN
    CREATE TABLE EventCategories (
        CategoryID INT IDENTITY(1,1) PRIMARY KEY,
        CategoryName NVARCHAR(100) UNIQUE NOT NULL,
        Description NVARCHAR(200),
        IsActive BIT DEFAULT 1
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Events' AND xtype='U')
BEGIN
    CREATE TABLE Events (
        EventID INT IDENTITY(1,1) PRIMARY KEY,
        CategoryID INT FOREIGN KEY REFERENCES EventCategories(CategoryID),
        Title NVARCHAR(150),
        Description NVARCHAR(MAX),
        OrganizerRole NVARCHAR(50),
        OrganizedBy NVARCHAR(100),
        Venue NVARCHAR(150),
        StartDate DATETIME,
        EndDate DATETIME,
        Semester NVARCHAR(10),
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        BranchID INT FOREIGN KEY REFERENCES Branches(BranchID),
        Status NVARCHAR(20) DEFAULT 'Scheduled',
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EventParticipants' AND xtype='U')
BEGIN
    CREATE TABLE EventParticipants (
        ParticipantID INT IDENTITY(1,1) PRIMARY KEY,
        EventID INT FOREIGN KEY REFERENCES Events(EventID),
        TokenNumber NVARCHAR(20),
        Role NVARCHAR(50),
        ParticipationStatus NVARCHAR(20) DEFAULT 'Registered',
        MarksAwarded INT,
        Feedback NVARCHAR(300),
        ProofPhoto NVARCHAR(200),
        UploadedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EventProofs' AND xtype='U')
BEGIN
    CREATE TABLE EventProofs (
        ProofID INT IDENTITY(1,1) PRIMARY KEY,
        EventID INT FOREIGN KEY REFERENCES Events(EventID),
        UploadedBy NVARCHAR(50),
        ProofType NVARCHAR(50),
        FilePath NVARCHAR(300),
        UploadedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- ==============================================================
-- 7️⃣  LMS (Learning Management System)
-- ==============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Subjects' AND xtype='U')
BEGIN
    CREATE TABLE Subjects (
        SubjectID INT IDENTITY(1,1) PRIMARY KEY,
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        SubjectName NVARCHAR(100),
        SubjectCode NVARCHAR(20) UNIQUE,
        Semester NVARCHAR(10),
        Credits INT DEFAULT 4,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudyMaterials' AND xtype='U')
BEGIN
    CREATE TABLE StudyMaterials (
        MaterialID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        UploadedBy NVARCHAR(50),
        Title NVARCHAR(150),
        Description NVARCHAR(MAX),
        FilePath NVARCHAR(300),
        FileType NVARCHAR(50),
        UploadDate DATETIME DEFAULT GETDATE(),
        IsPublic BIT DEFAULT 0
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Assignments' AND xtype='U')
BEGIN
    CREATE TABLE Assignments (
        AssignmentID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        Title NVARCHAR(150),
        Description NVARCHAR(MAX),
        AssignedBy NVARCHAR(50),
        DueDate DATE,
        MaxMarks INT DEFAULT 10,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Submissions' AND xtype='U')
BEGIN
    CREATE TABLE Submissions (
        SubmissionID INT IDENTITY(1,1) PRIMARY KEY,
        AssignmentID INT FOREIGN KEY REFERENCES Assignments(AssignmentID),
        TokenNumber NVARCHAR(20),
        FilePath NVARCHAR(300),
        SubmittedOn DATETIME DEFAULT GETDATE(),
        MarksAwarded INT,
        Feedback NVARCHAR(300)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Quizzes' AND xtype='U')
BEGIN
    CREATE TABLE Quizzes (
        QuizID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        Question NVARCHAR(MAX),
        OptionA NVARCHAR(200),
        OptionB NVARCHAR(200),
        OptionC NVARCHAR(200),
        OptionD NVARCHAR(200),
        CorrectOption CHAR(1),
        Marks INT DEFAULT 1
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='QuizResults' AND xtype='U')
BEGIN
    CREATE TABLE QuizResults (
        ResultID INT IDENTITY(1,1) PRIMARY KEY,
        QuizID INT FOREIGN KEY REFERENCES Quizzes(QuizID),
        TokenNumber NVARCHAR(20),
        Score INT,
        AttemptedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- ==============================================================
-- 8️⃣  DEFAULT DATA
-- ==============================================================

IF NOT EXISTS (SELECT * FROM EventCategories)
    INSERT INTO EventCategories (CategoryName, Description)
    VALUES ('Academic','Academic events'),('Cultural','Cultural programs'),
           ('Sports','Sports and tournaments'),('Technical','Tech events');
GO

IF NOT EXISTS (SELECT * FROM LatecomerRules)
    INSERT INTO LatecomerRules (MaxExcuses, Warning1Limit, Warning2Limit, SuspensionLimit)
    VALUES (3,4,5,6);
GO

PRINT('✅ I_Campus full schema setup completed successfully.');
GO
