@echo off
chcp 65001 > nul
title RestoKZ Server & Bot
echo ========================================================
echo   RestoKZ — Система бронирования ресторанов Казахстана
echo ========================================================
echo.
echo [1/2] Освобождение порта 8080...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] Запуск сервера RestoKZ и Telegram-бота...
python -u bot.py
pause
