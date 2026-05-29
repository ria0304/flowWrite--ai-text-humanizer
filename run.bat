@echo off
cd /d "%~dp0"
call humanizer_env\Scripts\activate
pip install python-multipart python-docx pdfplumber
start "" cmd /k "call humanizer_env\Scripts\activate && python -m uvicorn main:app --reload --port 8000"
start "" cmd /k "call humanizer_env\Scripts\activate && python -m http.server 3000"
timeout /t 3 >nul
start http://localhost:3000/index.html
