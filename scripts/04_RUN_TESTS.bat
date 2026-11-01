@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist "..\.venv\Scripts\python.exe" (
  echo ERROR: Set up the project first.
  pause
  exit /b 1
)
echo Running custom algorithm and API tests...
"..\.venv\Scripts\python.exe" -m pytest -v tests
pause
