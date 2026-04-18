from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import sqlite3
from database import get_db
import pdfplumber
import io
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

router = APIRouter()

import uuid
import random
import string

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
    referral_code: str = "" # The code used by this student during signup

def generate_unique_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/profile")
def save_profile(profile: StudentProfile):
    conn = get_db()
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
            # Reward the referrer (e.g., 50 points)
            cursor.execute("UPDATE students SET referral_points = referral_points + 50 WHERE id = ?", (referred_by_id,))

    cursor.execute('''
        INSERT INTO students (name, email, degree, gpa, target_country, target_course, budget, timeline, english_test, work_exp, referral_code, referred_by, referral_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (profile.name, profile.email, profile.degree, profile.gpa, profile.target_country, profile.target_course, profile.budget, profile.timeline, profile.english_test, profile.work_exp, my_referral_code, referred_by_id, 10 if referred_by_id else 0))
    
    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return {"student_id": student_id, "message": "Profile saved successfully", "referral_code": my_referral_code}

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
@router.get("/login/{email}")
def login_by_email(email: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE email = ? ORDER BY id DESC LIMIT 1', (email,))
    student = cursor.fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found with this email")
    return dict(student)

@router.post("/scan-transcript")
async def scan_transcript(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # 1. Extract text from PDF
        content = await file.read()
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")

        # 2. Use AI to parse the text
        prompt = f"""Extract student information from the following transcript text. 
        Return ONLY a JSON object with these keys: "name" (string), "degree" (string), "gpa" (float, out of 10), "target_course" (string).
        If GPA is out of 4.0, convert it to 10.0 scale.
        Text:
        {extracted_text[:3000]}  # Limit text length
        """
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            res_data = response.json()
            ai_json = res_data['choices'][0]['message']['content']
            return json.loads(ai_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Scan Failed: {str(e)}")
