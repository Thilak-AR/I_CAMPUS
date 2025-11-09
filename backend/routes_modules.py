from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required
from flask_jwt_extended import get_jwt_identity, get_jwt
import datetime

modules_bp = Blueprint('modules_bp', __name__)

@modules_bp.route('/modules/list', methods=['GET'])
@role_required(["admin", "superadmin"])
def list_modules():
    """List all modules and whether enabled for current branch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT B.BranchName, M.ModuleName, BM.IsEnabled
        FROM BranchModules BM
        JOIN Branches B ON BM.BranchID = B.BranchID
        JOIN Modules M ON BM.ModuleID = M.ModuleID
    """)
    data = [{"branch": r[0], "module": r[1], "enabled": bool(r[2])} for r in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "modules": data})


@modules_bp.route('/modules/toggle', methods=['POST'])
@role_required(["admin", "superadmin"])
def toggle_module():
    """Enable or disable a module for a branch"""
    data = request.json
    branch_code = data.get("branch_code")
    module_name = data.get("module_name")
    enable = data.get("enable")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT BranchID FROM Branches WHERE BranchCode = ?", (branch_code,))
    branch = cursor.fetchone()
    if not branch:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid branch"}), 400

    cursor.execute("SELECT ModuleID FROM Modules WHERE ModuleName = ?", (module_name,))
    module = cursor.fetchone()
    if not module:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid module"}), 400

    cursor.execute("""
        UPDATE BranchModules
        SET IsEnabled = ?, LastModified = GETDATE(), ModifiedBy = ?
        WHERE BranchID = ? AND ModuleID = ?
    """, (1 if enable else 0, get_jwt_identity(), branch[0], module[0]))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": f"{module_name} {'enabled' if enable else 'disabled'} for {branch_code}"})
