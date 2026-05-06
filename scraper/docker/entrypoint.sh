#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

DISPLAY_VALUE="${DISPLAY:-:99}"
SCREEN_WIDTH="${SCREEN_WIDTH:-1280}"
SCREEN_HEIGHT="${SCREEN_HEIGHT:-720}"
SCREEN_DEPTH="${SCREEN_DEPTH:-24}"

VNC_ENABLED="${VNC_ENABLED:-false}"
VNC_PORT="${VNC_PORT:-5901}"
VNC_PASSWORD="${VNC_PASSWORD:-}"

export DISPLAY="${DISPLAY_VALUE}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-scraper}"
export XAUTHORITY=/tmp/.docker.xauth

mkdir -p "${XDG_RUNTIME_DIR}"
chmod 700 "${XDG_RUNTIME_DIR}" || true
touch "$XAUTHORITY"

DISPLAY_NUM="${DISPLAY_VALUE#:}"

rm -f "/tmp/.X${DISPLAY_NUM}-lock"
rm -f "/tmp/.X11-unix/X${DISPLAY_NUM}"

log "Starting dbus session..."
if command -v dbus-launch >/dev/null 2>&1; then
  eval "$(dbus-launch --sh-syntax)"
  export DBUS_SESSION_BUS_ADDRESS
  export DBUS_SESSION_BUS_PID
fi

log "Starting Xvfb on ${DISPLAY_VALUE} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})..."
Xvfb "${DISPLAY_VALUE}" \
  -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" \
  -nolisten tcp \
  >/tmp/xvfb.log 2>&1 &

sleep 2

log "Checking X server..."
if ! xdpyinfo -display "${DISPLAY_VALUE}" >/tmp/xdpyinfo.log 2>&1; then
  log "Xvfb did not start correctly."
  cat /tmp/xvfb.log || true
  cat /tmp/xdpyinfo.log || true
  exit 1
fi

log "Starting openbox..."
openbox >/tmp/openbox.log 2>&1 &

sleep 1

if [ "${VNC_ENABLED}" = "true" ]; then
  if [ -z "${VNC_PASSWORD}" ]; then
    log "VNC_ENABLED=true, but VNC_PASSWORD is empty. Refusing to start unsafe VNC."
    exit 1
  fi

  VNC_PASSWORD_FILE="/tmp/x11vnc.pass"

  log "Preparing VNC password..."
  x11vnc -storepasswd "${VNC_PASSWORD}" "${VNC_PASSWORD_FILE}" >/dev/null 2>&1

  log "Starting x11vnc on port ${VNC_PORT}..."
  x11vnc \
    -display "${DISPLAY_VALUE}" \
    -forever \
    -shared \
    -rfbport "${VNC_PORT}" \
    -rfbauth "${VNC_PASSWORD_FILE}" \
    >/tmp/x11vnc.log 2>&1 &
else
  log "VNC disabled."
fi

log "Starting scraper..."
exec python -m core.main