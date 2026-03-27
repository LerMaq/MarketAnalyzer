# OzonAI Scraper - Установка на Windows
# PowerShell скрипт для настройки окружения
# Для обычной Windows (не WSL)

param(
    [string]$VncPassword = "scraper123"
)

$ErrorActionPreference = "Stop"

Write-Host '========================================'
Write-Host '  OzonAI Scraper - Установка на Windows'
Write-Host '========================================'
Write-Host ''

# Получаем путь к скрипту и проекту
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScraperDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "Путь к скраперу: $ScraperDir"
Write-Host ''

# ============================================
# 1. Проверка Python
# ============================================
Write-Host '>>> Шаг 1: Проверка Python...' -ForegroundColor Green

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  $pythonVersion"
} catch {
    Write-Host '  Python не найден!' -ForegroundColor Red
    Write-Host '  Установите Python 3.8+ с https://www.python.org/downloads/'
    Write-Host "  При установке отметьте 'Add Python to PATH'"
    exit 1
}

# ============================================
# 2. Создание виртуального окружения
# ============================================
Write-Host '>>> Шаг 2: Создание виртуального окружения...' -ForegroundColor Green

$VenvDir = Join-Path $ScraperDir '.venv'

if (Test-Path $VenvDir) {
    Write-Host '  Виртуальное окружение уже существует'
} else {
    python -m venv $VenvDir
    Write-Host "  Виртуальное окружение создано: $VenvDir"
}

# ============================================
# 3. Установка зависимостей
# ============================================
Write-Host '>>> Шаг 3: Установка Python зависимостей...' -ForegroundColor Green

$PipPath = Join-Path $VenvDir 'Scripts\pip.exe'

& $PipPath install --upgrade pip
& $PipPath install -r (Join-Path $ScraperDir 'requirements.txt')

Write-Host '  Зависимости установлены'

# ============================================
# 4. Настройка .env
# ============================================
Write-Host '>>> Шаг 4: Настройка .env...' -ForegroundColor Green

$EnvPath = Join-Path $ScraperDir '.env'

Write-Host '  Настройка подключения к бэкенду'
$BaseURL = Read-Host '  Введите BASE_URL (по умолчанию http://localhost:8000)'
if ([string]::IsNullOrWhiteSpace($BaseURL)) {
    $BaseURL = 'http://localhost:8000'
}

$EnvContent = @"
# Платформа
PLATFORM=windows

# Бэкенд
BASE_URL=$BaseURL

# Токен (заполняется после авторизации)
SESSION_TOKEN=
"@

Set-Content -Path $EnvPath -Value $EnvContent -Encoding UTF8
Write-Host '  .env создан'

# ============================================
# Завершение
# ============================================
Write-Host ''
Write-Host '========================================'
Write-Host '  Установка завершена!' -ForegroundColor Green
Write-Host '========================================'
Write-Host ''

$RunScraper = Read-Host 'Запустить скрапер прямо сейчас? (Y/N)'
if ($RunScraper -eq 'Y' -or $RunScraper -eq 'y') {
    Write-Host ''
    Write-Host '>>> Запуск скрапера...' -ForegroundColor Green
    Write-Host ''
    Set-Location $ScraperDir
    & ".\.venv\Scripts\python.exe" "main.py"
}
