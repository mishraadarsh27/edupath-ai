from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import json
import logging
from database import get_db_conn
from dotenv import load_dotenv

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load University data for context
def load_university_context():
    try:
        uni_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "universities.json")
        with open(uni_path, 'r') as f:
            unis = json.load(f)
            # Create a summary of top universities to keep prompt length manageable
            summary = ""
            for u in unis[:15]: # Take top 15 for context
                summary += f"- {u['name']} ({u['country']}): {u['description']}. Cost: {u['annual_cost_inr']} INR/yr.\n"
            return summary
    except Exception as e:
        logger.error(f"Error loading university context: {e}")
        return ""

UNI_CONTEXT = load_university_context()

SYSTEM_PROMPT = f"""You are EduPath AI, a friendly and knowledgeable mentor helping Indian students with study abroad.
Consult this real-time database of universities when giving advice:
{UNI_CONTEXT}

Your goals:
- Give precise university recommendations based on student's GPA and budget.
- Explain visa processes clearly.
- Provide SOP and application tips.
- Be concise (max 4 sentences), professional yet warm.
- Focus on USA, UK, Canada, Germany, and Australia."""

class ChatMessage(BaseModel):
    message: str
    student_id: int
    chat_history: Optional[List[dict]] = []

async def groq_stream_generator(messages: list, student_context: dict = None):
    context = f"\n[STUDENT DATA: GPA {student_context.get('gpa')}, Budget {student_context.get('budget')} INR, Target {student_context.get('target_country')}]" if student_context else ""
    
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT + context}]
    for msg in messages:
        groq_messages.append({"role": msg["role"], "content": msg["content"]})
        
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": groq_messages,
        "stream": True # Enable streaming
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", GROQ_API_URL, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    yield f"AI Error: {response.status_code}"
                    return

                full_response = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            chunk = data_json["choices"][0]["delta"].get("content", "")
                            if chunk:
                                full_response += chunk
                                yield chunk
                        except:
                            continue
                
                # After stream ends, save history
                if student_context and full_response:
                    save_history(student_context['id'], 'assistant', full_response)
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"System error calling AI: {str(e)}"

def save_history(student_id: int, role: str, message: str):
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chat_history (student_id, role, message) VALUES (?, ?, ?)', 
                          (student_id, role, message))
    except Exception as e:
        logger.error(f"Error saving history: {e}")

@router.post("")
async def chat_with_ai(chat: ChatMessage):
    """Main chat endpoint. Returns a stream for better UX."""
    student_ctx = None
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE id = ?', (chat.student_id,))
            student = cursor.fetchone()
            if student:
                student_ctx = dict(student)
                # Save user message
                cursor.execute('INSERT INTO chat_history (student_id, role, message) VALUES (?, ?, ?)', 
                              (chat.student_id, 'user', chat.message))
    except Exception as e:
        logger.error(f"Database error in chat: {e}")

    formatted_messages = []
    for msg in chat.chat_history:
        formatted_messages.append({"role": msg["role"], "content": msg["message"]})
    formatted_messages.append({"role": "user", "content": chat.message})
    
    return StreamingResponse(groq_stream_generator(formatted_messages, student_ctx), media_type="text/event-stream")

@router.get("/history/{student_id}")
def get_chat_history(student_id: int):
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role, message FROM chat_history WHERE student_id = ? ORDER BY created_at ASC', (student_id,))
            history = cursor.fetchall()
            return {"history": [dict(row) for row in history]}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"history": []}

class ContentRequest(BaseModel):
    student_id: int
    content_type: str  # "blog", "newsletter", "reel"

@router.post("/generate-content")
async def generate_marketing_content(req: ContentRequest):
    """Generates personalized study-abroad content for the Growth Engine."""
    student_data = {}
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (req.student_id,))
        student = cursor.fetchone()
        if student:
            student_data = dict(student)

    prompt_map = {
        "blog": f"Write a short, engaging blog post (300 words) for an Indian student planning to study {student_data.get('target_course')} in {student_data.get('target_country')}. Focus on job opportunities and early application benefits. Tone: Inspiring.",
        "newsletter": f"Write an email newsletter subject and body for a student interested in {student_data.get('target_country')}. Mention that for a GPA of {student_data.get('gpa')}, they have great chances.",
        "reel": f"Write a 30-second script for an Instagram Reel about studying in {student_data.get('target_country')}. Include hook, 3 value points, and a CTA for EduPath AI. Keep it catchy."
    }

    prompt = prompt_map.get(req.content_type, "Provide high-value study abroad advice.")
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a creative marketing & admissions AI. Provide high-quality content for students."},
            {"role": "user", "content": prompt}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(GROQ_API_URL, json=payload, headers=headers)
        data = res.json()
        if "choices" in data:
            return {"content": data['choices'][0]['message']['content']}
        else:
            return {"error": "Content generation failed"}

class SOPRequest(BaseModel):
    student_id: int
    sop_text: str

@router.post("/review-sop")
async def review_sop(req: SOPRequest):
    """Deep AI analysis of student SOPs/Essays."""
    student_data = {}
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (req.student_id,))
        student = cursor.fetchone()
        if student:
            student_data = dict(student)

    prompt = f"""You are an Admissions Officer at a top university in {student_data.get('target_country')}.
    Review this Statement of Purpose for a student applying for {student_data.get('target_course')}.
    
    Student Profile: GPA {student_data.get('gpa')}, Experience: {student_data.get('work_exp')} months.
    
    CRITIQUE THE FOLLOWING SOP:
    ---
    {req.sop_text}
    ---
    
    Provide:
    1. Score (0-100)
    2. Strengths (3 points)
    3. Weaknesses/Gaps (3 points)
    4. Actionable improvements.
    
    Format as JSON with keys: "score", "strengths", "weaknesses", "improvements"."""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a professional academic reviewer. Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=40.0) as client:
        res = await client.post(GROQ_API_URL, json=payload, headers=headers)
        data = res.json()
        if "choices" in data:
            return json.loads(data['choices'][0]['message']['content'])
        else:
            return {"error": "SOP Review failed"}

@router.get("/run-agent-loop")
async def run_autonomous_agent():
    """Simulates the Bonus Challenge: Zero-Human AI Growth Loop."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, target_country, gpa FROM students")
            all_students = cursor.fetchall()

        agent_logs = []
        for student in all_students:
            # Simulate "Analysis" phase
            needs_nudge = random.random() > 0.3 # 70% chance they need a nudge
            
            if needs_nudge:
                # Simulate "Generation" phase
                agent_prompt = f"Student {student['name']} is interested in {student['target_country']} with GPA {student['gpa']}. Generate a 1-sentence hyper-personalized nudge."
                
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": agent_prompt}]
                }
                
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
                    res = await client.post(GROQ_API_URL, json=payload, headers=headers)
                    nudget_text = res.json()['choices'][0]['message']['content']
                    
                agent_logs.append({
                    "student_id": student['id'],
                    "action": "PERSONAL_NUDGE_GENERATED",
                    "content": nudget_text,
                    "channel": "PUSH_NOTIFICATION"
                })

        return {
            "status": "success",
            "agent_cycle_id": f"CYCLE_{random.randint(1000, 9999)}",
            "students_analyzed": len(all_students),
            "actions_taken": agent_logs
        }
    except Exception as e:
        logger.error(f"Agent Loop error: {e}")
        return {"status": "error", "message": str(e)}



