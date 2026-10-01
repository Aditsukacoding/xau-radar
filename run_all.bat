@echo off
title XAUUSD Radar - System Launcher
echo ===================================================
echo   Memulai Trading Analytics System (XAUUSD Radar)
echo ===================================================
echo.
echo [1/2] Menjalankan Backend Server (FastAPI Port 8000)...
start "Trading Backend Server" cmd /c "%~dp0run_backend.bat"

echo [2/2] Menunggu backend siap (3 detik)...
timeout /t 3 /nobreak >nul

echo [3/3] Menjalankan Flutter Web App (Chrome Port 3000)...
start "Trading Flutter App" cmd /c "%~dp0run_app.bat"

echo.
echo ===================================================
echo   Semua layanan berhasil dijalankan!
echo   - Backend API Docs : http://127.0.0.1:8000/docs
echo   - Web App (Chrome) : http://localhost:3000
echo ===================================================
echo Jendela ini dapat ditutup.
pause
