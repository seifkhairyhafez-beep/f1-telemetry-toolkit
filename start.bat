@echo off
title F1 25 Telemetry
cd /d "%~dp0"

echo ============================================
echo  F1 25 Telemetry Dashboard
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
python -c "import websockets" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting listener...
echo   UDP port:   20777
echo   Dashboard:  http://localhost:8766/dashboard
echo   Compare:    http://localhost:8766/compare
echo.
echo Press Ctrl+C to stop.
echo.

python listener.py

pause
