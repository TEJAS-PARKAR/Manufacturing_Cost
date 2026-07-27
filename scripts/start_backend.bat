@echo off
setlocal

cd /d "%~dp0\.."

call scripts\setup.bat

echo Starting backend on http://localhost:8000 ...
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
