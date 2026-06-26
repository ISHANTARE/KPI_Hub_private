@echo off
REM KPI Agent - Setup & Run Script
REM This script installs dependencies and runs the Streamlit web app

echo.
echo ============================================
echo  KPI Hub
echo  Setup & Launch Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

echo [1/3] Python found: 
python --version
echo.

REM Install dependencies
echo [2/3] Installing dependencies...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Run Streamlit app in background and open browser
echo [3/3] Launching KPI Hub Dashboard...
echo.
echo Opening at http://localhost:8501
echo Press Ctrl+C in this window to stop the server
echo.

REM Start Scheduler in background
echo Starting Background Sync Scheduler...
start /B python integrations/scheduler.py

REM Start Streamlit in background
start "" python -m streamlit run web_app.py

REM Wait for server to start
timeout /t 3 /nobreak

REM Open browser once
start http://localhost:8501

pause
