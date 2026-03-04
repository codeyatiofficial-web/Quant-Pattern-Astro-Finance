#!/bin/bash
# Astro-Finance - Start System Locally
# Starts both FastAPI Backend and Next.js Frontend

echo "🚀 Starting Astro-Finance System..."

# Activate Virtual Environment Check
if [ ! -d "venv" ]; then
    echo "❌ Error: Python virtual environment not found!"
    exit 1
fi

source venv/bin/activate

# 1. Start FastAPI Backend (Port 8000)
echo "🌙 Starting FastAPI Backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 3

# 2. Start Next.js Frontend (Port 3000)
echo "💻 Starting Next.js Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "==========================================="
echo "✅ Backend running at:  http://localhost:8000"
echo "✅ Frontend running at: http://localhost:3000"
echo "==========================================="
echo "Press Ctrl+C to shut down both servers."

# Trap Ctrl+C to kill both services safely
trap "echo 'Shutting down Astro-Finance...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Keep script running
wait
