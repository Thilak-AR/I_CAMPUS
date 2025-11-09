from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

attendance_bp = Blueprint('attendance_bp', __name__)

# ---------- MARK ATTENDANCE ----------
@attendance_bp.route('/attendance/mark', methods=['POST'])
@role_required(["admin", "teacher", "system"])
def mark_attendance():
    data = request.json
    token = data.get("token_number")
    mode = data.get("mode")   # "rfid" or "biometric"
    location = data.get("location")

    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now()

    # Record raw logs
    if mode == "rfid":
        cursor.execute("INSERT INTO RFID_Logs (TokenNumber, ReaderLocation, ScanTime) VALUES (?, ?, ?)", (token, location, now))
    elif mode == "biometric":
        cursor.execute("INSERT INTO Biometric_Logs (TokenNumber, DeviceLocation, ScanTime) VALUES (?, ?, ?)", (token, location, now))
    else:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid mode"}), 400

    # Determine current class schedule
    day_name = now.strftime("%A")
    time_now = now.time()
    cursor.execute("""
        SELECT TOP 1 ScheduleID, CourseID, StartTime, EndTime
        FROM ClassSchedule
        WHERE DayOfWeek = ? AND ? BETWEEN StartTime AND EndTime
    """, (day_name, time_now))
    schedule = cursor.fetchone()

    if not schedule:
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"{mode.upper()} log stored (outside class hours)"}), 200

    schedule_id, course_id, start_t, end_t = schedule

    # Check if attendance record exists for this class
    cursor.execute("""
        SELECT AttendanceID, RFIDDetected, BiometricDetected FROM Attendance
        WHERE TokenNumber = ? AND ScheduleID = ? AND AttendanceDate = CAST(GETDATE() AS DATE)
    """, (token, schedule_id))
    record = cursor.fetchone()

    if record:
        att_id, rfid_flag, bio_flag = record
        if mode == "rfid": rfid_flag = True
        if mode == "biometric": bio_flag = True
        status = "Present" if rfid_flag and bio_flag else "Flag"
        cursor.execute("""
            UPDATE Attendance
            SET RFIDDetected=?, BiometricDetected=?, Status=?, LastUpdated=GETDATE()
            WHERE AttendanceID=?
        """, (rfid_flag, bio_flag, status, att_id))
    else:
        rfid_flag = mode == "rfid"
        bio_flag = mode == "biometric"
        status = "Pending"
        cursor.execute("""
            INSERT INTO Attendance (TokenNumber, CourseID, ScheduleID, RFIDDetected, BiometricDetected, Status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (token, course_id, schedule_id, rfid_flag, bio_flag, status))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"{mode.upper()} log recorded for {token}"}), 200


# ---------- GET STATUS ----------
@attendance_bp.route('/attendance/status/<token>', methods=['GET'])
@role_required(["student", "teacher", "admin"])
def get_status(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AttendanceDate, Status, RFIDDetected, BiometricDetected
        FROM Attendance
        WHERE TokenNumber = ? ORDER BY AttendanceDate DESC
    """, (token,))
    rows = cursor.fetchall()
    conn.close()
    data = [
        {"date": str(r[0]), "status": r[1], "rfid": bool(r[2]), "biometric": bool(r[3])}
        for r in rows
    ]
    return jsonify({"status": "success", "records": data})
