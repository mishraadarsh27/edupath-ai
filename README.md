# EduPath AI 🎓🚀

**EduPath AI** is a premium, AI-powered student assistant platform designed to simplify the journey of Indian students planning higher education abroad. It provides data-driven insights into university selection, financial ROI, and admission chances through an ultra-modern, responsive interface.

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://edupath-ai-nxm0.onrender.com)

---

## 🌟 Key Features

- **🧠 AI Streaming Mentor**: A real-time intelligent counselor powered by Groq (Llama 3.3). It uses **RAG-lite** (Retrieval-Augmented Generation) to provide factual university recommendations from a curated database.
- **🧭 University Navigator**: Profile-based discovery with match-score algorithms covering the USA, UK, Canada, Germany, and Australia.
- **📊 Real-time ROI Analyzer**: 10-year financial forecasting to help students understand the true value of their international degree.
- **✨ AI Profile Scan**: Instant data extraction from academic transcripts (PDF) using AI-powered OCR.
- **🎯 Admission Predictor**: Probability scoring based on GPA, English proficiency, and work experience.
- **🏦 Loan Gateway**: Instant eligibility checks and EMI comparisons between top Indian banks like SBI and HDFC.
- **🎁 Referral System**: Integrated reward mechanism for students to invite friends and gain points.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5 & Vanilla CSS**: Custom-built design system with light-mode glassmorphism and bento-grid layouts.
- **JavaScript (ES6+)**: Real-time streaming API integration and dynamic UI states.
- **Responsive Design**: Fully optimized for Desktop, Tablet, and Mobile devices.

### Backend
- **FastAPI**: High-performance Python framework for modern APIs.
- **SQLite**: Local database with context-managed connection pools for speed and consistency.
- **Groq AI**: Llama 3.3-70b integration for ultra-low latency intelligent interactions.
- **pdfplumber**: Professional PDF parsing for transcript analysis.

---

## 🚀 Live Deployment

The application is deployed and live at:
🔗 **[https://edupath-ai-nxm0.onrender.com](https://edupath-ai-nxm0.onrender.com)**

---

## ⚙️ Local Development

### Prerequisites
- Python 3.9+
- Groq API Key (Get it at [console.groq.com](https://console.groq.com))

### Steps to Run
1. **Clone the repository:**
   ```bash
   git clone https://github.com/mishraadarsh27/edupath-ai.git
   cd edupath-ai
   ```

2. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the `backend/` folder:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Start the Server:**
   ```bash
   python main.py
   ```

5. **Access the App:**
   Open your browser and go to `http://localhost:8000`.

---

## 📈 Optimization & Architecture
- **Database Context Manager**: Automated connection lifecycle in `database.py`.
- **Streaming Responses**: Implemented via `StreamingResponse` for low latency.
- **Systematic Migrations**: Automated schema updates for production safety.
- **Mobile-First Design**: Media queries at 900px and 600px break-points for fluid UI.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---
**Developed with ❤️ for Students by EduPath AI Team**
