import hashlib
import time
from backend_python.db.database import get_db_connection

def hash_password(password: str) -> str:
    """
    Hashes password using SHA-256 to match Spring Boot AuthService implementation.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(name: str, email: str, password: str):
    """
    Registers a new user in MySQL database.
    """
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or not email.strip() or '@' not in email:
        raise ValueError("Invalid email format")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                raise ValueError(f"User with email {email} already exists.")

            hashed_pw = hash_password(password)
            cursor.execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (%s, %s, %s, %s, NOW(6))",
                (name, email, hashed_pw, 'USER')
            )
            user_id = cursor.lastrowid
            
            token = f"token_{user_id}_{int(time.time() * 1000)}"
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": "USER",
                "token": token
            }
    finally:
        conn.close()

def login_user(email: str, password: str):
    """
    Authenticates user against MySQL database records.
    """
    if not email or not password:
        raise ValueError("Invalid email or password.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, password, role FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Invalid email or password.")

            hashed_pw = hash_password(password)
            if user['password'] != hashed_pw:
                raise ValueError("Invalid email or password.")

            token = f"token_{user['id']}_{int(time.time() * 1000)}"
            return {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "token": token
            }
    finally:
        conn.close()

def get_user_by_id(user_id: int):
    """
    Fetches user record by ID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise ValueError(f"User not found with ID: {user_id}")
            return user
    finally:
        conn.close()
