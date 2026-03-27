# OzonAI Scraper

Скрапер Ozon.ru с поддержкой нескольких платформ (Debian, Ubuntu, Windows).

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│              main.py (общая логика)                 │
│  • Авторизация на бэкенде                           │
│  • Получение задач                                  │
│  • Обработка raw_content                            │
│  • Отправка результатов                             │
└─────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          │               │               │               │
          ▼               ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
   │   Debian   │  │   Ubuntu   │  │  Windows   │  │  ...       │
   │ controller │  │ controller │  │ controller │  │            │
   └────────────┘  └────────────┘  └────────────┘  └────────────┘
```

## Быстрый старт

### Debian (автоматическая установка)

```bash
cd /root/MarketAnalyzer/scraper/install/debian
sudo ./install.sh
```

Скрипт автоматически:
- Определит архитектуру (x86_64 / aarch64)
- Установит Python 3.10 (готовая сборка)
- Установит системные зависимости (firefox-esr, xclip, wmctrl, xvfb, tightvncserver, xfce4)
- Настроит VNC сервер (пароль: `scraper123`)
- Создаст виртуальное окружение и установит зависимости
- Настроит systemd сервис
- Запросит BASE_URL и проведёт авторизацию

**После установки:**
```bash
# Запуск сервиса
systemctl start ozon-scraper.service

# Просмотр статуса
systemctl status ozon-scraper.service

# Логи в реальном времени
journalctl -u ozon-scraper.service -f

# Остановка
systemctl stop ozon-scraper.service
```

**VNC подключение:** `localhost:5901` (дисплей :1)

### Ubuntu

```bash
# 1. Системные зависимости
sudo apt install firefox-esr xclip wmctrl python3-tk

# 2. Xvfb (опционально)
sudo apt install xvfb
Xvfb :1 -screen 0 1280x720x24 &
export DISPLAY=:1

# 3. Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Запуск
source venv/bin/activate
python main.py
```

### Windows

**Автоматическая установка:**
```powershell
cd scraper/install/windows
.\install.ps1
```

**Запуск:**
```cmd
cd scraper\install\windows
.\run.bat
```

## Настройка .env

```ini
# Платформа
PLATFORM=debian          # или ubuntu, windows

# Бэкенд
BASE_URL=http://localhost:8000

# Токен (заполняется после авторизации)
SESSION_TOKEN=

# Для Linux
DISPLAY=:1
XDG_RUNTIME_DIR=/run/user/1000
```

## Структура проекта

```
scraper/
├── main.py                     # Главная программа
├── browser_controller.py       # Абстрактный интерфейс
├── .env                        # Переменные окружения
├── requirements.txt            # Зависимости
├── venv/                       # Виртуальное окружение
│
├── install/                    # Скрипты установки
│   ├── debian/
│   │   ├── install.sh          # Автоустановка на Debian
│   │   ├── autostart.sh        # Автозапуск (VNC + скрапер)
│   │   └── README.md
│   └── windows/
│       ├── install.ps1         # Установка на Windows
│       ├── run.bat             # Быстрый запуск
│       └── README.md
│
└── platform/
    ├── debian/
    │   ├── controller.py       # Firefox ESR + VNC :1 + xclip
    │   └── __init__.py
    ├── ubuntu/
    │   ├── controller.py       # Firefox ESR + xclip
    │   └── __init__.py
    └── windows/
        ├── controller.py       # Chrome + pyperclip + pygetwindow
        └── __init__.py
```

## Добавление новой платформы

1. Создайте `platform/<name>/__init__.py`
2. Создайте `platform/<name>/controller.py`:

```python
from scraper.browser_controller import BrowserController

class BrowserControllerImpl(BrowserController):
    def initialize(self) -> bool:
        # Запуск браузера
        pass

    def scrape_product(self, ozon_id: str) -> dict:
        # Скрапинг страницы
        pass
    
    def cleanup(self) -> None:
        # Очистка ресурсов
        pass
```

3. Обновите `get_browser_controller()` в `main.py`:

```python
elif PLATFORM == "newplatform":
    from scraper.platform.newplatform.controller import BrowserControllerImpl
```

## Тайминги скрапинга (оптимизированные)

Время скрапинга одной страницы: **~35-40 секунд**

```
1. Загрузка страницы          — 5 сек
2. Прокрутка к рекомендациям  — 1.2 сек (4 pgdn)
3. Ожидание прогрузки         — 5 сек
4. Прокрутка к отзывам        — 11.2 сек (8 pgdn × 1.4 сек)
5. Поиск блока отзывов        — 16 сек (50 итераций)
6. Раскрытие комментариев     — 7.5 сек (JS через консоль)
7. Захват данных              — 3 сек
───────────────────────────────────────
Итого:                        ~53 сек
```

## Особенности

### Debian
- VNC сервер :1 (tightvncserver + xfce4)
- Firefox ESR
- wmctrl для управления окнами
- Автозапуск через systemd

### Ubuntu
- Физический дисплей или Xvfb :1
- Firefox ESR
- wmctrl для управления окнами

### Windows
- Google Chrome
- pywin32 для управления окнами
- pyperclip для буфера обмена
