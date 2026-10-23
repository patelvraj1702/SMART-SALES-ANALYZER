@echo off
title Stop Smart Sales Analyzer
color 0C

echo ==============================================================
echo             STOPPING SMART SALES ANALYZER...
echo ==============================================================
echo.

echo Stopping Backend on port 8000...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":8000\>"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo   Terminated PID %%a (Backend)
)

echo Stopping Frontend on port 5173...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":5173\>"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo   Terminated PID %%a (Frontend)
)

echo.
echo ==============================================================
echo      Smart Sales Analyzer servers have been stopped.
echo ==============================================================
echo.
ping 127.0.0.1 -n 3 >nul
exit /b 0
