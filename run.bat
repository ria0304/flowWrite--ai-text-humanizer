@echo off
cd /d "%~dp0"

echo Starting FlowWrite...

REM Activate virtual environment
call humanizer_env\Scripts\activate

REM FIX #13 — Only install packages if not already installed
REM Old: pip install ran every single launch (slow)
REM New: check if uvicorn exists first, install only if missing
python -c "import uvicorn" 2>nul || (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start FastAPI backend on port 8000
start "" cmd /k "call humanizer_env\Scripts\activate && python -m uvicorn main:app --reload --port 8000"

REM Start frontend HTTP server on port 3000
start "" cmd /k "call humanizer_env\Scripts\activate && python -m http.server 3000"

REM Wait for servers to start
timeout /t 3 >nul

REM Open browser
start http://localhost:3000/index.html

echo.
echo FlowWrite is running!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
