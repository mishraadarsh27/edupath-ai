import sqlite3
import os

DB_PATH = "edupath.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      email TEXT,
      degree TEXT,
      gpa REAL,
      target_country TEXT,
      target_course TEXT,
      budget INTEGER,
      timeline TEXT,
      english_test TEXT,
      work_exp INTEGER,
      referral_code TEXT UNIQUE,
      referred_by INTEGER,
      referral_points INTEGER DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN english_test TEXT")
        cursor.execute("ALTER TABLE students ADD COLUMN work_exp INTEGER")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
        cursor.execute("ALTER TABLE students ADD COLUMN referral_code TEXT")
        cursor.execute("ALTER TABLE students ADD COLUMN referred_by INTEGER")
        cursor.execute("ALTER TABLE students ADD COLUMN referral_points INTEGER DEFAULT 0")
    except:
        pass

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS saved_universities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER,
      university_name TEXT,
      country TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER,
      role TEXT,
      message TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS loan_applications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER,
      loan_amount REAL,
      status TEXT DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
