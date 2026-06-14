#!/usr/bin/env bash
# Run GradeOps locally without Docker (SQLite + FastAPI + Vite)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export DATABASE_URL="sqlite:///./gradeops.db"
export USE_MOCK_AI=true
export CORS_ORIGINS="http://localhost:5173"

# Backend setup
if [ ! -d backend/.venv ]; then
  echo "Creating Python virtualenv..."
  python3 -m venv backend/.venv
fi
source backend/.venv/bin/activate
pip install -q -r backend/requirements-dev.txt

# Frontend setup
if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

echo ""
echo "Starting GradeOps..."
echo "  Web app:  http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Demo logins:"
echo "  Instructor: instructor@gradeops.edu / instructor123"
echo "  TA:         ta@gradeops.edu / ta123456"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Start backend in background
(cd backend && uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

# Start frontend in foreground
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
