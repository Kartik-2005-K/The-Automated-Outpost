@echo off
title The Automated Outpost — Frontend
echo.
echo  ===================================================
echo   THE AUTOMATED OUTPOST — Frontend (Vite + React)
echo  ===================================================
echo.

REM Refresh PATH to pick up newly installed Node.js
set PATH=C:\Program Files\nodejs;%PATH%

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found.
    echo Please download and install Node.js from: https://nodejs.org/
    echo Then re-run this script.
    pause
    exit /b 1
)

echo [*] Node.js: 
node --version
echo [*] npm:
npm --version

echo.
echo [*] Installing dependencies (first time only)...
cd frontend
npm install

echo.
echo [*] Starting frontend on http://localhost:5173
echo [*] Make sure backend is running first! (start-backend.bat)
echo [*] Press Ctrl+C to stop
echo.
npm run dev
pause
