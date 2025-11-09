# backend/routes_auth.py
from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
import datetime
from auth_utils import role_required

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "email and password required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TokenNumber, Password FROM Students WHERE Email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "invalid credentials"}), 401

        token_number, stored_password = row[0], row[1]
        if stored_password != password:
            conn.close()
            return jsonify({"status": "error", "message": "invalid credentials"}), 401

        # Role lookup (safe)
        role_cursor = conn.cursor()
        role_cursor.execute("SELECT RoleName FROM UserRoles WHERE TokenNumber = ?", (token_number,))
        role_row = role_cursor.fetchone()
        role = role_row[0] if role_row else "student"
        conn.close()

        from flask_jwt_extended import create_access_token
        import datetime
        expires = datetime.timedelta(days=1)
        additional_claims = {"role": role}
        access_token = create_access_token(
            identity=token_number,
            additional_claims=additional_claims,
            expires_delta=expires
        )

        return jsonify({
            "status": "success",
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": int(expires.total_seconds())
        }), 200

    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/student/dashboard', methods=['GET'])
@jwt_required()
def student_dashboard():
    """
    Protected sample route for student role.
    """
    identity = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')
    if role != 'student':
        return jsonify({"status": "error", "message": "forbidden"}), 403

    # Example: fetch student's basic info from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT FullName, CourseCode, BatchYear FROM Students WHERE TokenNumber = ?", (identity,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "error", "message": "student not found"}), 404

    full_name, course, batch = row[0], row[1], row[2]
    return jsonify({
        "status": "success",
        "student": {
            "token": identity,
            "name": full_name,
            "course": course,
            "batch": batch
        }
    })


@auth_bp.route('/admin/dashboard', methods=['GET'])
@role_required(["admin", "superadmin"])
def admin_dashboard():
    return jsonify({
        "status": "success",
        "dashboard": "admin_dashboard",
        "message": "Welcome, Admin! Here's your overview."
    })


@auth_bp.route('/superadmin/dashboard', methods=['GET'])
@role_required(["superadmin"])
def superadmin_dashboard():
    return jsonify({
        "status": "success",
        "dashboard": "superadmin_dashboard",
        "message": "Welcome Super Admin — full system access granted."
    })

@auth_bp.route('/system/hierarchy', methods=['GET'])
@role_required(["superadmin", "admin"])
def view_hierarchy():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT I.InstitutionName, B.BranchName, C.CourseName
        FROM Institutions I
        JOIN Branches B ON I.InstitutionID = B.InstitutionID
        JOIN Courses C ON B.BranchID = C.BranchID
    """)
    rows = cursor.fetchall()
    conn.close()

    data = [{"Institution": r[0], "Branch": r[1], "Course": r[2]} for r in rows]
    return jsonify({"status": "success", "hierarchy": data})
