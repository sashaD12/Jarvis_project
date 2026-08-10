@echo off
cd /d "%~dp0"
py -3.13 Start_Jarvis_Program.py
if errorlevel 1 (
    echo.
    echo Program exited with an error.
    pause
)
