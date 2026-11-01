@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist "..\.venv\Scripts\python.exe" (
  echo ERROR: Python virtual environment missing.
  echo Run scripts\01_SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
echo Starting CampusMind API at http://127.0.0.1:8000
echo Open http://127.0.0.1:8000/docs for interactive API docs.
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
if errorlevel 1 (echo Backend failed. Check port 8000 or installation. & pause)
