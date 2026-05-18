@echo off
title ICICI - Frontend (Vite)
cd /d "%~dp0frontend"
set PATH=C:\Program Files\nodejs;%PATH%
echo Starting Frontend on http://localhost:5173 ...
npm run dev
pause
