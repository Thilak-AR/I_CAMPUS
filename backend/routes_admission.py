from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
import datetime

admission_bp = Blueprint('admission_bp', __name__)

@admission_bp.route('/admission/register', methods=['POST'])
def register_student():
    try:
        data = request.json
        full_name = data['full_name']
        course = data['course']
        batch = data['batch']
        dob = datetime.datetime.strptime(data['dob'], "%Y-%m-%d").date()

        # Generate Token: NEC + CourseCode + BatchYear(last2) + autoID style
        token_number = f"NEC{course}{str(batch)[-2:]}{int(datetime.datetime.now().timestamp())%1000}"

        # Create Email
        email = f"{token_number.lower()}@nttf.co.in"

        # Default Password: DOB in DDMMYY
        password = dob.strftime("%d%m%y")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Students (TokenNumber, FullName, CourseCode, BatchYear, DOB, Email, Password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (token_number, full_name, course, batch, dob, email, password))
        conn.commit()
        conn.close()

        # Insert default role as 'student'
        cursor = conn.cursor()
        cursor.execute("INSERT INTO UserRoles (TokenNumber, RoleName) VALUES (?, ?)", (token_number, 'student'))
        conn.commit()


        return jsonify({
            "status": "success",
            "message": "Student registered successfully",
            "token_number": token_number,
            "email": email,
            "default_password": password
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
