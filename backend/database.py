import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "edupath.db")

@contextmanager
def get_db_conn():
    """Context manager for database connections. Handles commits and rollbacks automatically."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_db():
    """Legacy helper for existing code that doesn't use the context manager yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema and handle automatic migrations."""
    with get_db_conn() as conn:
        cursor = conn.cursor()

        # Core Students Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            degree TEXT,
            gpa REAL,
            target_country TEXT,
            target_course TEXT,
            budget INTEGER,
            timeline TEXT,
            english_test TEXT,
            work_exp INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            referral_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Saved Universities Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            university_name TEXT NOT NULL,
            country TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
        ''')

        # Chat History Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
        ''')

        # Loan Applications Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            loan_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
        ''')

        # Robust Migration: Check for columns and add if missing
        cursor.execute("PRAGMA table_info(students)")
        existing_cols = [row['name'] for row in cursor.fetchall()]
        
        migrations = {
            "english_test": "TEXT",
            "work_exp": "INTEGER DEFAULT 0",
            "email": "TEXT",
            "referral_code": "TEXT UNIQUE",
            "referred_by": "INTEGER",
            "referral_points": "INTEGER DEFAULT 0"
        }

        for col, type_ in migrations.items():
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE students ADD COLUMN {col} {type_}")
                except sqlite3.OperationalError:
                    pass
