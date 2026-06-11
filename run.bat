@echo off
setlocal
cd /d "%~dp0"
title Local Data Masking Tool

if not exist ".venv\Scripts\python.exe" (
    echo The app is not set up yet. Starting setup...
    call setup.bat
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" "app.py"
if errorlevel 1 (
    echo.
    echo The app could not start. Review the message above or startup-error.log.
    pause
    exit /b 1
)
