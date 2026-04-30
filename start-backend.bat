@echo off
title The Automated Outpost — Backend Server
echo.
echo  ===================================================
echo   THE AUTOMATED OUTPOST — AI Brain (FastAPI)
echo  ===================================================
echo.

REM Try to find Python
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3
    goto :run
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :run
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :run
)

echo ERROR: Python not found. Please install Python 3.10+ from https://python.org
pause
exit /b 1

:run
echo [*] Using Python: %PYTHON_CMD%
echo [*] Installing/verifying dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet

echo.
echo [*] Starting backend on http://localhost:8000
echo [*] API docs: http://localhost:8000/docs
echo [*] Press Ctrl+C to stop
echo.
%PYTHON_CMD% -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
pause
