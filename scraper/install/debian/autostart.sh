#!/bin/bash
#
# Скрипт автозапуска для OzonAI Scraper на Debian
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPER_DIR="$SCRIPT_DIR/../.."

# Читаем DISPLAY из .env
if [ -f "$SCRAPER_DIR/.env" ]; then
    VNC_DISPLAY=$(grep "^DISPLAY=" "$SCRAPER_DIR/.env" | cut -d'=' -f2)
fi
VNC_DISPLAY="${VNC_DISPLAY:-:1}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ============================================
# 1. Запуск VNC сервера
# ============================================
log "Проверка VNC сервера..."

# Очищаем lock файлы
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1

log "🚀 Запуск VNC сервера на дисплее $VNC_DISPLAY..."
vncserver $VNC_DISPLAY -geometry 1280x720 -depth 24
log "✅ VNC сервер запущен"

sleep 3

# ============================================
# 2. Запуск скрапера
# ============================================
log "Запуск скрапера..."

cd "$SCRAPER_DIR" || exit 1

export DISPLAY=$VNC_DISPLAY
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

# Запуск в цикле
while true; do
    log "🚀 Запуск main.py..."
    "$SCRAPER_DIR/.venv/bin/python" "$SCRAPER_DIR/main.py"
    
    log "⚠️ Скрапер завершился. Перезапуск через 10 секунд..."
    sleep 10
done
