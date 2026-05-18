@echo off
title ICICI - FastAPI Backend
cd /d "%~dp0backend"
set PATH=C:\Users\Zeel\AppData\Local\Programs\Python\Python311;C:\Users\Zeel\AppData\Local\Programs\Python\Python311\Scripts;C:\Users\Zeel\AppData\Roaming\Python\Scripts;%PATH%
echo Starting FastAPI on http://localhost:8000 ...
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
