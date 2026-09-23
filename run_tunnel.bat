@echo off
chcp 65001 > nul
title RestoKZ Public Tunnel
echo ========================================================
echo   RestoKZ — Публичный HTTPS туннель для Telegram WebApp
echo ========================================================
echo.
python tunnel.py
pause
