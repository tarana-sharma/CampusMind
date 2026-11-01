@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Run 01_SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules\vite" (
  echo Run 01_SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
echo Launching CampusMind API and web interface...
start "CampusMind Backend" cmd /k call "%~dp002_START_BACKEND.bat"
start "CampusMind Frontend" cmd /k call "%~dp003_START_FRONTEND.bat"
echo Opening your browser...
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173"
echo Both terminal windows must remain open while using CampusMind.
exit /b 0
