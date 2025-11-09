import pyodbc
from loguru import logger
from config import DB_CONFIG

def get_db_connection():
    """
    Creates and returns a new SQL Server database connection.
    Auto-handles trust certificates and logging.
    """
    try:
        conn = pyodbc.connect(
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            "TrustServerCertificate=yes;"
        )
        logger.info("Database connection established successfully.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None
