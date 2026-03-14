import sqlite3
import hashlib
import os
import time
from datetime import datetime
import secrets
from cryptography.fernet import Fernet
from dotenv import load_dotenv

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.db')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
ENCRYPTION_KEY = os.getenv("ALGO_ENCRYPTION_KEY")
if ENCRYPTION_KEY:
    cipher = Fernet(ENCRYPTION_KEY.encode())
else:
    cipher = None
    print("WARNING: ALGO_ENCRYPTION_KEY not set in .env. API Keys cannot be securely managed.")

def encrypt_val(val: str) -> str:
    if not cipher or not val: return val
    return cipher.encrypt(val.encode()).decode()

def decrypt_val(val: str) -> str:
    if not cipher or not val: return val
    try:
        return cipher.decrypt(val.encode()).decode()
    except:
        return ""

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_broker_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            broker_name TEXT NOT NULL,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            access_token TEXT,
            is_active BOOLEAN DEFAULT 0,
            trade_multiplier REAL DEFAULT 1.0,
            updated_at TEXT NOT NULL,
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

def save_broker_config(user_id: int, broker_name: str, api_key: str, api_secret: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        enc_key = encrypt_val(api_key.strip())
        enc_secret = encrypt_val(api_secret.strip())
        
        cursor.execute("SELECT id FROM user_broker_configs WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute('''
                UPDATE user_broker_configs 
                SET broker_name=?, api_key=?, api_secret=?, updated_at=? 
                WHERE user_id=?
            ''', (broker_name, enc_key, enc_secret, now, user_id))
        else:
            cursor.execute('''
                INSERT INTO user_broker_configs (user_id, broker_name, api_key, api_secret, updated_at) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, broker_name, enc_key, enc_secret, now))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving broker config: {e}")
        return False

def get_broker_config(user_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT broker_name, api_key, api_secret, access_token, is_active, trade_multiplier FROM user_broker_configs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "broker_name": row[0],
        "api_key": decrypt_val(row[1]),
        "api_secret": decrypt_val(row[2]),
        "access_token": row[3],
        "is_active": bool(row[4]),
        "trade_multiplier": row[5]
    }

def update_broker_status(user_id: int, is_active: bool, access_token: str = None, trade_multiplier: float = None) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        updates.append("is_active=?")
        params.append(int(is_active))
        
        if access_token is not None:
            updates.append("access_token=?")
            params.append(access_token)
            
        if trade_multiplier is not None:
            updates.append("trade_multiplier=?")
            params.append(trade_multiplier)
            
        params.append(user_id)
        
        query = f"UPDATE user_broker_configs SET {', '.join(updates)} WHERE user_id=?"
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating broker status: {e}")
        return False

def get_active_broker_configs() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, broker_name, api_key, api_secret, access_token, trade_multiplier FROM user_broker_configs WHERE is_active=1")
    rows = cursor.fetchall()
    conn.close()
    
    configs = []
    for r in rows:
        # Require an access token for it to be actionable
        if r[4]:
            configs.append({
                "user_id": r[0],
                "broker_name": r[1],
                "api_key": decrypt_val(r[2]),
                "api_secret": decrypt_val(r[3]),
                "access_token": r[4],
                "trade_multiplier": r[5]
            })
    return configs

# Initialize DB on module load
init_db()
