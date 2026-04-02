@echo off
title Dadarzz Agent
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║    🧠 Dadarzz Agent is starting...          ║
echo ╚══════════════════════════════════════════════╝
echo.
echo Opening in your browser...
echo To stop: close this window or press Ctrl+C
echo.

REM Activate venv and start server
call .venv\Scripts\activate.bat
python main.py
pause
