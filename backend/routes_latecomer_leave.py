from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

lateleave_bp = Blueprint('lateleave_bp', __name__)

# -----------------------------------------------------------------
# 1️⃣ AUTO-EVALUATE LATE STUDENTS
# -----------------------------------------------------------------
@lateleave_bp.route('/latecomer/evaluate', methods=['POST'])
@role_required(["admin", "superadmin"])
def evaluate_latecomers():
    """Scan today's Attendance, detect late entries, and apply rules"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 1 MaxExcuses, Warning1Limit, Warning2Limit, SuspensionLimit
        FROM LatecomerRules ORDER BY RuleID DESC
    """)
    rules = cursor.fetchone()
    if not rules:
        conn.close()
        return jsonify({"status": "error", "message": "Rules not defined"}), 400

    max_excuse, warn1, warn2, suspend = rules
    today = datetime.date.today()

    cursor.execute("""
        SELECT AttendanceID, TokenNumber, Status, RFIDDetected, BiometricDetected
        FROM Attendance WHERE AttendanceDate = ? AND Status IN ('Flag','Late')
    """, (today,))
    late_entries = cursor.fetchall()

    flagged = 0
    for rec in late_entries:
        att_id, token, status, rfid, bio = rec
        cursor.execute("SELECT LateCount FROM LatecomerRecords WHERE TokenNumber = ?", (token,))
        existing = cursor.fetchone()

        if existing:
            new_count = existing[0] + 1
            if new_count <= max_excuse:
                level = "Excused"
            elif new_count == warn1:
                level = "Warning1"
            elif new_count == warn2:
                level = "Warning2"
            elif new_count >= suspend:
                level = "Suspended"
            else:
                level = "None"

            cursor.execute("""
                UPDATE LatecomerRecords
                SET LateCount=?, WarningLevel=?, LastUpdated=GETDATE()
                WHERE TokenNumber=?
            """, (new_count, level, token))
        else:
            cursor.execute("""
                INSERT INTO LatecomerRecords (TokenNumber, AttendanceID, LateCount, WarningLevel)
                VALUES (?, ?, 1, 'Excused')
            """, (token, att_id))
        flagged += 1

        # Insert a notification
        cursor.execute("""
            INSERT INTO Notifications (TokenNumber, Title, Message, RecipientRole)
            VALUES (?, 'Latecomer Alert',
                    'You were marked late today. Please meet your Class Coordinator.',
                    'student')
        """, (token,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success",
                    "flagged": flagged,
                    "message": "Latecomer evaluation completed"})


# -----------------------------------------------------------------
# 2️⃣ LEAVE APPLICATION
# -----------------------------------------------------------------
@lateleave_bp.route('/leave/apply', methods=['POST'])
@role_required(["student"])
def apply_leave():
    data = request.json
    token = get_jwt_identity()
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    reason = data.get("reason")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LeaveRequests (TokenNumber, FromDate, ToDate, Reason, CurrentApproverRole)
        VALUES (?, ?, ?, ?, 'class_coordinator')
    """, (token, from_date, to_date, reason))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Leave request submitted"})


# -----------------------------------------------------------------
# 3️⃣ APPROVAL FLOW
# -----------------------------------------------------------------
@lateleave_bp.route('/leave/approve', methods=['POST'])
@role_required(["class_coordinator", "hod", "admin", "principal"])
def approve_leave():
    data = request.json
    leave_id = data.get("leave_id")
    decision = data.get("decision")
    comments = data.get("comments", "")
    role = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()

    next_role = None
    if role == "class_coordinator" and decision == "approve":
        next_role = "hod"
    elif role == "hod" and decision == "approve":
        next_role = "admin"
    elif role == "admin" and decision == "approve":
        next_role = "principal"

    if decision == "approve" and next_role:
        cursor.execute("""
            UPDATE LeaveRequests
            SET CurrentApproverRole=?, ApprovedBy=?, Comments=?, LastUpdated=GETDATE()
            WHERE LeaveID=?
        """, (next_role, role, comments, leave_id))
    elif decision == "approve" and role == "principal":
        cursor.execute("""
            UPDATE LeaveRequests
            SET Status='Approved', ApprovedBy=?, Comments=?, LastUpdated=GETDATE()
            WHERE LeaveID=?
        """, (role, comments, leave_id))
    else:
        cursor.execute("""
            UPDATE LeaveRequests
            SET Status='Rejected', RejectedBy=?, Comments=?, LastUpdated=GETDATE()
            WHERE LeaveID=?
        """, (role, comments, leave_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Leave {decision}d by {role}"})


# -----------------------------------------------------------------
# 4️⃣ VIEW NOTIFICATIONS
# -----------------------------------------------------------------
@lateleave_bp.route('/notifications/list', methods=['GET'])
@role_required(["student", "teacher", "admin"])
def view_notifications():
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Title, Message, SentDate, IsRead FROM Notifications
        WHERE TokenNumber = ?
        ORDER BY SentDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()
    data = [{"title": r[0], "message": r[1], "date": str(r[2]), "read": bool(r[3])} for r in rows]
    return jsonify({"status": "success", "notifications": data})
