from fastapi import APIRouter, HTTPException
import logging
from database import get_db_conn
import random
import string

logger = logging.getLogger(__name__)
router = APIRouter()

def generate_unique_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("/stats/{student_id}")
def get_referral_stats(student_id: int):
    """Fetches referral metrics for a specific student."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Get current student's info
            cursor.execute("SELECT referral_code, referral_points FROM students WHERE id = ?", (student_id,))
            student = cursor.fetchone()
            
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            
            ref_code = student["referral_code"]
            if not ref_code:
                ref_code = generate_unique_referral_code()
                cursor.execute("UPDATE students SET referral_code = ? WHERE id = ?", (ref_code, student_id))
                
            # Get metrics
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE referred_by = ?", (student_id,))
            referred_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT name, created_at FROM students WHERE referred_by = ? ORDER BY created_at DESC LIMIT 5", (student_id,))
            recent_referrals = [dict(row) for row in cursor.fetchall()]
            
            return {
                "referral_code": ref_code,
                "referral_points": student["referral_points"],
                "total_referrals": referred_count,
                "recent_referrals": recent_referrals
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Referral stats error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching referral stats")
