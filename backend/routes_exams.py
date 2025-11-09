from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import json, datetime

exams_bp = Blueprint('exams_bp', __name__)

# -----------------------------------------------------------------
# Add question to QuestionBank (teacher / hod)
# -----------------------------------------------------------------
@exams_bp.route('/exam/question/add', methods=['POST'])
@role_required(["teacher", "hod"])
def add_question():
    data = request.json
    subject_id = data.get("subject_id")
    faculty = get_jwt_identity()
    qtext = data.get("question")
    qtype = data.get("question_type", "mcq")  # mcq/descriptive
    optA = data.get("option_a")
    optB = data.get("option_b")
    optC = data.get("option_c")
    optD = data.get("option_d")
    correct = data.get("correct_option")
    marks = data.get("marks", 1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO QuestionBank
        (SubjectID, FacultyToken, QuestionText, QuestionType, OptionA, OptionB, OptionC, OptionD, CorrectOption, Marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (subject_id, faculty, qtext, qtype, optA, optB, optC, optD, correct, marks))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Question added to bank"}), 201


# -----------------------------------------------------------------
# List questions for a subject (any role with access)
# -----------------------------------------------------------------
@exams_bp.route('/exam/questions/<int:subject_id>', methods=['GET'])
@role_required(["teacher", "hod", "admin", "student"])
def list_questions(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT QuestionID, QuestionText, QuestionType, OptionA, OptionB, OptionC, OptionD, Marks
        FROM QuestionBank
        WHERE SubjectID = ?
        ORDER BY CreatedOn DESC
    """, (subject_id,))
    rows = cursor.fetchall()
    conn.close()

    qs = []
    for r in rows:
        qs.append({
            "question_id": r[0],
            "question": r[1],
            "type": r[2],
            "option_a": r[3],
            "option_b": r[4],
            "option_c": r[5],
            "option_d": r[6],
            "marks": r[7]
        })
    return jsonify({"status": "success", "questions": qs})


# -----------------------------------------------------------------
# Auto-generate an Exam Paper (MCQ part) using random selection
# Input JSON:
# {
#   "exam_id": 1,
#   "subject_id": 1,
#   "mcq_count": 25,
#   "part_meta": {"A": {"count": 25, "marks":1}, "B": {...}}  // optional
# }
# -----------------------------------------------------------------
@exams_bp.route('/exam/paper/generate', methods=['POST'])
@role_required(["teacher", "hod", "admin"])
def generate_paper():
    data = request.json
    exam_id = data.get("exam_id")
    subject_id = data.get("subject_id")
    mcq_count = int(data.get("mcq_count", 25))
    # part_meta optional JSON for complex distribution (not used for simple MCQ only)
    part_meta = data.get("part_meta", None)
    generated_on = datetime.datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()

    # create paper record
    cursor.execute("""
        INSERT INTO ExamPapers (ExamID, SubjectID, GeneratedOn, PaperMeta)
        VALUES (?, ?, ?, ?)
    """, (exam_id, subject_id, generated_on, json.dumps(part_meta) if part_meta else None))
    # get identity
    paper_id = cursor.execute("SELECT @@IDENTITY").fetchval()

    # Select random MCQ questions from question bank using SQL NEWID()
    # Only select mcq type
    cursor.execute(f"""
        SELECT TOP ({mcq_count}) QuestionID, Marks
        FROM QuestionBank
        WHERE SubjectID = ? AND QuestionType = 'mcq'
        ORDER BY NEWID()
    """, (subject_id,))
    chosen = cursor.fetchall()

    seq = 1
    for q in chosen:
        qid = q[0]
        qmarks = q[1] if q[1] is not None else 1
        cursor.execute("""
            INSERT INTO PaperQuestions (PaperID, QuestionID, SeqNo, Marks)
            VALUES (?, ?, ?, ?)
        """, (paper_id, qid, seq, qmarks))
        seq += 1

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "paper_id": paper_id, "questions_selected": len(chosen)}), 201


# -----------------------------------------------------------------
# Get paper and its questions (for proctoring / student attempt)
# -----------------------------------------------------------------
@exams_bp.route('/exam/paper/<int:paper_id>', methods=['GET'])
@role_required(["teacher", "hod", "admin", "student"])
def get_paper(paper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT P.PaperID, P.ExamID, P.SubjectID, P.GeneratedOn, P.PaperMeta
        FROM ExamPapers P
        WHERE P.PaperID = ?
    """, (paper_id,))
    paper = cursor.fetchone()
    if not paper:
        conn.close()
        return jsonify({"status": "error", "message": "Paper not found"}), 404

    cursor.execute("""
        SELECT PQ.SeqNo, Q.QuestionID, Q.QuestionText, Q.OptionA, Q.OptionB, Q.OptionC, Q.OptionD, PQ.Marks
        FROM PaperQuestions PQ
        JOIN QuestionBank Q ON PQ.QuestionID = Q.QuestionID
        WHERE PQ.PaperID = ?
        ORDER BY PQ.SeqNo
    """, (paper_id,))
    rows = cursor.fetchall()
    conn.close()

    questions = []
    for r in rows:
        questions.append({
            "seq_no": r[0],
            "question_id": r[1],
            "question": r[2],
            "option_a": r[3],
            "option_b": r[4],
            "option_c": r[5],
            "option_d": r[6],
            "marks": r[7]
        })

    return jsonify({
        "status": "success",
        "paper": {
            "paper_id": paper[0],
            "exam_id": paper[1],
            "subject_id": paper[2],
            "generated_on": str(paper[3]),
            "meta": paper[4]
        },
        "questions": questions
    })

# ---------- Append / Add to backend/routes_exams.py ----------

from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import json, datetime

# exams_bp already defined above in Part A; reuse it.

# -----------------------------------------------------------------
# 1) Student submits attempt (MCQ answers or descriptive file)
# Body (MCQ): { "paper_id": 1, "answers": {"<question_id>": "A", ...} }
# Body (Descriptive): { "paper_id": 2, "file_path": "uploads/answers/..." }
# -----------------------------------------------------------------
@exams_bp.route('/exam/attempt/submit', methods=['POST'])
@role_required(["student"])
def submit_attempt():
    data = request.json
    token = get_jwt_identity()
    paper_id = data.get("paper_id")
    answers = data.get("answers")      # dict for MCQ
    file_path = data.get("file_path")  # for descriptive

    conn = get_db_connection()
    cursor = conn.cursor()
    started_on = datetime.datetime.now()

    # Insert attempt record
    cursor.execute("""
        INSERT INTO StudentExamAttempts (PaperID, ExamID, TokenNumber, StartedOn, SubmittedOn, Status, AnswerJSON, FilePath)
        SELECT ?, P.ExamID, ?, ?, ?, 'Submitted', ?, ?
        FROM ExamPapers P WHERE P.PaperID=?
    """, (paper_id, token, started_on, started_on, json.dumps(answers) if answers else None, file_path, paper_id))
    attempt_id = cursor.execute("SELECT @@IDENTITY").fetchval()

    # Auto-grade MCQ if answers provided
    total_score = 0.0
    total_marks = 0.0
    if answers:
        # fetch questions for this paper with correct options and marks
        cursor.execute("""
            SELECT PQ.QuestionID, Q.CorrectOption, PQ.Marks
            FROM PaperQuestions PQ
            JOIN QuestionBank Q ON Q.QuestionID = PQ.QuestionID
            WHERE PQ.PaperID = ?
        """, (paper_id,))
        qrows = cursor.fetchall()
        for q in qrows:
            qid, correct_opt, qmarks = q
            total_marks += float(qmarks or 1)
            sel = answers.get(str(qid)) or answers.get(qid)  # accept int keys or str keys
            if sel is not None and correct_opt is not None and str(sel).upper() == str(correct_opt).upper():
                total_score += float(qmarks or 1)

        # store aggregated marks in Marks table
        # Need ExamID and SubjectID for Marks: fetch them
        cursor.execute("SELECT ExamID, SubjectID FROM ExamPapers WHERE PaperID=?", (paper_id,))
        paper_meta = cursor.fetchone()
        exam_id = paper_meta[0]
        subject_id = paper_meta[1]

        cursor.execute("""
            INSERT INTO Marks (AttemptID, TokenNumber, ExamID, SubjectID, MarksObtained, GradedBy, GradeRemarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (attempt_id, token, exam_id, subject_id, total_score, 'system', 'Auto-graded MCQ'))

        # update attempt status to graded
        cursor.execute("UPDATE StudentExamAttempts SET Status='Graded' WHERE AttemptID=?", (attempt_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "attempt_id": int(attempt_id),
        "auto_score": total_score,
        "total_marks": total_marks
    }), 201


# -----------------------------------------------------------------
# 2) Teacher manual grading for descriptive parts (and override)
# Body: { "attempt_id": 12, "marks": 40.5, "remarks": "Good" }
# Role: teacher/hod
# -----------------------------------------------------------------
@exams_bp.route('/exam/attempt/grade', methods=['POST'])
@role_required(["teacher", "hod"])
def grade_attempt():
    data = request.json
    attempt_id = data.get("attempt_id")
    marks = float(data.get("marks", 0))
    remarks = data.get("remarks", "")
    grader = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()

    # get attempt metadata
    cursor.execute("SELECT AttemptID, TokenNumber, ExamID, PaperID FROM StudentExamAttempts WHERE AttemptID=?", (attempt_id,))
    att = cursor.fetchone()
    if not att:
        conn.close()
        return jsonify({"status": "error", "message": "Attempt not found"}), 404

    token = att[1]
    exam_id = att[2]
    paper_id = att[3]

    # determine subject id from paper
    cursor.execute("SELECT SubjectID FROM ExamPapers WHERE PaperID=?", (paper_id,))
    subj = cursor.fetchone()
    subject_id = subj[0] if subj else None

    # Insert or update Marks row
    cursor.execute("SELECT MarkID FROM Marks WHERE AttemptID=?", (attempt_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
            UPDATE Marks
            SET MarksObtained=?, GradedBy=?, GradeRemarks=?, GradedOn=GETDATE()
            WHERE AttemptID=?
        """, (marks, grader, remarks, attempt_id))
    else:
        cursor.execute("""
            INSERT INTO Marks (AttemptID, TokenNumber, ExamID, SubjectID, MarksObtained, GradedBy, GradeRemarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (attempt_id, token, exam_id, subject_id, marks, grader, remarks))

    # mark attempt as Graded
    cursor.execute("UPDATE StudentExamAttempts SET Status='Graded' WHERE AttemptID=?", (attempt_id,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Attempt graded"})


# -----------------------------------------------------------------
# 3) Eligibility check API
#    Computes: fee cleared (no pending bills), attendance %, LMS completion %, average marks
#    Saves a row in EligibilityChecks
# -----------------------------------------------------------------
@exams_bp.route('/exam/eligibility/check/<string:token>/<string:semester>', methods=['POST'])
@role_required(["admin", "hod", "class_coordinator"])
def check_eligibility(token, semester):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1) Fee cleared: if any pending bills exist -> not cleared
    cursor.execute("SELECT COUNT(1) FROM StudentBills WHERE TokenNumber=? AND Status!='Paid'", (token,))
    pending = cursor.fetchone()[0]
    fee_cleared = 0 if pending > 0 else 1

    # 2) Attendance percent: count Present vs total attendance records for that student's course/semester
    # We'll calculate based on Attendance records for that token and distinct ScheduleIDs for the semester
    cursor.execute("""
        SELECT COUNT(1) FROM Attendance
        WHERE TokenNumber=? AND AttendanceDate IS NOT NULL AND Status='Present'
    """, (token,))
    present_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(1) FROM Attendance
        WHERE TokenNumber=? 
    """, (token,))
    total_count = cursor.fetchone()[0]
    attendance_percent = 100.0
    if total_count > 0:
        attendance_percent = round((present_count / total_count) * 100.0, 2)

    # 3) LMS completion percent: ratio of student's submissions to assignments for subjects in their course/semester
    # Find student's course
    cursor.execute("SELECT CourseID FROM Students WHERE TokenNumber=?", (token,))
    c = cursor.fetchone()
    course_id = c[0] if c else None

    lms_percent = 100.0
    if course_id:
        cursor.execute("""
            SELECT COUNT(1) FROM Assignments A
            JOIN Subjects S ON A.SubjectID = S.SubjectID
            WHERE S.CourseID = ?
        """, (course_id,))
        total_assign = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(1) FROM Submissions WHERE TokenNumber = ?
        """, (token,))
        submitted = cursor.fetchone()[0]

        if total_assign > 0:
            lms_percent = round((submitted / total_assign) * 100.0, 2)

    # 4) AssessmentsCleared -> simplest rule: average marks across Marks table >= 40% considered cleared
    cursor.execute("SELECT AVG(CAST(MarksObtained AS FLOAT)) FROM Marks WHERE TokenNumber=?", (token,))
    avg_marks = cursor.fetchone()[0] or 0
    assessments_cleared = 1 if avg_marks >= 40 else 0

    # Final decision: basic pass criteria (all checks)
    final_decision = 'Eligible' if (fee_cleared and attendance_percent >= 75 and lms_percent >= 50 and assessments_cleared) else 'NotEligible'

    # Insert record
    cursor.execute("""
        INSERT INTO EligibilityChecks (TokenNumber, Semester, FeeCleared, AttendancePercent, LMSCompletionPercent, AssessmentsCleared, FinalDecision, CheckedOn, CheckedBy)
        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
    """, (token, semester, fee_cleared, attendance_percent, lms_percent, assessments_cleared, final_decision, get_jwt_identity()))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "fee_cleared": bool(fee_cleared),
        "attendance_percent": attendance_percent,
        "lms_percent": lms_percent,
        "assessments_avg": float(avg_marks),
        "final_decision": final_decision
    })


# -----------------------------------------------------------------
# 4) Generate consolidated marksheet for a student & semester using MarksheetRules JSON
#    Uses rule JSON: e.g. {"mid":25,"final":75,"internal":25,"shop_talk":10,...}
# -----------------------------------------------------------------
@exams_bp.route('/exam/marksheet/generate', methods=['POST'])
@role_required(["admin", "hod", "class_coordinator"])
def generate_marksheet():
    data = request.json
    token = data.get("token_number")
    course_id = data.get("course_id")
    semester = str(data.get("semester"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # fetch applicable rules: course specific or default
    cursor.execute("SELECT JSONConfig FROM MarksheetRules WHERE CourseID=? ORDER BY IsDefault DESC, RuleID DESC", (course_id,))
    row = cursor.fetchone()
    if row and row[0]:
        cfg = json.loads(row[0])
    else:
        # fallback to default rule
        cursor.execute("SELECT JSONConfig FROM MarksheetRules WHERE IsDefault=1")
        r2 = cursor.fetchone()
        cfg = json.loads(r2[0]) if r2 and r2[0] else {"mid":25,"final":75}

    # gather subjects for course & semester
    cursor.execute("SELECT SubjectID, SubjectName FROM Subjects WHERE CourseID=? AND Semester=?", (course_id, semester))
    subjects = cursor.fetchall()

    marksheet = {"subjects": [], "total_obtained": 0.0, "total_max": 0.0}
    total_final_weight = sum([v for k,v in cfg.items() if isinstance(v,(int,float))])

    for subj in subjects:
        subject_id = subj[0]
        subject_name = subj[1]

        # gather average marks per exam-type keys in cfg
        subject_scores = {}
        # initialize
        for key in cfg.keys():
            subject_scores[key] = 0.0

        # fetch marks for this student & subject across exams
        cursor.execute("""
            SELECT E.ExamName, M.MarksObtained, E.TotalMarks
            FROM Marks M
            JOIN Exams E ON M.ExamID = E.ExamID
            WHERE M.TokenNumber=? AND M.SubjectID=?
        """, (token, subject_id))
        mr = cursor.fetchall()

        # aggregate per type
        type_agg = {}
        for rec in mr:
            exam_name, m_obt, total_m = rec
            # map exam_name to key used in cfg
            key = None
            en = exam_name.lower()
            if 'mid' in en: key = 'mid'
            elif 'final' in en or 'end' in en: key = 'final'
            elif 'internal' in en: key = 'internal'
            else:
                # fallback: use exam_name token as is if present in cfg
                for k in cfg.keys():
                    if k.lower() in en:
                        key = k
                        break
            if not key:
                key = 'other'
            if key not in type_agg: type_agg[key] = {"obt":0.0,"max":0.0,"count":0}
            type_agg[key]["obt"] += float(m_obt or 0)
            type_agg[key]["max"] += float(total_m or 0)
            type_agg[key]["count"] += 1

        # compute weighted score
        subject_total = 0.0
        subject_max_equivalent = 0.0
        for k,v in cfg.items():
            if k in type_agg and type_agg[k]["max"] > 0:
                frac = type_agg[k]["obt"] / type_agg[k]["max"]
                # v is percent weight
                subject_score = frac * float(v)
                subject_total += subject_score
                subject_max_equivalent += float(v)
            else:
                # no marks for that component -> contributes 0
                subject_max_equivalent += float(v)

        marksheet["subjects"].append({
            "subject_id": subject_id,
            "subject_name": subject_name,
            "score_weighted": round(subject_total,2),
            "max_weighted": round(subject_max_equivalent,2)
        })
        marksheet["total_obtained"] += subject_total
        marksheet["total_max"] += subject_max_equivalent

    # determine pass/fail simple threshold 40% of total_max
    result_status = "Pass" if (marksheet["total_max"]>0 and (marksheet["total_obtained"]/marksheet["total_max"]*100)>=40) else "Fail"

    # Save GeneratedMarksheet
    cursor.execute("""
        INSERT INTO GeneratedMarksheet (TokenNumber, CourseID, Semester, MarksheetJSON, TotalMarks, ResultStatus)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (token, course_id, semester, json.dumps(marksheet), marksheet["total_obtained"], result_status))

    gen_id = cursor.execute("SELECT @@IDENTITY").fetchval()
    conn.commit()
    conn.close()

    return jsonify({"status":"success", "marksheet_id": int(gen_id), "result": result_status, "marksheet": marksheet})
