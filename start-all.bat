@echo off
echo =============================================
echo   ICICI Prudential AMC - Voice Agent
echo =============================================
echo.
echo Starting all services...
echo.

start "FastAPI Backend" cmd /k "cd /d "%~dp0backend" && set PATH=C:\Users\Zeel\AppData\Local\Programs\Python\Python311;C:\Users\Zeel\AppData\Local\Programs\Python\Python311\Scripts;C:\Users\Zeel\AppData\Roaming\Python\Scripts;%PATH% && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 4 /nobreak >nul

start "LiveKit Agent" cmd /k "cd /d "%~dp0backend" && set PATH=C:\Users\Zeel\AppData\Local\Programs\Python\Python311;C:\Users\Zeel\AppData\Local\Programs\Python\Python311\Scripts;C:\Users\Zeel\AppData\Roaming\Python\Scripts;%PATH% && poetry run python -m app.agent.worker start"

timeout /t 2 /nobreak >nul

start "Frontend UI" cmd /k "cd /d "%~dp0frontend" && set PATH=C:\Program Files\nodejs;%PATH% && npm run dev"

echo.
echo All services started in separate windows.
echo.
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo   Frontend:      http://localhost:5173
echo.
echo Press any key to close this window...
pause >nul
