from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from auth_utils import role_required, get_actor_role  # assume get_actor_role(token) exists or implement simple helper
from flask_jwt_extended import get_jwt_identity
import json

security_bp = Blueprint('security_bp', __name__)

# -----------------------------
# 1) Toggle module for a branch (only allowed higher-role -> lower-role)
# -----------------------------
@security_bp.route('/security/module/toggle', methods=['POST'])
@role_required(["super_admin","admin"])
def toggle_module():
    data = request.json
    branch_id = data.get("branch_id")
    module_key = data.get("module_key")
    enable = bool(data.get("enable", True))
    actor = get_jwt_identity()
    actor_role = get_actor_role(actor)  # returns role key like 'admin' or 'super_admin'

    conn = get_db_connection()
    cursor = conn.cursor()
    # get module id
    cursor.execute("SELECT ModuleID FROM SystemModules WHERE ModuleKey=?", (module_key,))
    mid = cursor.fetchone()
    if not mid:
        conn.close()
        return jsonify({"status":"error","message":"Module not found"}), 404
    module_id = mid[0]

    # enforce hierarchy: only super_admin can enable core modules globally; admin can toggle branch-level non-core if allowed
    cursor.execute("SELECT IsCore FROM SystemModules WHERE ModuleID=?", (module_id,))
    is_core = cursor.fetchone()[0]

    if actor_role != 'super_admin' and is_core == 1:
        conn.close()
        return jsonify({"status":"error","message":"Only super_admin can toggle core modules"}), 403

    # insert or update toggle
    cursor.execute("""
        MERGE BranchModuleToggles AS T
        USING (SELECT ? AS BranchID, ? AS ModuleID) AS S
        ON T.BranchID = S.BranchID AND T.ModuleID = S.ModuleID
        WHEN MATCHED THEN UPDATE SET IsEnabled=?, ModifiedBy=?, ModifiedOn=GETDATE()
        WHEN NOT MATCHED THEN INSERT (BranchID, ModuleID, IsEnabled, ModifiedBy) VALUES (?, ?, ?, ?);
    """, (branch_id, module_id, enable, actor, branch_id, module_id, enable, actor))
    # log audit
    cursor.execute("""
        INSERT INTO SystemAuditLogs (ActorToken, ActorRole, ActionKey, ResourceType, ResourceID, Details, IPAddress)
        VALUES (?, ?, 'module:toggle', 'Module', ?, ?, ?)
    """, (actor, actor_role, f"ModuleID:{module_id}", json.dumps({"enable": enable, "branch_id": branch_id}), request.remote_addr))
    conn.commit()
    conn.close()
    return jsonify({"status":"success","message":"Module toggle updated"})


# -----------------------------
# 2) Create / list roles (super_admin only can create system roles)
# -----------------------------
@security_bp.route('/security/role/create', methods=['POST'])
@role_required(["super_admin"])
def create_role():
    data = request.json
    rk = data.get("role_key")
    dn = data.get("display_name")
    desc = data.get("description")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO SystemRoles (RoleKey, DisplayName, Description) VALUES (?, ?, ?)", (rk, dn, desc))
    cursor.execute("INSERT INTO SystemAuditLogs (ActorToken, ActorRole, ActionKey, ResourceType, ResourceID, Details, IPAddress) VALUES (?, ?, 'role:create', 'Role', ?, ?, ?)",
                   (get_jwt_identity(), 'super_admin', rk, json.dumps(data), request.remote_addr))
    conn.commit()
    conn.close()
    return jsonify({"status":"success","message":"Role created"}), 201

@security_bp.route('/security/roles', methods=['GET'])
@role_required(["super_admin","admin"])
def list_roles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT RoleID, RoleKey, DisplayName, Description, IsActive FROM SystemRoles")
    rows = cursor.fetchall()
    conn.close()
    roles = [{"role_id":r[0],"role_key":r[1],"display_name":r[2],"description":r[3],"is_active":bool(r[4])} for r in rows]
    return jsonify({"status":"success","roles":roles})


# -----------------------------
# 3) SuperAdmin list management (add/remove) - super_admin only, max 5 enforcement
# -----------------------------
@security_bp.route('/security/superadmin/add', methods=['POST'])
@role_required(["super_admin"])
def add_superadmin():
    data = request.json
    token = data.get("actor_token")
    name = data.get("full_name")
    email = data.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) FROM SuperAdmins")
    count = cursor.fetchone()[0]
    if count >= 5:
        conn.close()
        return jsonify({"status":"error","message":"Max 5 superadmins allowed"}), 400
    cursor.execute("INSERT INTO SuperAdmins (ActorToken, FullName, Email) VALUES (?, ?, ?)", (token, name, email))
    cursor.execute("INSERT INTO SystemAuditLogs (ActorToken, ActorRole, ActionKey, ResourceType, ResourceID, Details, IPAddress) VALUES (?, ?, 'superadmin:add', 'SuperAdmin', ?, ?, ?)",
                   (get_jwt_identity(), get_actor_role(get_jwt_identity()), token, json.dumps(data), request.remote_addr))
    conn.commit()
    conn.close()
    return jsonify({"status":"success","message":"Superadmin added"}), 201


# -----------------------------
# 4) Audit log retrieval (admins & super_admin) with filters
# -----------------------------
@security_bp.route('/security/audit', methods=['GET'])
@role_required(["super_admin","admin","audit"])
def get_audit_logs():
    actor = request.args.get("actor")
    action = request.args.get("action")
    resource = request.args.get("resource")
    limit = int(request.args.get("limit", 200))

    q = "SELECT AuditID, ActorToken, ActorRole, ActionKey, ResourceType, ResourceID, Details, IPAddress, CreatedOn FROM SystemAuditLogs WHERE 1=1"
    params = []
    if actor:
        q += " AND ActorToken=?"; params.append(actor)
    if action:
        q += " AND ActionKey LIKE ?"; params.append(f"%{action}%")
    if resource:
        q += " AND ResourceType=?"; params.append(resource)
    q += " ORDER BY CreatedOn DESC;"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(q, tuple(params))
    rows = cursor.fetchmany(limit)
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "audit_id": r[0],
            "actor_token": r[1],
            "actor_role": r[2],
            "action": r[3],
            "resource_type": r[4],
            "resource_id": r[5],
            "details": r[6],
            "ip": r[7],
            "time": str(r[8])
        })
    return jsonify({"status":"success","logs":logs})


# -----------------------------
# 5) Helper: Get all modules & branch settings
# -----------------------------
@security_bp.route('/security/modules/list', methods=['GET'])
@role_required(["super_admin","admin"])
def list_modules():
    branch_id = request.args.get("branch_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    if branch_id:
        cursor.execute("""
            SELECT M.ModuleKey, M.ModuleName, ISNULL(BT.IsEnabled, 1) AS IsEnabled
            FROM SystemModules M
            LEFT JOIN BranchModuleToggles BT ON M.ModuleID = BT.ModuleID AND BT.BranchID=?
        """, (branch_id,))
        rows = cursor.fetchall()
        modules = [{"module_key":r[0],"module_name":r[1],"is_enabled":bool(r[2])} for r in rows]
    else:
        cursor.execute("SELECT ModuleKey, ModuleName, IsCore FROM SystemModules")
        rows = cursor.fetchall()
        modules = [{"module_key":r[0],"module_name":r[1],"is_core":bool(r[2])} for r in rows]
    conn.close()
    return jsonify({"status":"success","modules":modules})
