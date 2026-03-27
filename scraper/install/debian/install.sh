#!/bin/bash
#
# Скрипт установки зависимостей для OzonAI Scraper на Debian
# Устанавливает: системные пакеты, Python, venv, scraper зависимости
# Настраивает: VNC, автозапуск скрапера
#
# Использует текущего пользователя (не создаёт нового)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPER_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "========================================"
echo "  OzonAI Scraper - Установка на Debian"
echo "========================================"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт от root (sudo ./install.sh)"
    exit 1
fi

# Получаем имя текущего пользователя
CURRENT_USER="$(whoami)"
CURRENT_UID="$(id -u)"
CURRENT_HOME="$(eval echo ~$CURRENT_USER)"

echo "👤 Текущий пользователь: $CURRENT_USER (UID: $CURRENT_UID)"
echo "📁 Домашняя директория: $CURRENT_HOME"
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}>>>${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}>>>${NC} $1"
}

log_error() {
    echo -e "${RED}>>>${NC} $1"
}

# ============================================
# 1. Обновление пакетов и установка зависимостей
# ============================================
log_info "Шаг 1: Обновление пакетов и установка системных зависимостей..."

apt-get update

# Зависимости для pyenv
apt-get install -y \
    curl \
    git \
    wget \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev

# Основные пакеты
apt-get install -y \
    firefox-esr \
    xclip \
    wmctrl \
    xvfb \
    x11vnc \
    xfce4 \
    xfce4-goodies \
    tightvncserver

log_info "Системные пакеты установлены."

# ============================================
# 1.5. Создание XDG_RUNTIME_DIR
# ============================================
# Создаём директорию для runtime-файлов (нужна для pyautogui, x11vnc)
mkdir -p /run/user/$CURRENT_UID
chmod 700 /run/user/$CURRENT_UID
log_info "XDG_RUNTIME_DIR создан: /run/user/$CURRENT_UID"

# ============================================
# 2. Установка Python 3.10 (готовая сборка)
# ============================================
log_info "Шаг 2: Установка Python 3.10..."

# Автоопределение архитектуры и загрузка
ARCH=$(uname -m)
PYTHON_VERSION="3.10.15"
PYTHON_BUILD="20241016"
PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_BUILD}/cpython-${PYTHON_VERSION}+${PYTHON_BUILD}-${ARCH}-unknown-linux-gnu-install_only.tar.gz"

log_info "Обнаружена архитектура: $ARCH"

if ! python3.10 --version &>/dev/null; then
    log_info "Загрузка готовой сборки Python $PYTHON_VERSION..."
    
    cd /tmp
    if ! wget -q --show-progress "$PYTHON_URL"; then
        log_error "❌ Архитектура $ARCH не поддерживается этим скриптом"
        log_error "   Ссылка: $PYTHON_URL"
        exit 1
    fi
    
    tar -xzf "cpython-${PYTHON_VERSION}+${PYTHON_BUILD}-${ARCH}-unknown-linux-gnu-install_only.tar.gz"
    mv python /opt/python3.10
    ln -sf /opt/python3.10/bin/python3.10 /usr/local/bin/python3.10
    ln -sf /opt/python3.10/bin/pip3.10 /usr/local/bin/pip3.10
    
    rm -rf /tmp/cpython-*
    
    log_info "Python 3.10 установлен в /opt/python3.10"
else
    log_info "Python 3.10 уже установлен"
fi

PYTHON3_VER=$(python3.10 --version 2>&1)
log_info "Установлен: $PYTHON3_VER"

# ============================================
# 3. Установка Python зависимостей
# ============================================
log_info "Шаг 3: Настройка Python окружения..."

VENV_DIR="$SCRAPER_DIR/.venv"

# Создание виртуального окружения
log_info "Создание виртуального окружения в $VENV_DIR..."
python3.10 -m venv "$VENV_DIR"

# Установка Python зависимостей
log_info "Установка Python зависимостей..."
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r "$SCRAPER_DIR/requirements.txt"

# ============================================
# 4. Настройка VNC
# ============================================
log_info "Шаг 4: Настройка VNC сервера..."

