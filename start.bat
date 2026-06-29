@echo off
REM 2026 World Cup Prediction System - Startup Script
REM ================================================

SET "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo [2026 World Cup Prediction System]
echo ===================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python found

REM Check .env
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Created .env file
    )
)

REM Install Python dependencies
echo [Installing Python dependencies...]
pip install -r backend\requirements.txt --quiet --break-system-packages 2>nul
if errorlevel 1 (
    pip install -r backend\requirements.txt --quiet 2>nul
)
echo [OK] Python dependencies ready

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
echo [OK] Node.js found

REM Install frontend dependencies
if not exist "frontend\node_modules" (
    echo [Installing frontend dependencies...]
    cd frontend
    call npm install
    cd /d "%SCRIPT_DIR%"
)
echo [OK] Frontend dependencies ready

REM Start backend
echo.
echo [Starting backend on port 6100...]
start "WorldCup Backend" /min cmd /c "cd /d "%SCRIPT_DIR%backend" && python server.py && pause"

REM Wait for backend to be ready (health check loop)
echo [Waiting for backend to be ready...]
set BACKEND_READY=0
for /L %%i in (1,1,30) do (
    if %BACKEND_READY%==0 (
        curl -s -o nul -w "%%{http_code}" http://localhost:6100/api/status 2>nul | findstr "200" >nul 2>nul
        if not errorlevel 1 (
            set BACKEND_READY=1
            echo [OK] Backend is ready! (after %%i seconds)
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if %BACKEND_READY%==0 (
    echo [WARN] Backend not responding after 30s, but frontend will auto-retry...
)

REM Start frontend
echo.
echo [Starting frontend on port 6101...]
start "WorldCup Frontend" /min cmd /c "cd /d "%SCRIPT_DIR%frontend" && npx vite --port 6101 && pause"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   System is running!
echo   Frontend: http://localhost:6101
echo   Backend:  http://localhost:6100
echo   API Docs: http://localhost:6100/docs
echo ========================================
echo.

start http://localhost:6101

pause
