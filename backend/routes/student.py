from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
from database import get_db

router = APIRouter()

class StudentProfile(BaseModel):
    name: str
    email: str = ""
    degree: str
    gpa: float
    target_country: str
    target_course: str
    budget: int
    timeline: str
    english_test: str = ""
    work_exp: int = 0

@router.post("/profile")
def save_profile(profile: StudentProfile):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO students (name, degree, gpa, target_country, target_course, budget, timeline, english_test, work_exp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (profile.name, profile.degree, profile.gpa, profile.target_country, profile.target_course, profile.budget, profile.timeline, profile.english_test, profile.work_exp))
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return {"student_id": student_id, "message": "Profile saved successfully"}

@router.get("/{student_id}")
def get_profile(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(student)
