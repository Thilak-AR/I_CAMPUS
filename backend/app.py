from flask import Flask, jsonify
from db_connection import get_db_connection
from flask_jwt_extended import JWTManager
from routes_admission import admission_bp
from routes_auth import auth_bp
import os

app = Flask(__name__)

# JWT config
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-change-me")
app.config["JWT_ALGORITHM"] = "HS256"
# Register JWT manager
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(admission_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE();")
        now = cursor.fetchone()[0]
        conn.close()
        return jsonify({"message": "I_Campus backend running successfully!", "server_time": str(now)})
    else:
        return jsonify({"error": "Database connection failed"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
