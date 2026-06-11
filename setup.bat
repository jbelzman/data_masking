@echo off
setlocal
cd /d "%~dp0"
title Local Data Masking Tool Setup

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo.
    echo Python 3.10 or newer was not found.
    echo Install Python from https://www.python.org/downloads/windows/
    echo During installation, enable "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating the private Python environment...
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 goto :failed
)

echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto :failed

echo.
echo Setup complete. Double-click run.bat to open the app.
pause
exit /b 0

:failed
echo.
echo Setup failed. Review the messages above.
pause
exit /b 1
