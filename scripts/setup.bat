@echo off
setlocal

cd /d "%~dp0\.."

:: ── Python setup ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is required but not installed or not on PATH.
    exit /b 1
)

if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

echo Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt --quiet

:: ── Node.js setup ──
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is required but not installed or not on PATH.
    echo Install it from https://nodejs.org/ and try again.
    exit /b 1
)

echo Installing frontend dependencies...
cd frontend
call npm install
cd /d "%~dp0\.."

echo.
echo Setup complete!
echo   Backend:  .venv\Scripts\activate
echo   Frontend: cd frontend ^&^& npm run dev
