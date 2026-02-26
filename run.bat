@echo off
title Hibbs Institute - Prep Tool
echo.
echo ============================================================
echo   Hibbs Institute - Interview, Presentation ^& Pitch Prep
echo ============================================================
echo.

:: Check for Python
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.8+ from python.org
    pause
    exit /b 1
)

:: Install Flask if needed
py -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo Installing Flask...
    py -m pip install flask --quiet
)

echo Starting app at http://localhost:5050
echo Press Ctrl+C to stop.
echo.

:: Open browser after short delay
start "" /min cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5050"

:: Run the app
py app.py
pause
