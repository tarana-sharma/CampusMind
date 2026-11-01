@echo off
setlocal
cd /d "%~dp0.."
echo.
echo  =================================================
echo       CAMPUSMIND - FIRST TIME SETUP
 echo  =================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (echo ERROR: Python is missing from PATH. & goto :failed)
  set "PYTHON=python"
)
where node >nul 2>nul
if errorlevel 1 (echo ERROR: Node.js is missing. Install LTS from nodejs.org. & goto :failed)
where npm.cmd >nul 2>nul
if errorlevel 1 (echo ERROR: npm is missing. Repair Node.js. & goto :failed)
echo [1/4] Checking installed versions...
%PYTHON% --version
node --version
call npm.cmd --version
if errorlevel 1 goto :failed
echo.
echo [2/4] Creating Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON% -m venv ".venv"
  if errorlevel 1 goto :failed
) else (
  echo Existing virtual environment found.
)
echo.
echo [3/4] Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :failed
echo.
echo [4/4] Installing frontend dependencies...
cd /d "%~dp0..\frontend"
call npm.cmd install --no-audit --no-fund
if errorlevel 1 goto :failed
cd /d "%~dp0.."
echo.
echo ===============================================
echo  SETUP COMPLETE!
echo  Next double-click 05_START_CAMPUSMIND.bat
 echo ===============================================
pause
exit /b 0
:failed
 echo.
echo  SETUP FAILED. Read the error messages above.
echo  For help see docs\WINDOWS_SETUP.md
pause
exit /b 1
