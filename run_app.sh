#!/bin/bash
# AgentTrader v3.1 — Run Script (Mac/Linux)

set -e

echo "🤖 AgentTrader v3.1 — Starting..."
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Create a .env file and add your API keys."
    exit 1
fi

# Create data directory
mkdir -p data

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install Python deps
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Install frontend deps if needed
if [ ! -d "next-frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    (cd next-frontend && npm install)
fi

echo ""
echo "🚀 Starting Backend API on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 3

echo ""
echo "✅ AgentTrader v3.1 is running!"
echo "   API:      http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Trap Ctrl+C to kill
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT TERM

wait
