"""
Debian Browser Controller — Управление Firefox ESR на Debian.

Окружение:
- Xvfb :1 (1280x720x24)
- firefox-esr
- xclip для буфера обмена
- wmctrl для управления окнами
- xfce4, tightvncserver для удаленного доступа

Оптимизированные тайминги для ускорения скрапинга:
- 5 сек на загрузку страницы
- 4 pgdn + 5 сек ожидание
- 8 pgdn с интервалом 1.4 сек
- Быстрое раскрытие комментариев
"""

import os
import subprocess
import time
from typing import Dict, Any

# Переменные окружения (можно переопределить в .env)
os.environ["DISPLAY"] = os.getenv("DISPLAY", ":1")
if os.getuid() != 0:
    os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

import pyautogui

from scraper.browser_controller import BrowserController

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01


def set_clipboard(text: str) -> None:
    """Запись в буфер обмена через xclip."""
    try:
        process = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        process.communicate(input=text.encode("utf-8"))
    except Exception as e:
        print(f"⚠️ Ошибка записи в clipboard: {e}")


def get_clipboard() -> str:
    """Чтение из буфера обмена через xclip."""
    try:
        result = subprocess.check_output(
            ["xclip", "-o", "-selection", "clipboard"],
            timeout=5
        )
        return result.decode("utf-8")
    except Exception as e:
        print(f"⚠️ Ошибка чтения из clipboard: {e}")
        return ""


def force_activate_firefox() -> bool:
    """Активация окна Firefox ESR через wmctrl."""
    try:
        result = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        firefox_windows = [
            line for line in result.stdout.split("\n")
            if "firefox" in line.lower() or "Firefox" in line
        ]

        if firefox_windows:
            win_id = firefox_windows[0].split()[0]
            subprocess.run(["wmctrl", "-i", "-a", win_id], timeout=5)
            time.sleep(0.3)
            return True
        return False
    except Exception as e:
        print(f"⚠️ Не удалось активировать Firefox: {e}")
        return False


def expand_comments_js() -> None:
    """Раскрытие комментариев через JS консоль Firefox."""
    print("  🛠 Раскрытие комментариев через JS...")

    # Открываем консоль разработчика (требуется 2-4 сек на открытие)
    pyautogui.hotkey("ctrl", "shift", "k")
    time.sleep(3)

    js_payload = (
        "(async()=>{const els=[...document.querySelectorAll('*')]"
        ".filter(el=>/комментар/i.test(el.innerText)&&el.children.length===0);"
        "let c=0;for(const e of els){if(c>=10)break;e.click();c++;"
        "await new Promise(r=>setTimeout(r,300));}})();"
    )

    set_clipboard(js_payload)
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.hotkey("f12")
    time.sleep(3)


class BrowserControllerImpl(BrowserController):
    """Реализация контроллера для Debian."""

    def __init__(self):
        self.browser_started = False

    def initialize(self) -> bool:
        """Запуск Firefox ESR."""
        try:
            result = subprocess.run(
                ["pgrep", "-x", "firefox-esr"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print("  ✅ Firefox ESR уже запущен.")
                self.browser_started = True
                return True

            print("  🌐 Запуск Firefox ESR (ожидание 35 секунд)...")
            subprocess.Popen(
                [
                    "firefox-esr",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-software-webgl",
                    "--disable-dev-shm-usage",
                    "--width=1280",
                    "--height=720",
                    "about:blank"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(35)
            self.browser_started = True
            print("  ✅ Браузер готов.")
            return True

        except Exception as e:
            print(f"❌ Ошибка инициализации браузера: {e}")
            return False

    def scrape_product(self, ozon_id: str) -> Dict[str, Any]:
        """Скрапинг страницы товара (оптимизированный, ~35-40 сек)."""
        print(f"  🔍 Скрапинг товара: {ozon_id}")

        # Активация Firefox
        if not force_activate_firefox():
            print("  ⚠️ Firefox не найден, пробуем продолжить...")

        # Новая вкладка
        pyautogui.hotkey("ctrl", "t")
        time.sleep(1)

        # Переход по URL
        url = f"https://www.ozon.ru/product/{ozon_id}/"
        set_clipboard(url)
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")

        # 1. Первичная загрузка страницы (5 сек)
        print("  ⏳ Загрузка страницы (5 сек)...")
        time.sleep(5)
        # = 6.6

        # 2. Прокрутка к рекомендациям (3-4 pgdn)
        print("  📜 Прокрутка к рекомендациям...")
        for _ in range(4):
            pyautogui.press("pagedown")
            time.sleep(0.3)

        # = 7.8

        # 3. Ожидание прогрузки (5 сек)
        print("  💤 Ожидание прогрузки (5 сек)...")
        time.sleep(5)

        # = 12.8

        # 4. Прокрутка к отзывам (8 pgdn с интервалом 1.4 сек)
        print("  📜 Прокрутка к отзывам...")
        for _ in range(8):
            pyautogui.press("pagedown")
            time.sleep(1.4)

        # = 24

        # 5. Поиск блока отзывов
        print("  🔎 Поиск блока отзывов...")
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        set_clipboard("Вам помог")
        time.sleep(0.5)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        # = 25.5

        # Поиск по странице (50 итераций)
        for _ in range(50):
            pyautogui.press("enter")
            time.sleep(0.3)

        # = 40.5

        pyautogui.press("esc")
        time.sleep(1)

        # = 41.5

        # 6. Раскрытие комментариев
        expand_comments_js() # 7.5 секунд

        # = 49

        # 7. Захват содержимого
        print("  📸 Захват данных...")
        pyautogui.hotkey("ctrl", "a")
        time.sleep(1)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(2)

        # = 52

        raw_content = get_clipboard()

        # Закрытие вкладки
        pyautogui.hotkey("ctrl", "w")
        time.sleep(1)

        # = 53

        return {"raw_content": raw_content}

    def cleanup(self) -> None:
        """Очистка ресурсов."""
        print("  🧹 Очистка ресурсов...")
        # Firefox не закрываем, он может понадобиться для следующего запуска
