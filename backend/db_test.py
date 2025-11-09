import pyodbc
from config import DB_CONFIG

def test_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            "TrustServerCertificate=yes;"
        )
        print("✅ Local SQL Server connection successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE();")
        result = cursor.fetchone()
        print(f"🕒 SQL Server Time: {result[0]}")
        conn.close()
    except Exception as e:
        print("❌ Database connection failed!")
        print(str(e))

if __name__ == "__main__":
    test_connection()
