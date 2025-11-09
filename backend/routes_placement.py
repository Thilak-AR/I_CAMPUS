from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity
import datetime

placement_bp = Blueprint('placement_bp', __name__)

# -------------------------
# Companies CRUD (admin)
# -------------------------
@placement_bp.route('/placement/company/create', methods=['POST'])
@role_required(["admin", "placement_admin"])
def create_company():
    data = request.json
    name = data.get("company_name")
    website = data.get("website")
    contact_person = data.get("contact_person")
    contact_email = data.get("contact_email")
    contact_phone = data.get("contact_phone")
    address = data.get("address")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Companies (CompanyName, Website, ContactPerson, ContactEmail, ContactPhone, Address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, website, contact_person, contact_email, contact_phone, address))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Company created"}), 201


@placement_bp.route('/placement/company/<int:company_id>', methods=['GET'])
@role_required(["admin", "placement_admin", "hod"])
def get_company(company_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CompanyID, CompanyName, Website, ContactPerson, ContactEmail, ContactPhone, Address FROM Companies WHERE CompanyID=?", (company_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return jsonify({"status": "error", "message": "Company not found"}), 404
    return jsonify({"status": "success", "company": {
        "company_id": r[0],
        "company_name": r[1],
        "website": r[2],
        "contact_person": r[3],
        "contact_email": r[4],
        "contact_phone": r[5],
        "address": r[6]
    }})


@placement_bp.route('/placement/company/<int:company_id>', methods=['PUT'])
@role_required(["admin", "placement_admin"])
def update_company(company_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Companies
        SET CompanyName=?, Website=?, ContactPerson=?, ContactEmail=?, ContactPhone=?, Address=?
        WHERE CompanyID=?
    """, (data.get("company_name"), data.get("website"), data.get("contact_person"),
          data.get("contact_email"), data.get("contact_phone"), data.get("address"), company_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Company updated"})


@placement_bp.route('/placement/company/<int:company_id>', methods=['DELETE'])
@role_required(["admin"])
def delete_company(company_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Companies WHERE CompanyID=?", (company_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Company deleted"})


# -------------------------
# Job Openings CRUD (placement_admin / admin)
# -------------------------
@placement_bp.route('/placement/opening/create', methods=['POST'])
@role_required(["placement_admin", "admin"])
def create_opening():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO JobOpenings (CompanyID, Title, OpeningType, Description, Role, Location, Stipend, SalaryRange,
                                 BatchYear, CourseID, Seats, ApplicationStart, ApplicationEnd, CreatedBy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get("company_id"), data.get("title"), data.get("opening_type"), data.get("description"),
          data.get("role"), data.get("location"), data.get("stipend"), data.get("salary_range"),
          data.get("batch_year"), data.get("course_id"), data.get("seats"),
          data.get("application_start"), data.get("application_end"), get_jwt_identity()))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Opening created"}), 201


@placement_bp.route('/placement/openings', methods=['GET'])
@role_required(["placement_admin", "admin", "hod", "student"])
def list_openings():
    # optional query args: course_id, batch_year, status
    course_id = request.args.get("course_id")
    batch_year = request.args.get("batch_year")
    status = request.args.get("status")
    conn = get_db_connection()
    cursor = conn.cursor()

    base = "SELECT OpeningID, CompanyID, Title, OpeningType, Location, BatchYear, CourseID, Seats, ApplicationStart, ApplicationEnd, Status FROM JobOpenings WHERE 1=1"
    params = []
    if course_id:
        base += " AND CourseID=?"
        params.append(course_id)
    if batch_year:
        base += " AND BatchYear=?"
        params.append(batch_year)
    if status:
        base += " AND Status=?"
        params.append(status)

    base += " ORDER BY ApplicationStart DESC"

    cursor.execute(base, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    openings = []
    for r in rows:
        openings.append({
            "opening_id": r[0],
            "company_id": r[1],
            "title": r[2],
            "type": r[3],
            "location": r[4],
            "batch_year": r[5],
            "course_id": r[6],
            "seats": r[7],
            "start": str(r[8]) if r[8] else None,
            "end": str(r[9]) if r[9] else None,
            "status": r[10]
        })
    return jsonify({"status": "success", "openings": openings})


@placement_bp.route('/placement/opening/<int:opening_id>', methods=['GET'])
@role_required(["placement_admin", "admin", "hod", "student"])
def get_opening(opening_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT OpeningID, CompanyID, Title, OpeningType, Description, Role, Location, Stipend, SalaryRange, BatchYear, CourseID, Seats, ApplicationStart, ApplicationEnd, Status FROM JobOpenings WHERE OpeningID=?", (opening_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return jsonify({"status": "error", "message": "Opening not found"}), 404
    return jsonify({"status": "success", "opening": {
        "opening_id": r[0], "company_id": r[1], "title": r[2], "type": r[3], "description": r[4],
        "role": r[5], "location": r[6], "stipend": float(r[7]) if r[7] is not None else None, "salary_range": r[8],
        "batch_year": r[9], "course_id": r[10], "seats": r[11], "start": str(r[12]) if r[12] else None,
        "end": str(r[13]) if r[13] else None, "status": r[14]
    }})


@placement_bp.route('/placement/opening/<int:opening_id>', methods=['PUT'])
@role_required(["placement_admin", "admin"])
def update_opening(opening_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE JobOpenings
        SET Title=?, OpeningType=?, Description=?, Role=?, Location=?, Stipend=?, SalaryRange=?, BatchYear=?, CourseID=?, Seats=?, ApplicationStart=?, ApplicationEnd=?, Status=?
        WHERE OpeningID=?
    """, (data.get("title"), data.get("opening_type"), data.get("description"), data.get("role"), data.get("location"),
          data.get("stipend"), data.get("salary_range"), data.get("batch_year"), data.get("course_id"), data.get("seats"),
          data.get("application_start"), data.get("application_end"), data.get("status", "Open"), opening_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Opening updated"})


@placement_bp.route('/placement/opening/<int:opening_id>', methods=['DELETE'])
@role_required(["admin"])
def delete_opening(opening_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM JobOpenings WHERE OpeningID=?", (opening_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Opening deleted"})


# -------------------------
# Student apply to opening (student)
# -------------------------
@placement_bp.route('/placement/apply', methods=['POST'])
@role_required(["student"])
def apply_opening():
    data = request.json
    opening_id = data.get("opening_id")
    resume_path = data.get("resume_path")  # store path, not raw file content
    token = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    # prevent duplicate application
    cursor.execute("SELECT COUNT(1) FROM PlacementApplications WHERE OpeningID=? AND TokenNumber=?", (opening_id, token))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({"status": "error", "message": "Already applied"}), 400

    cursor.execute("""
        INSERT INTO PlacementApplications (OpeningID, TokenNumber, ResumePath, Status)
        VALUES (?, ?, ?, 'Applied')
    """, (opening_id, token, resume_path))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Applied successfully"}), 201


# -------------------------
# Interview rounds & results
# -------------------------
@placement_bp.route('/placement/round/create', methods=['POST'])
@role_required(["placement_admin", "admin"])
def create_interview_round():
    data = request.json
    opening_id = data.get("opening_id")
    round_name = data.get("round_name")
    round_date = data.get("round_date")
    conducted_by = data.get("conducted_by", get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO InterviewRounds (OpeningID, RoundName, RoundDate, ConductedBy)
        VALUES (?, ?, ?, ?)
    """, (opening_id, round_name, round_date, conducted_by))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Interview round created"}), 201


@placement_bp.route('/placement/round/<int:round_id>/result', methods=['POST'])
@role_required(["placement_admin", "admin", "interviewer", "hod"])
def submit_interview_result(round_id):
    data = request.json
    application_id = data.get("application_id")
    score = data.get("score")
    status = data.get("status")  # Pass / Fail / Hold
    feedback = data.get("feedback", "")
    evaluator = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO InterviewResults (RoundID, ApplicationID, Score, Status, Feedback, EvaluatedBy)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (round_id, application_id, score, status, feedback, evaluator))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Interview result submitted"}), 201


# -------------------------
# Offer issuance (company or placement_admin)
# -------------------------
@placement_bp.route('/placement/offer/create', methods=['POST'])
@role_required(["placement_admin", "admin"])
def create_offer():
    data = request.json
    application_id = data.get("application_id")
    company_id = data.get("company_id")
    offered_role = data.get("offered_role")
    ctc = data.get("ctc")
    stipend = data.get("stipend")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Offers (ApplicationID, CompanyID, OfferedRole, CTC, Stipend, OfferStatus)
        VALUES (?, ?, ?, ?, ?, 'Offered')
    """, (application_id, company_id, offered_role, ctc, stipend))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Offer created"}), 201


# Student accept / decline
@placement_bp.route('/placement/offer/respond', methods=['POST'])
@role_required(["student"])
def respond_offer():
    data = request.json
    offer_id = data.get("offer_id")
    action = data.get("action")  # accept / decline
    token = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()
    if action == "accept":
        cursor.execute("UPDATE Offers SET OfferStatus='Accepted', AcceptanceDate=GETDATE() WHERE OfferID=?", (offer_id,))
        # find application and create StudentPlacements
        cursor.execute("SELECT ApplicationID, CompanyID, OfferedRole FROM Offers WHERE OfferID=?", (offer_id,))
        r = cursor.fetchone()
        if r:
            application_id, company_id, role = r[0], r[1], r[2]
            cursor.execute("""
                INSERT INTO StudentPlacements (TokenNumber, OfferID, CompanyID, Role, StartDate, IsInternship)
                VALUES (?, ?, ?, ?, GETDATE(), 0)
            """, (token, offer_id, company_id, role))
    else:
        cursor.execute("UPDATE Offers SET OfferStatus='Declined' WHERE OfferID=?", (offer_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Offer {action}ed"})


# -------------------------
# Placement reports & search
# -------------------------
@placement_bp.route('/placement/report/student/<string:token>', methods=['GET'])
@role_required(["placement_admin", "admin", "hod"])
def student_placement_report(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT P.PlacementID, P.TokenNumber, O.OfferedRole, C.CompanyName, P.StartDate, P.EndDate, P.IsInternship
        FROM StudentPlacements P
        JOIN Offers O ON P.OfferID = O.OfferID
        JOIN Companies C ON P.CompanyID = C.CompanyID
        WHERE P.TokenNumber=?
    """, (token,))
    rows = cursor.fetchall()
    conn.close()
    placements = []
    for r in rows:
        placements.append({
            "placement_id": r[0],
            "token": r[1],
            "role": r[2],
            "company": r[3],
            "start": str(r[4]) if r[4] else None,
            "end": str(r[5]) if r[5] else None,
            "is_internship": bool(r[6])
        })
    return jsonify({"status": "success", "placements": placements})


@placement_bp.route('/placement/report/company/<int:company_id>', methods=['GET'])
@role_required(["placement_admin", "admin"])
def company_placement_report(company_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT P.PlacementID, P.TokenNumber, O.OfferedRole, P.StartDate, P.EndDate, P.IsInternship
        FROM StudentPlacements P
        JOIN Offers O ON P.OfferID = O.OfferID
        WHERE P.CompanyID=?
    """, (company_id,))
    rows = cursor.fetchall()
    conn.close()
    data = []
    for r in rows:
        data.append({
            "placement_id": r[0],
            "token": r[1],
            "role": r[2],
            "start": str(r[3]) if r[3] else None,
            "end": str(r[4]) if r[4] else None,
            "is_internship": bool(r[5])
        })
    return jsonify({"status": "success", "placements": data})


# -------------------------
# PII Audit Logging (who downloaded / viewed resume)
# -------------------------
@placement_bp.route('/placement/piaudit/log', methods=['POST'])
@role_required(["placement_admin", "admin", "hod", "interviewer"])
def log_pii_access():
    data = request.json
    token = data.get("token_number")  # student whose resume was accessed
    actor = get_jwt_identity()  # staff token
    action = data.get("action")  # ViewResume / DownloadResume / Share
    ip = request.remote_addr

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO PlacementPIIAudit (TokenNumber, Actor, Action, IPAddress)
        VALUES (?, ?, ?, ?)
    """, (token, actor, action, ip))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "PII access logged"}), 201
