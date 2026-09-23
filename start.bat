@echo off
chcp 65001 > nul
title RestoKZ Server & Bot
echo ========================================================
echo   RestoKZ — Система бронирования ресторанов Казахстана
echo ========================================================
echo.
echo [1/3] Освобождение портов и старых процессов...
taskkill /F /IM node.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/3] Запуск публичного HTTPS туннеля...
start "RestoKZ Tunnel" /min cmd /c "python tunnel.py"

echo [3/3] Запуск локального сервера и Telegram-бота...
python -u bot.py
pause
