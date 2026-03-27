"""
Windows Browser Controller — Управление Chrome на Windows.

Окружение:
- Google Chrome
- pyperclip для буфера обмена
- pygetwindow для управления окнами
"""

import os
import re
import subprocess
import time
from typing import Dict, Any

import pyautogui
import pyperclip
import pygetwindow as gw

# Windows-специфичные импорты
try:
    import win32gui
    import win32con
    import win32com.client
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from scraper.browser_controller import BrowserController

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01


def force_activate_chrome() -> bool:
    """Активация окна Google Chrome."""
    if not WINDOWS_AVAILABLE:
        print("  ⚠️ Windows модули не доступны")
        return False

    def is_chrome_normal(window):
        return (
            "Google Chrome" in window.title and
            "Incognito" not in window.title and
            "Инкогнито" not in window.title
        )

    chrome_windows = [w for w in gw.getAllWindows() if is_chrome_normal(w)]

    if not chrome_windows:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        subprocess.Popen([chrome_path])
        time.sleep(5)
        chrome_windows = [w for w in gw.getAllWindows() if is_chrome_normal(w)]
        if not chrome_windows:
            return False

    win = chrome_windows[0]
    hwnd = win._hWnd

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys("^")

    try:
        win32gui.SetForegroundWindow(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        pyautogui.click(rect[0] + 150, rect[1] + 10)
    except Exception:
        pass

    time.sleep(0.5)
    pyautogui.press("f6")
    time.sleep(0.2)
    return True


def expand_comments_chrome() -> None:
    """Раскрытие комментариев через JS консоль Chrome."""
    print("  🛠 Раскрытие комментариев через JS...")

    pyautogui.hotkey("ctrl", "shift", "j")
    time.sleep(3)

    js_payload = (
        "(async()=>{const els=[...document.querySelectorAll('*')]"
        ".filter(el=>/комментар/i.test(el.innerText)&&el.children.length===0);"
        "let c=0;for(const e of els){if(c>=10)break;e.click();c++;"
        "await new Promise(r=>setTimeout(r,300));}})();"
    )

    pyperclip.copy(js_payload)
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.hotkey("f12")
    time.sleep(4)


class BrowserControllerImpl(BrowserController):
    """Реализация контроллера для Windows."""

    def __init__(self):
        self.browser_started = False

    def initialize(self) -> bool:
        """Проверка готовности Chrome."""
        try:
            # На Windows браузер обычно уже запущен
            print("  ✅ Chrome готов к работе.")
            self.browser_started = True
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации браузера: {e}")
            return False

    def scrape_product(self, ozon_id: str) -> Dict[str, Any]:
        """Скрапинг страницы товара."""
        print(f"  🔍 Скрапинг товара: {ozon_id}")

        if not force_activate_chrome():
            print("  ⚠️ Chrome не найден, пробуем продолжить...")

        pyautogui.press("alt")
        time.sleep(0.1)
        pyautogui.press("esc")
        time.sleep(0.2)

        pyautogui.hotkey("ctrl", "t")
        time.sleep(1.2)

        url = f"https://www.ozon.ru/product/{ozon_id}/"
        pyperclip.copy(url)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press("enter")

        print("  ⏳ Загрузка страницы (7 сек)...")
        time.sleep(7)

        print("  📜 Прокрутка к рекомендациям...")
        for _ in range(5):
            pyautogui.press("pgdn")
            time.sleep(0.4)

        print("  💤 Ожидание прогрузки (18 сек)...")
        time.sleep(18)

        print("  📜 Прокрутка к отзывам...")
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        pyperclip.copy("Вам помог")
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        for _ in range(50):
            pyautogui.press("enter")
            time.sleep(0.15)

        pyautogui.press("esc")
        time.sleep(0.5)

        # Подсчёт комментариев
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(1)
        current_text = pyperclip.paste().lower()
        found_matches = re.findall(r"комментари", current_text)
        comment_limit = min(len(found_matches), 10)
        print(f"  📝 Найдено веток для раскрытия: {comment_limit}")

        if comment_limit > 0:
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            pyperclip.copy("комментари")
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)

            for _ in range(comment_limit):
                pyautogui.press("enter")
                time.sleep(0.01)
                pyautogui.press("esc")
                time.sleep(0.01)
                pyautogui.press("enter")
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "f")
                time.sleep(0.01)

        expand_comments_chrome()

        print("  📸 Захват данных...")
        pyautogui.press("esc")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(1.5)

        raw_content = pyperclip.paste()

        pyautogui.hotkey("ctrl", "w")
        time.sleep(0.5)

        return {"raw_content": raw_content}

    def cleanup(self) -> None:
        """Очистка ресурсов."""
        print("  🧹 Очистка ресурсов...")
