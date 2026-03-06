import sqlite3
import hashlib
import os
import time
from datetime import datetime
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def _hash_password(password: str) -> str:
    # Adding a simple salt string for basic security
    salted = password + "taksha2026_salt"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def create_user(email: str, password: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                       (email, _hash_password(password), now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def verify_user(email: str, password: str) -> int:
    """Returns user_id if valid, else None."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row and row[1] == _hash_password(password):
            return row[0]
        return None
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None

def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    # 30 days expiration
    expires_at = time.time() + (30 * 24 * 60 * 60)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                   (token, user_id, expires_at))
    conn.commit()
    conn.close()
    return token

def get_user_from_token(token: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.email, s.expires_at 
        FROM sessions s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.token = ?
    ''', (token,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    user_id, email, expires_at = row
    if time.time() > expires_at:
        # Session expired
        return None
        
    return {"id": user_id, "email": email}

def get_all_users():
    """Returns all registered users for CSV export."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "email": r[1], "signup_date": r[2]} for r in rows]
    except Exception:
        return []

# Initialize DB on module load
init_db()
