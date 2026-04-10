#!/bin/bash
# AgentTrader v2 — Run Script (Mac/Linux)

set -e

echo "🤖 AgentTrader v2 — Starting..."
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copy .env.example to .env and add your API keys."
    echo "   cp .env.example .env"
    exit 1
fi

# Create cache directory
mkdir -p data/cache

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "🚀 Starting Backend (FastAPI) on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 3

echo "🎨 Starting Frontend (Streamlit) on port 8501..."
streamlit run frontend/app.py --server.port 8501 --server.headless true &
FRONTEND_PID=$!

echo ""
echo "✅ AgentTrader v2 is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:8501"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Trap Ctrl+C to kill both
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
