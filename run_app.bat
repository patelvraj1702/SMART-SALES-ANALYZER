@echo off
setlocal enabledelayedexpansion
title Smart Sales Analyzer Launcher
color 0B

echo ==============================================================
echo             STARTING SMART SALES ANALYZER...
echo ==============================================================
echo.

:: Ensure current working directory is the project root
cd /d "%~dp0"

:: -----------------------------------------------------------------
:: 1. CHECK MONGODB SERVICE
:: -----------------------------------------------------------------
echo [1/4] Checking MongoDB service...
sc query MongoDB | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] MongoDB is running.
) else (
    echo     [INFO] MongoDB is not running. Attempting to start MongoDB...
    net start MongoDB >nul 2>&1
    sc query MongoDB | findstr /i "RUNNING" >nul 2>&1
    if %errorlevel% equ 0 (
        echo     [OK] MongoDB started successfully.
    ) else (
        echo     [WARNING] Could not start MongoDB service automatically.
        echo     If MongoDB is not running, please ensure MongoDB is active.
    )
)
echo.

:: -----------------------------------------------------------------
:: 2. DETECT PYTHON ENVIRONMENT
:: -----------------------------------------------------------------
echo [2/4] Detecting Python installation...
set "PYTHON_CMD="

:: Check py launcher with 3.14
py -3.14 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3.14"
    goto :python_found
)

:: Check general py launcher
py -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :python_found
)

:: Check direct LocalPrograms path
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python314\python.exe""
    goto :python_found
)

:: Check system python command
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

:python_found
if not defined PYTHON_CMD (
    echo [ERROR] Python was not found on your system!
    echo Please install Python 3.10+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON_CMD% -c "import sys; print(sys.version.split()[0])"') do set "PY_VER=%%v"
echo     [OK] Using Python: %PYTHON_CMD% (version %PY_VER%)
echo.

:: -----------------------------------------------------------------
:: 3. DETECT NODE.JS & NPM
:: -----------------------------------------------------------------
echo [3/4] Detecting Node.js and npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm was not found in your system PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%n in ('node -v') do set "NODE_VER=%%n"
for /f "tokens=*" %%m in ('npm -v') do set "NPM_VER=%%m"
echo     [OK] Node.js %NODE_VER% and npm %NPM_VER% detected.
echo.

:: -----------------------------------------------------------------
:: 4. CHECK PRE-REQUISITES (ENV FILES & PORT CONFLICTS)
:: -----------------------------------------------------------------
echo [4/4] Preparing environment...

:: Ensure backend .env exists
if not exist "backend\.env" (
    if exist ".env.example" (
        echo     [INFO] Creating backend\.env from .env.example...
        copy ".env.example" "backend\.env" >nul
    )
)

:: Ensure frontend .env exists
if not exist "frontend\.env" (
    echo VITE_API_BASE=http://localhost:8000 > "frontend\.env"
)

:: Clean up old stuck processes on ports 8000 or 5173 if any
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":8000\>"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":5173\>"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: -----------------------------------------------------------------
:: 5. LAUNCH BACKEND & FRONTEND SERVERS
:: -----------------------------------------------------------------
echo     Starting FastAPI backend server on port 8000...
start "Smart Sales Analyzer - Backend API (Port 8000)" cmd /k "title Backend API (Port 8000) && cd /d "%~dp0backend" && %PYTHON_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo     Starting React/Vite frontend server on port 5173...
start "Smart Sales Analyzer - Frontend UI (Port 5173)" cmd /k "title Frontend UI (Port 5173) && cd /d "%~dp0frontend" && npm run dev"

:: Give servers a few seconds to spin up reliably
echo.
echo Waiting for servers to initialize...
ping 127.0.0.1 -n 4 >nul

:: Open browser automatically
start http://localhost:5173

color 0A
echo.
echo ==============================================================
echo                 SMART SALES ANALYZER IS LIVE!                
echo ==============================================================
echo.
echo   Frontend Application :  http://localhost:5173
echo   Backend REST API     :  http://127.0.0.1:8000
echo   API Documentation    :  http://127.0.0.1:8000/docs
echo   MongoDB Connection   :  mongodb://localhost:27017
echo.
echo ==============================================================
echo   The web application has been opened in your default browser.
echo   Separate console windows for Backend and Frontend are open
echo   in your taskbar to stream logs in real time.
echo.
echo   OPTIONS:
echo     [S] Stop all servers and exit
echo     [Any other key] Keep servers running and close this window
echo ==============================================================
echo.

set /p USER_CHOICE="Enter your choice: "
if /i "%USER_CHOICE%"=="S" (
    echo.
    echo Stopping servers...
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":8000\>"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /r ":5173\>"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    echo Servers stopped.
    ping 127.0.0.1 -n 3 >nul
    exit /b 0
)

exit /b 0
