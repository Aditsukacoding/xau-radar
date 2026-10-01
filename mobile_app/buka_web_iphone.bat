@echo off
title XAU/USD Radar - iPhone Web Server
echo ========================================================
echo Membuka Trading Analytics untuk iPhone & Local Network
echo ========================================================
cd /d "%~dp0"
python server_iphone.py
pause
