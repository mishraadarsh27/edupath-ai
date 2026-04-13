from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from database import get_db
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are EduPath AI, a friendly and knowledgeable mentor 
helping Indian students with study abroad decisions. You help with:
- University selection for USA, UK, Canada, Germany, Australia
- Visa processes and requirements  
- Education loan guidance in India
- SOP and application tips
- Career prospects
Be concise (max 3-4 sentences), warm, and encouraging. 
Always respond in simple English that Indian students can understand."""

class ChatMessage(BaseModel):
    message: str
    student_id: int
    chat_history: Optional[List[dict]] = []

async def get_groq_response(messages: list, student_context: dict = None):
    context = f"\nStudent Profile: GPA {student_context.get('gpa')}, Target: {student_context.get('target_country')}, Course: {student_context.get('target_course')}" if student_context else ""
    
    # Format messages for Groq
    groq_messages = [
        {"role": "system", "content": SYSTEM_PROMPT + context}
    ]
    for msg in messages:
        groq_messages.append({"role": msg["role"], "content": msg["content"]})
        
    payload = {
        "model": "llama3-8b-8192",
        "messages": groq_messages
    }
    
    api_key = GROQ_API_KEY or "no-key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return f"Error from AI: {data.get('error', 'Unknown error')}"
        except Exception as e:
            return f"System error calling AI: {str(e)}"

@router.post("")
async def chat_with_ai(chat: ChatMessage):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (chat.student_id,))
    student = cursor.fetchone()
    student_ctx = dict(student) if student else None
    
    cursor.execute('INSERT INTO chat_history (student_id, role, message) VALUES (?, ?, ?)', (chat.student_id, 'user', chat.message))
    
    formatted_messages = []
    for msg in chat.chat_history:
        formatted_messages.append({"role": msg["role"], "content": msg["message"]})
    formatted_messages.append({"role": "user", "content": chat.message})
    
    ai_response = await get_groq_response(formatted_messages, student_ctx)
    
    cursor.execute('INSERT INTO chat_history (student_id, role, message) VALUES (?, ?, ?)', (chat.student_id, 'assistant', ai_response))
    conn.commit()
    conn.close()
    
    return {"message": ai_response}

@router.get("/history/{student_id}")
def get_chat_history(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT role, message FROM chat_history WHERE student_id = ? ORDER BY created_at ASC', (student_id,))
    history = cursor.fetchall()
    conn.close()
    return {"history": [dict(row) for row in history]}
