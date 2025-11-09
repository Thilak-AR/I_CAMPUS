from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

lms_bp = Blueprint('lms_bp', __name__)

# -----------------------------------------------------------------
# 1️⃣ Upload Study Material (Teacher / HOD / Coordinator)
# -----------------------------------------------------------------
@lms_bp.route('/lms/material/upload', methods=['POST'])
@role_required(["teacher", "hod", "class_coordinator"])
def upload_material():
    data = request.json
    subject_id = data.get("subject_id")
    title = data.get("title")
    description = data.get("description")
    file_path = data.get("file_path")
    file_type = data.get("file_type", "pdf")
    is_public = data.get("is_public", 0)
    uploaded_by = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO StudyMaterials (SubjectID, UploadedBy, Title, Description, FilePath, FileType, IsPublic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (subject_id, uploaded_by, title, description, file_path, file_type, is_public))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Material uploaded successfully"})


# -----------------------------------------------------------------
# 2️⃣ View Study Materials (All users, with cross-access)
# -----------------------------------------------------------------
@lms_bp.route('/lms/materials', methods=['GET'])
@role_required(["student", "teacher", "hod", "admin"])
def view_materials():
    course_filter = request.args.get("course_id", None)
    conn = get_db_connection()
    cursor = conn.cursor()

    if course_filter:
        cursor.execute("""
            SELECT M.MaterialID, S.SubjectName, M.Title, M.FilePath, M.FileType, M.IsPublic
            FROM StudyMaterials M
            JOIN Subjects S ON M.SubjectID = S.SubjectID
            WHERE S.CourseID=? OR M.IsPublic=1
            ORDER BY M.UploadDate DESC
        """, (course_filter,))
    else:
        cursor.execute("""
            SELECT M.MaterialID, S.SubjectName, M.Title, M.FilePath, M.FileType, M.IsPublic
            FROM StudyMaterials M
            JOIN Subjects S ON M.SubjectID = S.SubjectID
            ORDER BY M.UploadDate DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    materials = []
    for r in rows:
        materials.append({
            "material_id": r[0],
            "subject": r[1],
            "title": r[2],
            "file_path": r[3],
            "type": r[4],
            "is_public": bool(r[5])
        })

    return jsonify({"status": "success", "materials": materials})


# -----------------------------------------------------------------
# 3️⃣ Create Assignment (Teacher / HOD)
# -----------------------------------------------------------------
@lms_bp.route('/lms/assignment/create', methods=['POST'])
@role_required(["teacher", "hod"])
def create_assignment():
    data = request.json
    subject_id = data.get("subject_id")
    title = data.get("title")
    description = data.get("description")
    due_date = data.get("due_date")
    max_marks = data.get("max_marks", 10)
    assigned_by = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Assignments (SubjectID, Title, Description, AssignedBy, DueDate, MaxMarks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (subject_id, title, description, assigned_by, due_date, max_marks))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Assignment created successfully"})


# -----------------------------------------------------------------
# 4️⃣ Student Submit Assignment
# -----------------------------------------------------------------
@lms_bp.route('/lms/assignment/submit', methods=['POST'])
@role_required(["student"])
def submit_assignment():
    data = request.json
    assignment_id = data.get("assignment_id")
    file_path = data.get("file_path")
    token = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Submissions (AssignmentID, TokenNumber, FilePath)
        VALUES (?, ?, ?)
    """, (assignment_id, token, file_path))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Assignment submitted successfully"})


# -----------------------------------------------------------------
# 5️⃣ Evaluate Assignment (Teacher / HOD)
# -----------------------------------------------------------------
@lms_bp.route('/lms/assignment/evaluate', methods=['POST'])
@role_required(["teacher", "hod"])
def evaluate_assignment():
    data = request.json
    submission_id = data.get("submission_id")
    marks = data.get("marks")
    feedback = data.get("feedback")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Submissions
        SET MarksAwarded=?, Feedback=?
        WHERE SubmissionID=?
    """, (marks, feedback, submission_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Evaluation updated successfully"})


# -----------------------------------------------------------------
# 6️⃣ Create Quiz (Teacher)
# -----------------------------------------------------------------
@lms_bp.route('/lms/quiz/create', methods=['POST'])
@role_required(["teacher"])
def create_quiz():
    data = request.json
    subject_id = data.get("subject_id")
    question = data.get("question")
    options = data.get("options")
    correct = data.get("correct")
    marks = data.get("marks", 1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Quizzes (SubjectID, Question, OptionA, OptionB, OptionC, OptionD, CorrectOption, Marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (subject_id, question, options["A"], options["B"], options["C"], options["D"], correct, marks))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Quiz question added"})


# -----------------------------------------------------------------
# 7️⃣ Attempt Quiz (Student)
# -----------------------------------------------------------------
@lms_bp.route('/lms/quiz/attempt', methods=['POST'])
@role_required(["student"])
def attempt_quiz():
    data = request.json
    quiz_id = data.get("quiz_id")
    selected = data.get("selected")
    token = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CorrectOption, Marks FROM Quizzes WHERE QuizID=?", (quiz_id,))
    correct_option, marks = cursor.fetchone()

    score = marks if selected.upper() == correct_option.upper() else 0
    cursor.execute("""
        INSERT INTO QuizResults (QuizID, TokenNumber, Score)
        VALUES (?, ?, ?)
    """, (quiz_id, token, score))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "score": score})
