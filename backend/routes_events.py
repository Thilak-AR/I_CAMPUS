from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

events_bp = Blueprint('events_bp', __name__)

# -----------------------------------------------------------------
# 1️⃣ CREATE EVENT (Admin / HOD / Class Coordinator)
# -----------------------------------------------------------------
@events_bp.route('/events/create', methods=['POST'])
@role_required(["admin", "hod", "class_coordinator"])
def create_event():
    data = request.json
    category_id = data.get("category_id")
    title = data.get("title")
    description = data.get("description")
    organized_by = data.get("organized_by")
    venue = data.get("venue")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    semester = data.get("semester")
    course_id = data.get("course_id")
    branch_id = data.get("branch_id")

    user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Events (CategoryID, Title, Description, OrganizerRole, OrganizedBy, Venue,
                            StartDate, EndDate, Semester, CourseID, BranchID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category_id, title, description, user, organized_by, venue,
          start_date, end_date, semester, course_id, branch_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Event created successfully"})


# -----------------------------------------------------------------
# 2️⃣ LIST ALL EVENTS
# -----------------------------------------------------------------
@events_bp.route('/events/list', methods=['GET'])
@role_required(["admin", "hod", "teacher", "student"])
def list_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT E.EventID, C.CategoryName, E.Title, E.Venue, E.StartDate, E.EndDate, E.Status
        FROM Events E
        JOIN EventCategories C ON E.CategoryID = C.CategoryID
        ORDER BY E.StartDate DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        events.append({
            "event_id": r[0],
            "category": r[1],
            "title": r[2],
            "venue": r[3],
            "start_date": str(r[4]),
            "end_date": str(r[5]),
            "status": r[6]
        })

    return jsonify({"status": "success", "events": events})


# -----------------------------------------------------------------
# 3️⃣ REGISTER PARTICIPANT (Student)
# -----------------------------------------------------------------
@events_bp.route('/events/register', methods=['POST'])
@role_required(["student"])
def register_participant():
    token = get_jwt_identity()
    data = request.json
    event_id = data.get("event_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM EventParticipants WHERE TokenNumber=? AND EventID=?)
        BEGIN
            INSERT INTO EventParticipants (EventID, TokenNumber, Role)
            VALUES (?, ?, 'student')
        END
    """, (token, event_id, event_id, token))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "You are registered for the event"})


# -----------------------------------------------------------------
# 4️⃣ MARK PARTICIPATION (Admin / HOD / Coordinator)
# -----------------------------------------------------------------
@events_bp.route('/events/mark', methods=['POST'])
@role_required(["admin", "hod", "class_coordinator"])
def mark_participation():
    data = request.json
    participant_id = data.get("participant_id")
    status = data.get("status")
    marks = data.get("marks")
    feedback = data.get("feedback")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE EventParticipants
        SET ParticipationStatus=?, MarksAwarded=?, Feedback=?, UploadedOn=GETDATE()
        WHERE ParticipantID=?
    """, (status, marks, feedback, participant_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Participation updated"})


# -----------------------------------------------------------------
# 5️⃣ UPLOAD PROOF (Any authorized user)
# -----------------------------------------------------------------
@events_bp.route('/events/proof', methods=['POST'])
@role_required(["admin", "hod", "teacher", "class_coordinator", "student"])
def upload_proof():
    data = request.json
    event_id = data.get("event_id")
    proof_type = data.get("proof_type")
    file_path = data.get("file_path")  # for now store URL or local path
    user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO EventProofs (EventID, UploadedBy, ProofType, FilePath)
        VALUES (?, ?, ?, ?)
    """, (event_id, user, proof_type, file_path))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Proof uploaded successfully"})


# -----------------------------------------------------------------
# 6️⃣ VIEW PARTICIPANTS FOR AN EVENT
# -----------------------------------------------------------------
@events_bp.route('/events/participants/<int:event_id>', methods=['GET'])
@role_required(["admin", "hod", "class_coordinator"])
def view_participants(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ParticipantID, TokenNumber, Role, ParticipationStatus, MarksAwarded, Feedback
        FROM EventParticipants
        WHERE EventID=?
    """, (event_id,))
    rows = cursor.fetchall()
    conn.close()

    participants = []
    for r in rows:
        participants.append({
            "participant_id": r[0],
            "token_number": r[1],
            "role": r[2],
            "status": r[3],
            "marks": r[4],
            "feedback": r[5]
        })

    return jsonify({"status": "success", "participants": participants})
