@echo off
setlocal

cd /d "%~dp0\.."

call scripts\setup.bat

echo Starting React frontend on http://localhost:5173 ...
cd frontend
call npm run dev
