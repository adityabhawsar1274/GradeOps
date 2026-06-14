# GradeOps

Human-in-the-Loop (HITL) exam grading platform — IIT Guwahati Coding Club Even Semester project.

Automates handwritten exam grading with OCR, agentic LLM rubric evaluation, plagiarism detection, and a high-speed TA review dashboard.

## Features

| Feature | Implementation |
|---------|----------------|
| Bulk exam upload (PDF) | FastAPI multipart upload |
| JSON rubric definition | Granular criteria per question |
| RBAC | Instructor vs TA roles (JWT) |
| OCR pipeline | Tesseract + pdf2image (VLM-ready architecture) |
| Agentic grading | LangGraph pipeline (OpenAI optional) |
| Plagiarism flags | Cross-submission similarity detection |
| TA dashboard | Side-by-side review + keyboard shortcuts (`A` approve, `O` override) |

## Tech Stack 

- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite
- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **ML/AI:** LangChain, LangGraph, Tesseract OCR
- **Auth:** JWT + bcrypt
- **DevOps:** Docker Compose

## Quick Start (Docker)

```bash
cd gradeops
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Instructor | instructor@gradeops.edu | instructor123 |
| TA | ta@gradeops.edu | ta123456 |

**Demo flow:** Login as instructor → **Load Demo Exam** → Logout → Login as TA → Review queue.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL (or use docker compose up db)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
