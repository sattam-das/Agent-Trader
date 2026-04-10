@echo off
setlocal

REM Launch backend API in a new terminal window
start "AgentTrader API" cmd /k python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

REM Launch Streamlit frontend in a new terminal window
start "AgentTrader UI" cmd /k python -m streamlit run frontend/app.py

echo Started AgentTrader services:
echo - API: http://127.0.0.1:8000
echo - UI : http://localhost:8501
