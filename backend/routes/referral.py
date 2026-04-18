from fastapi import APIRouter, HTTPException
import sqlite3
from database import get_db

router = APIRouter()

import random
import string

def generate_unique_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("/stats/{student_id}")
def get_referral_stats(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current student's info
    cursor.execute("SELECT referral_code, referral_points FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    
    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    
    ref_code = student["referral_code"]
    if not ref_code:
        ref_code = generate_unique_referral_code()
        cursor.execute("UPDATE students SET referral_code = ? WHERE id = ?", (ref_code, student_id))
        conn.commit()
        
    # Get count of people referred
    cursor.execute("SELECT COUNT(*) as count FROM students WHERE referred_by = ?", (student_id,))
    referred_count = cursor.fetchone()['count']
    
    # Get list of people referred (optional, just for demo)
    cursor.execute("SELECT name, created_at FROM students WHERE referred_by = ? LIMIT 5", (student_id,))
    recent_referrals = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "referral_code": ref_code,
        "referral_points": student["referral_points"],
        "total_referrals": referred_count,
        "recent_referrals": recent_referrals
    }
