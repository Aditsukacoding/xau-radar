@echo off
title XAU/USD Radar - Web & Mobile Runner
echo ========================================================
echo       XAU/USD RADAR - INSTITUTIONAL ANALYTICS
echo ========================================================
echo Pastikan Backend sudah berjalan di http://127.0.0.1:8000
echo.
echo Pilih mode:
echo [1] Jalankan Server iPhone ^& PC (Release Cepat - Siap Pakai)
echo [2] Rebuild Web Bundle ^& Jalankan Server
echo [3] Flutter Debug Mode (Khusus Developer di PC Chrome)
echo.
set /p choice="Pilihan Anda [1/2/3] (Tekan Enter untuk [1]): "

if "%choice%"=="2" goto rebuild
if "%choice%"=="3" goto debug

:release
echo.
echo [INFO] Memulai server produksi untuk iPhone ^& PC...
python server_iphone.py 3000
goto end

:rebuild
echo.
echo [INFO] Mengompilasi ulang Flutter Web Release...
call flutter build web --release --no-web-resources-cdn
echo.
echo [INFO] Build selesai! Menjalankan server...
python server_iphone.py 3000
goto end

:debug
echo.
echo [INFO] Menjalankan Flutter Debug Mode di Chrome...
flutter run -d chrome --web-port=3000
goto end

:end
pause
