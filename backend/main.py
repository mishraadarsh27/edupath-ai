from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
import os

from routes import student, ai, loan, universities, referral

app = FastAPI(title="EduPath AI API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(universities.router, prefix="/api", tags=["Universities & Prediction"])
app.include_router(ai.router, prefix="/api/chat", tags=["AI"])
app.include_router(loan.router, prefix="/api/loan", tags=["Loan"])
app.include_router(referral.router, prefix="/api/referral", tags=["Referral"])

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Serve static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount frontend files
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
