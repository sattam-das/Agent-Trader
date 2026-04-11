@echo off
setlocal

REM Launch backend API in a new terminal window
start "AgentTrader API" cmd /k python -m uvicorn backend.main:app --host localhost --port 8000 --reload

REM Launch React frontend in a new terminal window
start "AgentTrader UI" cmd /k "cd next-frontend && npm run dev"

echo Started AgentTrader services:
echo - API: http://localhost:8000
echo - UI : http://localhost:5173
