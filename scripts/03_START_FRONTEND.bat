@echo off
setlocal
cd /d "%~dp0..\frontend"
if not exist "node_modules\vite" (
  echo ERROR: Frontend dependencies missing.
  echo Run scripts\01_SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
echo Starting CampusMind web interface at http://127.0.0.1:5173
call npm.cmd run dev
if errorlevel 1 (echo Frontend failed. Check port 5173 or installation. & pause)
