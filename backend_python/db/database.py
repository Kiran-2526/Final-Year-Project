import pymysql
import pymysql.cursors
from backend_python.config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_db():
    """
    Ensures tables exist in the database.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(255) NOT NULL DEFAULT 'USER',
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                ) ENGINE=InnoDB;
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    image_name VARCHAR(255) NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    predicted_disease VARCHAR(255) NOT NULL,
                    disease_key VARCHAR(255) NOT NULL,
                    confidence DOUBLE NOT NULL,
                    status VARCHAR(255) NOT NULL,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
            """)
        conn.close()
        logger.info("MySQL database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing MySQL database: {e}")
