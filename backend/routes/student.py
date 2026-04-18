from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import pdfplumber
import io
import os
import httpx
import json
import random
import string
import logging
from database import get_db_conn
from dotenv import load_dotenv

load_dotenv()

# Configure Logging
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

router = APIRouter()

class StudentProfile(BaseModel):
    name: str
    email: EmailStr
    degree: str
    gpa: float
    target_country: str
    target_course: str
    budget: int
    timeline: str
    english_test: Optional[str] = ""
    work_exp: Optional[int] = 0
    referral_code: Optional[str] = ""

def generate_unique_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/profile")
def save_profile(profile: StudentProfile):
    """Saves student profile and handles referrals."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            # Generate unique referral code for this new student
            my_referral_code = generate_unique_referral_code()
            
            # Check if this student was referred by someone
            referred_by_id = None
            if profile.referral_code:
                cursor.execute("SELECT id FROM students WHERE referral_code = ?", (profile.referral_code,))
                referrer = cursor.fetchone()
                if referrer:
                    referred_by_id = referrer['id']
                    # Reward the referrer (50 points)
                    cursor.execute("UPDATE students SET referral_points = referral_points + 50 WHERE id = ?", (referred_by_id,))

            cursor.execute('''
                INSERT INTO students 
                (name, email, degree, gpa, target_country, target_course, budget, timeline, english_test, work_exp, referral_code, referred_by, referral_points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (profile.name, profile.email, profile.degree, profile.gpa, profile.target_country, 
                  profile.target_course, profile.budget, profile.timeline, profile.english_test, 
                  profile.work_exp, my_referral_code, referred_by_id, 10 if referred_by_id else 0))
            
            student_id = cursor.lastrowid
            return {
                "student_id": student_id, 
                "message": "Profile saved successfully", 
                "referral_code": my_referral_code
            }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists in our system")
    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        raise HTTPException(status_code=500, detail="System error saving profile")

@router.get("/{student_id}")
def get_profile(student_id: int):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return dict(student)

@router.get("/login/{email}")
def login_by_email(email: str):
    """Simple email-based login."""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE email = ? ORDER BY id DESC LIMIT 1', (email,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="No profile found with this email")
        return dict(student)

@router.post("/scan-transcript")
async def scan_transcript(file: UploadFile = File(...)):
    """AI-powered OCR and data extraction from transcript PDFs."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        content = await file.read()
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not read text from this PDF")

        prompt = f"""Extract student information from transcribed text. 
        Format as JSON with keys: "name", "degree", "gpa" (0-10), "target_course".
        Text:
        {extracted_text[:4000]}"""
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a data extraction AI. Return ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            res_data = response.json()
            if "choices" in res_data:
                return json.loads(res_data['choices'][0]['message']['content'])
            else:
                raise Exception("AI failed to extract data")

    except Exception as e:
        logger.error(f"OCR Scan error: {e}")
        raise HTTPException(status_code=500, detail=f"OCR Scan Failed: {str(e)}")

@router.get("/timeline/{student_id}")
def get_timeline(student_id: int):
    """Generates a dynamic 12-month application timeline based on target enrollment."""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timeline, target_country FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        target_date_str = student['timeline'] # Format: YYYY-MM
        try:
            from datetime import datetime, timedelta
            target_date = datetime.strptime(target_date_str, "%Y-%m")
        except:
            # Fallback if format is wrong
            target_date = datetime.now() + timedelta(days=365)

        milestones = [
            {"month_offset": -12, "task": "Initial Research & Goal Setting", "category": "Discovery", "status": "completed"},
            {"month_offset": -10, "task": "Standardized Test Prep (IELTS/GRE)", "category": "Tests", "status": "active"},
            {"month_offset": -8, "task": "University Shortlisting & Academic CV", "category": "Discovery", "status": "upcoming"},
            {"month_offset": -7, "task": "Take English/Entrance Exams", "category": "Tests", "status": "upcoming"},
            {"month_offset": -6, "task": "SOP & LOR Finalization", "category": "Documents", "status": "upcoming"},
            {"month_offset": -5, "task": "Apply to Universities (Round 1)", "category": "Submission", "status": "upcoming"},
            {"month_offset": -3, "task": "Receive Offers & Secure Funding", "category": "Submission", "status": "upcoming"},
            {"month_offset": -2, "task": "Student Visa Application", "category": "Visa", "status": "upcoming"},
            {"month_offset": 0, "task": "Departure & Virtual Orientation", "category": "Final", "status": "upcoming"}
        ]

        generated_timeline = []
        for m in milestones:
            date = target_date + timedelta(days=m['month_offset'] * 30)
            generated_timeline.append({
                "date": date.strftime("%b %Y"),
                "task": m['task'],
                "category": m['category'],
                "status": m['status']
            })
            
        return generated_timeline

@router.post("/subscribe")
def subscribe_newsletter(data: dict):
    """Growth Engine: Simulated subscription for newsletters and smart nudges."""
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    return {"message": "Success! You are now part of our AI growth loop. Expect smart nudges soon.", "id": "".join(random.choices(string.digits, k=6))}

