USE Thilak;
GO

-- ==============================================================
-- Step 26: Exam & Result Automation Schema
-- ==============================================================

-- 1) Exams (Exam masters: Midterm, Final, Internal etc.)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Exams' AND xtype='U')
BEGIN
    CREATE TABLE Exams (
        ExamID INT IDENTITY(1,1) PRIMARY KEY,
        ExamName NVARCHAR(100) NOT NULL,        -- e.g., Midterm, Final
        ExamType NVARCHAR(50),                  -- Online / Offline / Hybrid
        TotalMarks INT DEFAULT 100,
        IsActive BIT DEFAULT 1,
        StartDate DATETIME,
        EndDate DATETIME,
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        Semester NVARCHAR(10),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 2) Question Bank (faculty uploads Qs used to auto-generate MCQ papers)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='QuestionBank' AND xtype='U')
BEGIN
    CREATE TABLE QuestionBank (
        QuestionID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        FacultyToken NVARCHAR(50),
        QuestionText NVARCHAR(MAX),
        QuestionType NVARCHAR(20),  -- mcq / descriptive
        OptionA NVARCHAR(500),
        OptionB NVARCHAR(500),
        OptionC NVARCHAR(500),
        OptionD NVARCHAR(500),
        CorrectOption CHAR(1),
        Marks INT DEFAULT 1,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 3) ExamPapers (generated set of questions for an exam/session)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ExamPapers' AND xtype='U')
BEGIN
    CREATE TABLE ExamPapers (
        PaperID INT IDENTITY(1,1) PRIMARY KEY,
        ExamID INT FOREIGN KEY REFERENCES Exams(ExamID),
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        GeneratedOn DATETIME DEFAULT GETDATE(),
        PaperMeta NVARCHAR(500) -- JSON/meta info: parts, marks distribution
    );
END
GO

-- 4) PaperQuestions (link questions chosen for a paper)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PaperQuestions' AND xtype='U')
BEGIN
    CREATE TABLE PaperQuestions (
        PQID INT IDENTITY(1,1) PRIMARY KEY,
        PaperID INT FOREIGN KEY REFERENCES ExamPapers(PaperID),
        QuestionID INT FOREIGN KEY REFERENCES QuestionBank(QuestionID),
        SeqNo INT,
        Marks INT
    );
END
GO

-- 5) StudentExamAttempts (student attempt record — MCQ responses / files)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StudentExamAttempts' AND xtype='U')
BEGIN
    CREATE TABLE StudentExamAttempts (
        AttemptID INT IDENTITY(1,1) PRIMARY KEY,
        PaperID INT FOREIGN KEY REFERENCES ExamPapers(PaperID),
        ExamID INT FOREIGN KEY REFERENCES Exams(ExamID),
        TokenNumber NVARCHAR(20),
        StartedOn DATETIME,
        SubmittedOn DATETIME,
        Status NVARCHAR(20) DEFAULT 'Submitted', -- Submitted / Graded / Pending
        AnswerJSON NVARCHAR(MAX),  -- for MCQ: JSON of {qId: selected}, or file path for descriptive
        FilePath NVARCHAR(300)
    );
END
GO

-- 6) Marks (final marks per student per subject/exam)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Marks' AND xtype='U')
BEGIN
    CREATE TABLE Marks (
        MarkID INT IDENTITY(1,1) PRIMARY KEY,
        AttemptID INT FOREIGN KEY REFERENCES StudentExamAttempts(AttemptID),
        TokenNumber NVARCHAR(20),
        ExamID INT FOREIGN KEY REFERENCES Exams(ExamID),
        SubjectID INT FOREIGN KEY REFERENCES Subjects(SubjectID),
        MarksObtained DECIMAL(8,2),
        GradedBy NVARCHAR(50),
        GradedOn DATETIME DEFAULT GETDATE(),
        GradeRemarks NVARCHAR(300)
    );
END
GO

-- 7) MarksheetRules (dynamic/customizable calculation rules per course/inst)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='MarksheetRules' AND xtype='U')
BEGIN
    CREATE TABLE MarksheetRules (
        RuleID INT IDENTITY(1,1) PRIMARY KEY,
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        RuleName NVARCHAR(100),
        JSONConfig NVARCHAR(MAX), -- JSON describing weightages, e.g. {"mid":25,"final":75,"internal":25,"shop_talk":10,...}
        IsDefault BIT DEFAULT 0,
        CreatedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 8) GeneratedMarksheet (final consolidated marks record)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='GeneratedMarksheet' AND xtype='U')
BEGIN
    CREATE TABLE GeneratedMarksheet (
        MarksheetID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        CourseID INT FOREIGN KEY REFERENCES Courses(CourseID),
        Semester NVARCHAR(10),
        MarksheetJSON NVARCHAR(MAX), -- JSON of subject-wise marks and totals
        TotalMarks DECIMAL(8,2),
        ResultStatus NVARCHAR(20), -- Pass / Fail / Hold
        GeneratedOn DATETIME DEFAULT GETDATE()
    );
END
GO

-- 9) EligibilityChecks (records checks used to allow exam hall ticket)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EligibilityChecks' AND xtype='U')
BEGIN
    CREATE TABLE EligibilityChecks (
        CheckID INT IDENTITY(1,1) PRIMARY KEY,
        TokenNumber NVARCHAR(20),
        Semester NVARCHAR(10),
        FeeCleared BIT DEFAULT 0,
        AttendancePercent DECIMAL(5,2) DEFAULT 0,
        LMSCompletionPercent DECIMAL(5,2) DEFAULT 0,
        AssessmentsCleared BIT DEFAULT 0,
        FinalDecision NVARCHAR(20) DEFAULT 'Pending', -- Eligible / NotEligible / Pending
        CheckedOn DATETIME DEFAULT GETDATE(),
        CheckedBy NVARCHAR(50),
        Remarks NVARCHAR(300)
    );
END
GO

-- 10) Sample default rule for a course (if none exist)
IF NOT EXISTS (SELECT * FROM MarksheetRules WHERE IsDefault = 1)
BEGIN
    INSERT INTO MarksheetRules (CourseID, RuleName, JSONConfig, IsDefault)
    VALUES (1, 'Default CP09 Rule', '{"mid":25,"final":75,"internal":25,"shop_talk":10,"weekend_project":10,"assignments":10,"attendance":10}', 1);
END
GO

PRINT('Exams & Results schema created successfully.');
GO
