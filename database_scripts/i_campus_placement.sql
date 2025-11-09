USE Thilak;
GO

-- ==============================================================
-- Step 28: Placement & Internship Module Schema
-- ==============================================================

-- 1) Companies / Recruiters
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Companies' AND xtype='U')
BEGIN
    CREATE TABLE Companies (
        CompanyID INT IDENTITY(1,1) PRIMARY KEY,
        CompanyName NVARCHAR(200) NOT NULL,
        Website NVARCHAR(200),
        ContactPerson NVARCHAR(100),
        ContactEmail NVARCHAR(100),
        ContactPhone NVARCHAR(30),
        Address NVARCHAR(300),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 2) Job / Internship Openings
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='JobOpenings' AND xtype='U')
BEGIN
    CREATE TABLE JobOpenings (
        OpeningID INT IDENTITY(1,1) PRIMARY KEY,
        CompanyID INT FOREIGN KEY REFERENCES Companies(CompanyID),
        Title NVARCHAR(200),
        OpeningType NVARCHAR(20), -- Job / Internship / Project
        Description NVARCHAR(MAX),
        Role NVARCHAR(100),
        Location NVARCHAR(150),
        Stipend DECIMAL(10,2) NULL,
        SalaryRange NVARCHAR(100) NULL,
        BatchYear INT NULL, -- target batch
        CourseID INT NULL FOREIGN KEY REFERENCES Courses(CourseID),
        Seats INT DEFAULT 1,
        ApplicationStart DATETIME,
        ApplicationEnd DATETIME,
        CreatedBy NVARCHAR(50),
        CreatedOn DATETIME DEFAULT GETDATE(),
        Status NVARCHAR(20) DEFAULT 'Open' -- Open / Closed / Cancelled
    );
END
GO

-- 3) Placement Events (Drives)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PlacementEvents' AND xtype='U')
BEGIN
    CREATE TABLE PlacementEvents (
        EventID INT IDENTITY(1,1) PRIMARY KEY,
        Title NVARCHAR(200),
        Description NVARCHAR(MAX),
        EventDate DATETIME,
        Venue NVARCHAR(200),
        OrganizedBy NVARCHAR(100),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 4) Student Applications to Openings
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PlacementApplications' AND xtype='U')
BEGIN
    CREATE TABLE PlacementApplications (
        ApplicationID INT IDENTITY(1,1) PRIMARY KEY,
        OpeningID INT FOREIGN KEY REFERENCES JobOpenings(OpeningID),
        TokenNumber NVARCHAR(20),
        AppliedOn DATETIME DEFAULT GETDATE(),
        ResumePath NVARCHAR(300), -- avoid storing raw PII files; store path
        Status NVARCHAR(30) DEFAULT 'Applied', -- Applied / Shortlisted / Interview / Offered / Rejected
        Remarks NVARCHAR(300)
    );
END
GO

-- 5) Interview Rounds & Results
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='InterviewRounds' AND xtype='U')
BEGIN
    CREATE TABLE InterviewRounds (
        RoundID INT IDENTITY(1,1) PRIMARY KEY,
        OpeningID INT FOREIGN KEY REFERENCES JobOpenings(OpeningID),
        RoundName NVARCHAR(100), -- e.g., "Aptitude", "Technical", "HR"
        RoundDate DATETIME,
        ConductedBy NVARCHAR(100),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='InterviewResults' AND xtype='U')
BEGIN
    CREATE TABLE InterviewResults (
        ResultID INT IDENTITY(1,1) PRIMARY KEY,
        RoundID INT FOREIGN KEY REFERENCES InterviewRounds(RoundID),
        ApplicationID INT FOREIGN KEY REFERENCES PlacementApplications(ApplicationID),
        Score DECIMAL(6,2),
        Status NVARCHAR(30), -- Pass / Fail / Hold
        Feedback NVARCHAR(400),
        EvaluatedOn DATETIME DEFAULT GETDATE(),
        EvaluatedBy NVARCHAR(100)
    );
END
GO

-- 6) Offers (company issues offer to student)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Offers' AND xtype='U')
BEGIN
    CREATE TABLE Offers (
        OfferID INT IDENTITY(1,1) PRIMARY KEY,
        ApplicationID INT FOREIGN KEY REFERENCES PlacementApplications(ApplicationID),
        CompanyID INT FOREIGN KEY REFERENCES Companies(CompanyID),
        OfferedRole NVARCHAR(150),
        CTC DECIMAL(12,2) NULL,
        Stipend DECIMAL(10,2) NULL,
        OfferStatus NVARCHAR(30) DEFAULT 'Offered', -- Offered / Accepted / Declined / Withdrawn
        OfferDate DATETIME DEFAULT GETDATE(),
        AcceptanceDate DATETIME NULL,
        Remarks NVARCHAR(300)
    );
END
GO

-- 7) Student Placement Records (final accepted placements / internships)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudentPlacements' AND xtype='U')
BEGIN
    CREATE TABLE StudentPlacements (
        PlacementID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        OfferID INT FOREIGN KEY REFERENCES Offers(OfferID),
        CompanyID INT FOREIGN KEY REFERENCES Companies(CompanyID),
        Role NVARCHAR(150),
        StartDate DATE,
        EndDate DATE NULL,
        IsInternship BIT DEFAULT 0,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 8) Privacy / PII audit log for placements (who viewed / downloaded resumes)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PlacementPIIAudit' AND xtype='U')
BEGIN
    CREATE TABLE PlacementPIIAudit (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        Actor NVARCHAR(100), -- staff token who accessed
        Action NVARCHAR(100), -- ViewResume / DownloadResume / Share
        ActionTime DATETIME DEFAULT GETDATE(),
        IPAddress NVARCHAR(50)
    );
END
GO

-- 9) Sample / optional data (one company + opening)
IF NOT EXISTS (SELECT * FROM Companies WHERE CompanyName='Acme Tech')
BEGIN
    INSERT INTO Companies (CompanyName, Website, ContactPerson, ContactEmail, ContactPhone, Address)
    VALUES ('Acme Tech','https://acme.example.com','Rahul HR','hr@acme.example.com','+91-9000000000','Bangalore, India');
END
GO

IF NOT EXISTS (SELECT * FROM JobOpenings WHERE Title='Acme - Summer Intern')
BEGIN
    INSERT INTO JobOpenings (CompanyID, Title, OpeningType, Description, Role, Location, Stipend, BatchYear, CourseID, Seats, ApplicationStart, ApplicationEnd, CreatedBy)
    VALUES (1, 'Acme - Summer Intern', 'Internship', 'Summer internship for CP students', 'Intern - Dev', 'Bangalore', 10000, 2025, 1, 5, GETDATE(), DATEADD(day,30,GETDATE()), 'placement_admin');
END
GO

PRINT('✅ Placement & Internship module tables created successfully.');
GO
