# OzonAI Scraper — Linux Edition

Скрапер Ozon для Linux с использованием PyAutoGUI и Firefox в VNC-среде.

## 📋 Требования

### Системные зависимости

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y firefox xclip wmctrl python3-pip python3-venv

# Для работы PyAutoGUI также понадобятся:
sudo apt install -y scrot python3-tk python3-dev
```

### Установка зависимостей Python

```bash
cd /path/to/ubuntu
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ Настройка

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Отредактируйте `.env`, указав правильный `BASE_URL`.

## 🚀 Запуск

```bash
source venv/bin/activate
python main.py
```

## 🔧 Важные замечания

### DISPLAY
Скрипт использует `DISPLAY=:1` для работы в VNC-сессии. Убедитесь, что VNC-сервер запущен на дисплее `:1`.

### Firefox
- Браузер запускается автоматически при старте скрипта
- Первый запуск может занять ~25 секунд на инициализацию
- Используйте флаг `--no-sandbox` для работы в ограниченных средах (proot, Docker)

### xclip
Обязательно установите `xclip` для работы буфера обмена:
```bash
sudo apt install xclip
```

### wmctrl
Нужен для активации окна Firefox:
```bash
sudo apt install wmctrl
```

## 🛠 Troubleshooting

### Проблемы с буфером обмена
Проверьте установку xclip:
```bash
echo "test" | xclip -selection clipboard
xclip -o -selection clipboard
```

### Ошибки PyAutoGUI
Убедитесь, что X-сервер запущен и переменная DISPLAY установлена корректно:
```bash
echo $DISPLAY  # Должно быть :1
```
