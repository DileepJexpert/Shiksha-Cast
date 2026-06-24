@echo off
REM Start the Shiksha-Cast backend API on http://localhost:8000
cd /d %~dp0
set PYTHONIOENCODING=utf-8
echo Starting backend on http://localhost:8000  (Ctrl+C to stop)
python -m uvicorn shiksha_cast.server:app --host 127.0.0.1 --port 8000
