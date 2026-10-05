import sqlite3
from datetime import datetime
from contextlib import closing
from config import DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            notes TEXT,
            created_at TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            timestamp TEXT,
            date TEXT,
            session_id INTEGER,
            UNIQUE(person, date, session_id)
        )""")
        conn.commit()

def create_session(name, notes=""):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO sessions (name, notes, created_at) VALUES (?, ?, ?)",
                    (name, notes, datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid

def list_sessions():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM sessions ORDER BY id DESC")
        return cur.fetchall()

def get_session(sid):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM sessions WHERE id=?", (sid,))
        return cur.fetchone()

def record_attendance_db(person, timestamp_iso, date_iso, session_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO attendance (person, timestamp, date, session_id) VALUES (?, ?, ?, ?)",
                        (person, timestamp_iso, date_iso, session_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def fetch_recent(limit=500):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.person, a.date, COALESCE(s.name,'None'), a.timestamp
            FROM attendance a
            LEFT JOIN sessions s ON a.session_id = s.id
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()

# initialize on import
init_db()
