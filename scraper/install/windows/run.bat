@echo off
REM OzonAI Scraper - Быстрый запуск на Windows
REM Обёртка над PowerShell скриптом

setlocal enabledelayedexpansion

REM Получаем путь к скрипту
set "SCRIPT_DIR=%~dp0"
set "SCRAPER_DIR=%SCRIPT_DIR%..\.."

REM Активация venv и запуск
cd /d "%SCRAPER_DIR%"
call .venv\Scripts\activate.bat
python main.py

pause
