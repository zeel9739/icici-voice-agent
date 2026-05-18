@echo off
title ICICI - LiveKit Voice Agent
cd /d "%~dp0backend"
set PATH=C:\Users\Zeel\AppData\Local\Programs\Python\Python311;C:\Users\Zeel\AppData\Local\Programs\Python\Python311\Scripts;C:\Users\Zeel\AppData\Roaming\Python\Scripts;%PATH%
echo Starting LiveKit Voice Agent Worker...
poetry run python -m app.agent.worker start
pause
