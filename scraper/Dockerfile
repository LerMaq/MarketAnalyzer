FROM python:3.10-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENV DISPLAY=:99
ENV XDG_RUNTIME_DIR=/tmp/runtime-scraper
ENV MOZ_DISABLE_CONTENT_SANDBOX=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    xvfb \
    x11vnc \
    xclip \
    wmctrl \
    openbox \
    dbus-x11 \
    procps \
    curl \
    ca-certificates \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-color-emoji \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY core ./core
COPY docker ./docker

RUN chmod +x /app/docker/entrypoint.sh \
    && useradd -m -u 10001 scraper \
    && mkdir -p /tmp/runtime-scraper /tmp/firefox-profile \
    && chown -R scraper:scraper /app /tmp/runtime-scraper /tmp/firefox-profile

USER scraper

ENTRYPOINT ["/app/docker/entrypoint.sh"]