VNC_PASSWORD="${VNC_PASSWORD:-scraper123}"

# Установка пароля VNC
mkdir -p "$CURRENT_HOME/.vnc"
echo "$VNC_PASSWORD" | vncpasswd -f > "$CURRENT_HOME/.vnc/passwd"
chmod 600 "$CURRENT_HOME/.vnc/passwd"
chown -R "$CURRENT_USER:$CURRENT_USER" "$CURRENT_HOME/.vnc"

# Конфигурация VNC
cat > "$CURRENT_HOME/.vnc/xstartup" << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF

chmod +x "$CURRENT_HOME/.vnc/xstartup"
chown "$CURRENT_USER:$CURRENT_USER" "$CURRENT_HOME/.vnc/xstartup"

# ============================================
# 4.5. Настройка Firefox ESR
# ============================================
log_info "Настройка Firefox ESR..."

# Создаём профиль Firefox по умолчанию
FIREFOX_PROFILE="$CURRENT_HOME/.mozilla/firefox/default"
mkdir -p "$FIREFOX_PROFILE"

# Отключаем предупреждение Self-XSS в консоли разработчика
cat >> "$FIREFOX_PROFILE/user.js" << 'EOF'
// Отключение предупреждения Self-XSS
user_pref("devtools.selfxss.count", 100);
EOF

chown -R "$CURRENT_USER:$CURRENT_USER" "$CURRENT_HOME/.mozilla"

# ============================================
# 5. Настройка systemd сервиса
# ============================================
log_info "Шаг 5: Настройка systemd сервиса..."

cat > "/etc/systemd/system/ozon-scraper.service" << EOF
[Unit]
Description=OzonAI Scraper Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$SCRAPER_DIR
ExecStart=$SCRIPT_DIR/autostart.sh
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:1
Environment=XDG_RUNTIME_DIR=/run/user/$CURRENT_UID

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ozon-scraper.service

log_info "Systemd сервис настроен: ozon-scraper.service"

# ============================================
# 6. Настройка .env и авторизация
# ============================================
echo ""
echo "========================================"
echo "  Настройка подключения к бэкенду"
echo "========================================"
echo ""

read -p "Введите BASE_URL (по умолчанию http://localhost:8000): " INPUT_BASE_URL
BASE_URL="${INPUT_BASE_URL:-http://localhost:8000}"

cat > "$SCRAPER_DIR/.env" << EOF
# Платформа
PLATFORM=debian

# Бэкенд
BASE_URL=$BASE_URL

# Токен (заполняется после авторизации)
SESSION_TOKEN=

# Для Linux
DISPLAY=:1
XDG_RUNTIME_DIR=/run/user/$CURRENT_UID
EOF

chown "$CURRENT_USER:$CURRENT_USER" "$SCRAPER_DIR/.env"

log_info ".env создан: $SCRAPER_DIR/.env"

# ============================================
# Запуск авторизации
# ============================================
echo ""
echo "========================================"
echo "  Авторизация в системе"
echo "========================================"
echo ""
echo "Сейчас будет запущен скрапер для авторизации."
echo "Введите email и пароль от бэкенда."
echo "После успешной авторизации нажмите Ctrl+C для выхода."
echo ""
read -p "Нажмите Enter для продолжения..."

# Запускаем скрапер для авторизации (без VNC, только авторизация)
cd "$SCRAPER_DIR"
export DISPLAY=:1
export XDG_RUNTIME_DIR="/run/user/$CURRENT_UID"

.venv/bin/python main.py

# Пользователь нажмёт Ctrl+C после авторизации
echo ""
log_info "Авторизация завершена."
echo ""
echo "========================================"
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo "========================================"
echo ""
echo "� Запуск сервиса:"
echo "   systemctl start ozon-scraper.service"
echo ""
echo "📊 Статус:"
echo "   systemctl status ozon-scraper.service"
echo ""
echo "📝 Логи:"
echo "   journalctl -u ozon-scraper.service -f"
echo ""
echo "🔐 VNC пароль: $VNC_PASSWORD"
echo "   Подключение: localhost:5901 (или :1)"
echo ""
