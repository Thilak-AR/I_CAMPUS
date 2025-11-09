from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

# ✅ Create Blueprint
th_bp = Blueprint('th_bp', __name__)

# -------------------------
# 🚍 TRANSPORT APIs
# -------------------------

@th_bp.route('/transport/route/create', methods=['POST'])
@role_required(["admin", "transport_admin"])
def create_route():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO TransportRoutes (RouteName, StartPoint, EndPoint, EstimatedTime)
        VALUES (?, ?, ?, ?)
    """, (data.get("route_name"), data.get("start_point"), data.get("end_point"), data.get("estimated_time")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Route created"}), 201


@th_bp.route('/transport/bus/create', methods=['POST'])
@role_required(["admin", "transport_admin"])
def create_bus():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO TransportBuses (BusNumber, Capacity, DriverName, DriverContact, RouteID)
        VALUES (?, ?, ?, ?, ?)
    """, (data.get("bus_number"), data.get("capacity"), data.get("driver_name"), data.get("driver_contact"), data.get("route_id")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Bus created"}), 201


@th_bp.route('/transport/stops/create', methods=['POST'])
@role_required(["admin", "transport_admin"])
def add_stop():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO TransportStops (RouteID, StopName, SequenceNo, GPSLat, GPSLon)
        VALUES (?, ?, ?, ?, ?)
    """, (data.get("route_id"), data.get("stop_name"), data.get("seq_no"), data.get("gps_lat"), data.get("gps_lon")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Stop added"}), 201


@th_bp.route('/transport/assign', methods=['POST'])
@role_required(["admin", "transport_admin"])
def assign_transport():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO TransportAssignments (TokenNumber, BusID, RouteID, StopID)
        VALUES (?, ?, ?, ?)
    """, (data.get("token_number"), data.get("bus_id"), data.get("route_id"), data.get("stop_id")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Student assigned to transport"}), 201


@th_bp.route('/transport/assignments/<string:token>', methods=['GET'])
@role_required(["student", "admin", "transport_admin", "hod"])
def view_assignments(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TA.AssignmentID, B.BusNumber, R.RouteName, S.StopName
        FROM TransportAssignments TA
        LEFT JOIN TransportBuses B ON TA.BusID = B.BusID
        LEFT JOIN TransportRoutes R ON TA.RouteID = R.RouteID
        LEFT JOIN TransportStops S ON TA.StopID = S.StopID
        WHERE TA.TokenNumber = ?
    """, (token,))
    rows = cursor.fetchall()
    conn.close()
    out = [{"assignment_id": r[0], "bus": r[1], "route": r[2], "stop": r[3]} for r in rows]
    return jsonify({"status": "success", "assignments": out})


@th_bp.route('/transport/scan', methods=['POST'])
@role_required(["transport_admin", "security"])
def record_transport_scan():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO TransportAttendance (TokenNumber, BusID, RouteID, StopID, ScanTime, ReaderID, Method)
        VALUES (?, ?, ?, ?, GETDATE(), ?, ?)
    """, (
        data.get("token_number"),
        data.get("bus_id"),
        data.get("route_id"),
        data.get("stop_id"),
        data.get("reader_id", "RFID_GATE"),
        data.get("method", "RFID")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Transport scan recorded"}), 201


# -------------------------
# 🏠 HOSTEL APIs
# -------------------------

@th_bp.route('/hostel/block/create', methods=['POST'])
@role_required(["admin", "hostel_admin"])
def create_block():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO HostelBlocks (BlockName, Address, ContactNumber, Capacity)
        VALUES (?, ?, ?, ?)
    """, (data.get("block_name"), data.get("address"), data.get("contact_number"), data.get("capacity")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Block created"}), 201


@th_bp.route('/hostel/room/create', methods=['POST'])
@role_required(["admin", "hostel_admin"])
def create_room():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO HostelRooms (BlockID, RoomNumber, BedCount, Occupied, RoomType, Status)
        VALUES (?, ?, ?, 0, ?, 'Available')
    """, (data.get("block_id"), data.get("room_number"), data.get("bed_count"), data.get("room_type")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Room created"}), 201


@th_bp.route('/hostel/allocate', methods=['POST'])
@role_required(["hostel_admin", "admin"])
def allocate_room():
    data = request.json
    token = data.get("token_number")
    block_id = data.get("block_id")
    room_id = data.get("room_id")
    bed_no = data.get("bed_number", None)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT BedCount, Occupied FROM HostelRooms WHERE RoomID=?", (room_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Room not found"}), 404

    bedcount, occupied = row
    if occupied >= bedcount:
        conn.close()
        return jsonify({"status": "error", "message": "Room full"}), 400

    cursor.execute("""
        INSERT INTO HostelAllocations (TokenNumber, BlockID, RoomID, BedNumber)
        VALUES (?, ?, ?, ?)
    """, (token, block_id, room_id, bed_no))
    cursor.execute("UPDATE HostelRooms SET Occupied = Occupied + 1, Status='Occupied' WHERE RoomID=?", (room_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Room allocated"}), 201


@th_bp.route('/hostel/checkout', methods=['POST'])
@role_required(["hostel_admin", "admin"])
def checkout_room():
    data = request.json
    alloc_id = data.get("allocation_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT RoomID, TokenNumber FROM HostelAllocations WHERE AllocationID=? AND Status='Active'", (alloc_id,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        return jsonify({"status": "error", "message": "Allocation not found"}), 404

    room_id, token = r
    cursor.execute("UPDATE HostelAllocations SET Status='CheckedOut', CheckoutOn=GETDATE() WHERE AllocationID=?", (alloc_id,))
    cursor.execute("UPDATE HostelRooms SET Occupied = CASE WHEN Occupied>0 THEN Occupied-1 ELSE 0 END WHERE RoomID=?", (room_id,))

    cursor.execute("SELECT Occupied FROM HostelRooms WHERE RoomID=?", (room_id,))
    occ = cursor.fetchone()[0]

    # ✅ Python-style fix
    if occ == 0:
        cursor.execute("UPDATE HostelRooms SET Status='Available' WHERE RoomID=?", (room_id,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Checked out successfully"}), 200


@th_bp.route('/hostel/mess/generate', methods=['POST'])
@role_required(["hostel_admin", "accounts", "admin"])
def generate_mess_bill():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO HostelMessBills (TokenNumber, MonthYear, Amount, Status)
        VALUES (?, ?, ?, 'Pending')
    """, (data.get("token_number"), data.get("month"), data.get("amount")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Mess bill generated"}), 201


@th_bp.route('/hostel/guest/apply', methods=['POST'])
@role_required(["student"])
def apply_guest():
    data = request.json
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO HostelGuests (HostToken, GuestName, GuestContact, FromDate, ToDate, Status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """, (token, data.get("guest_name"), data.get("guest_contact"), data.get("from_date"), data.get("to_date")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Guest request submitted"}), 201


@th_bp.route('/hostel/guest/approve', methods=['POST'])
@role_required(["hostel_admin", "warden", "admin"])
def approve_guest():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    action = data.get("action")
    approver = get_jwt_identity()

    if action == "approve":
        cursor.execute("UPDATE HostelGuests SET Status='Approved', ApprovedBy=? WHERE GuestID=?", (approver, data.get("guest_id")))
    else:
        cursor.execute("UPDATE HostelGuests SET Status='Rejected', ApprovedBy=? WHERE GuestID=?", (approver, data.get("guest_id")))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Guest request processed"}), 200


@th_bp.route('/hostel/complaint', methods=['POST'])
@role_required(["student", "hostel_admin", "admin"])
def lodge_complaint():
    data = request.json
    token = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO HostelComplaints (TokenNumber, BlockID, RoomID, ComplaintText)
        VALUES (?, ?, ?, ?)
    """, (token, data.get("block_id"), data.get("room_id"), data.get("complaint")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Complaint lodged"}), 201


@th_bp.route('/hostel/complaints/<int:block_id>', methods=['GET'])
@role_required(["hostel_admin", "warden", "admin"])
def view_complaints(block_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ComplaintID, TokenNumber, RoomID, ComplaintText, RaisedOn, Status, ActionTaken
        FROM HostelComplaints WHERE BlockID=? ORDER BY RaisedOn DESC
    """, (block_id,))
    rows = cursor.fetchall()
    conn.close()
    out = [
        {"id": r[0], "token": r[1], "room": r[2], "text": r[3], "date": str(r[4]), "status": r[5], "action": r[6]}
        for r in rows
    ]
    return jsonify({"status": "success", "complaints": out})
