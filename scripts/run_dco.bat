@echo off
REM Daily Chess Offline Launcher
REM This batch file runs the DCO application

echo Starting Daily Chess Offline...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the application
python app.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
