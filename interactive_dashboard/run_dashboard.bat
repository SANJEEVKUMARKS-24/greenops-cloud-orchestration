@echo off
title GreenOps Cloud Orchestrator Dashboard
cd /d "%~dp0\.."
echo ============================================================
echo   Starting GreenOps Interactive Cloud Dashboard...
echo ============================================================
call .\greenops_env\Scripts\activate.bat
python interactive_dashboard\server.py --port 8080
pause
