from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify
from db_connection import get_db_connection

def role_required(allowed_roles):
    """
    Usage:
    @role_required(["admin", "student"])
    def my_route():
        ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get("role")
                if user_role not in allowed_roles:
                    return jsonify({"status": "error", "message": "Access denied for role"}), 403
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 401
        return wrapper
    return decorator


# ✅ Helper: Get the user's role based on TokenNumber
def get_actor_role(token_number: str):
    """
    Fetch role name from UserRoles table given a TokenNumber.
    Returns 'student' by default if not found.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT RoleName FROM UserRoles WHERE TokenNumber = ?", (token_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        else:
            return "student"
    except Exception as e:
        print(f"[get_actor_role] Error: {e}")
        return "student"
