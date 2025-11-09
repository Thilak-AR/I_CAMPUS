from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify

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
