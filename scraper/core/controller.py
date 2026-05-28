from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

from core.browser_controller import BrowserController
from core.config import settings


os.environ["DISPLAY"] = settings.display
os.environ.setdefault("XDG_RUNTIME_DIR", "/tmp/runtime-scraper")

import pyautogui


pyautogui.FAILSAFE = True
pyautogui.PAUSE = settings.pyautogui_pause_sec


def log(message: str) -> None:
    print(message, flush=True)


def set_clipboard(text: str) -> None:
    """Запись текста в clipboard через xclip."""
    try:
        process = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.communicate(input=text.encode("utf-8"))
    except Exception as exc:
        log(f"⚠️ Ошибка записи в clipboard: {exc}")


def get_clipboard() -> str:
    """Чтение текста из clipboard через xclip."""
    try:
        result = subprocess.check_output(
            ["xclip", "-o", "-selection", "clipboard"],
            timeout=10,
        )
        return result.decode("utf-8", errors="replace")
    except Exception as exc:
        log(f"⚠️ Ошибка чтения из clipboard: {exc}")
        return ""


def force_activate_firefox() -> bool:
    """Активация окна Firefox через wmctrl."""
    try:
        result = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        firefox_windows = [
            line
            for line in result.stdout.splitlines()
            if "firefox" in line.lower()
        ]

        if not firefox_windows:
            return False

        win_id = firefox_windows[0].split()[0]
        subprocess.run(["wmctrl", "-i", "-a", win_id], timeout=5)
        time.sleep(settings.window_activate_wait_sec)
        return True

    except Exception as exc:
        log(f"⚠️ Не удалось активировать Firefox: {exc}")
        return False


def prepare_firefox_profile() -> None:
    """
    Готовим отдельный профиль Firefox.
    Это нужно, чтобы:
    - отключить первое приветствие;
    - отключить Self-XSS предупреждение в devtools console;
    - уменьшить количество всплывающих окон.
    """
    profile_dir = Path(settings.firefox_profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    user_js = profile_dir / "user.js"
    user_js.write_text(
        """
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage", "about:blank");
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.aboutConfig.showWarning", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("devtools.selfxss.count", 100);
user_pref("devtools.chrome.enabled", true);
user_pref("devtools.debugger.remote-enabled", true);
""".strip()
        + "\n",
        encoding="utf-8",
    )


def expand_comments_js(review_count: int) -> None:
    """Раскрытие комментариев через JS-консоль Firefox."""
    limit = settings.comments_click_limit_for(review_count)
    delay_ms = int(settings.comments_click_interval_sec * 1000)

    log(f"  🛠 Раскрытие комментариев через JS, limit={limit}...")

    if not force_activate_firefox():
        log("  ⚠️ Firefox не найден через wmctrl, пробуем открыть devtools всё равно...")

    pyautogui.hotkey("ctrl", "shift", "k")
    time.sleep(settings.devtools_open_wait_sec)

    js_payload = (
        "(async()=>{"
        "const els=[...document.querySelectorAll('*')]"
        ".filter(el=>/комментар/i.test(el.innerText||'')&&el.children.length===0);"
        f"let c=0;for(const e of els){{if(c>={limit})break;e.click();c++;"
        f"await new Promise(r=>setTimeout(r,{delay_ms}));}}"
        "})();"
    )

    set_clipboard(js_payload)
    time.sleep(settings.clipboard_settle_wait_sec)

    pyautogui.hotkey("ctrl", "v")
    time.sleep(settings.devtools_after_paste_wait_sec)

    pyautogui.press("enter")
    time.sleep(settings.devtools_after_enter_wait_sec)

    pyautogui.hotkey("f12")
    time.sleep(settings.devtools_close_wait_sec)


class BrowserControllerImpl(BrowserController):
    """
    Docker/Xvfb Firefox controller.

    Официальная среда:
    - Docker;
    - Xvfb;
    - Firefox ESR;
    - xclip;
    - wmctrl;
    - openbox;
    - optional x11vnc.
    """

    def __init__(self) -> None:
        self.browser_started = False

    def initialize(self) -> bool:
        try:
            prepare_firefox_profile()

            result = subprocess.run(
                ["pgrep", "-x", settings.firefox_bin],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                log("  ✅ Firefox уже запущен.")
                self.browser_started = True
                return True

            log(f"  🌐 Запуск Firefox ({settings.firefox_bin}), ожидание {settings.browser_startup_wait_sec} сек...")

            env = os.environ.copy()
            env["DISPLAY"] = settings.display
            env["XDG_RUNTIME_DIR"] = os.getenv("XDG_RUNTIME_DIR", "/tmp/runtime-scraper")

            subprocess.Popen(
                [
                    settings.firefox_bin,
                    "--no-remote",
                    "--profile",
                    settings.firefox_profile_dir,
                    "--width",
                    str(settings.screen_width),
                    "--height",
                    str(settings.screen_height),
                    "about:blank",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )

            time.sleep(settings.browser_startup_wait_sec)

            self.browser_started = True
            log("  ✅ Браузер готов.")
            return True

        except Exception as exc:
            log(f"❌ Ошибка инициализации браузера: {exc}")
            return False

    def scrape_product(self, ozon_id: int | str, review_count: int) -> dict[str, Any]:
        review_count = max(1, int(review_count))

        reviews_pagedown_count = settings.reviews_pagedown_count
        find_iterations = settings.find_iterations_for(review_count)

        log(f"  🔍 Скрапинг товара: {ozon_id}")
        log(f"  🧾 Нужно отзывов: {review_count}")
        log(f"  ⚙️ reviews_pagedown_count={reviews_pagedown_count}, find_iterations={find_iterations}")

        if not force_activate_firefox():
            log("  ⚠️ Firefox не найден через wmctrl, пробуем продолжить...")

        # Новая вкладка
        pyautogui.hotkey("ctrl", "t")
        time.sleep(settings.new_tab_wait_sec)

        # Переход по URL
        url = f"https://www.ozon.ru/product/{ozon_id}/"
        set_clipboard(url)
        time.sleep(settings.url_paste_wait_sec)

        pyautogui.hotkey("ctrl", "v")
        time.sleep(settings.url_paste_wait_sec)

        pyautogui.press("enter")

        # Первичная загрузка
        log(f"  ⏳ Первичная загрузка страницы ({settings.page_initial_load_wait_sec} сек)...")
        time.sleep(settings.page_initial_load_wait_sec)

        # Прокрутка к рекомендациям
        log("  📜 Прокрутка к рекомендациям...")
        for _ in range(settings.recommendations_pagedown_count):
            pyautogui.press("pagedown")
            time.sleep(settings.recommendations_pagedown_interval_sec)

        # Ожидание прогрузки
        log(f"  💤 Ожидание прогрузки ({settings.after_recommendations_wait_sec} сек)...")
        time.sleep(settings.after_recommendations_wait_sec)

        # Прокрутка к отзывам
        log("  📜 Прокрутка к отзывам...")
        for _ in range(reviews_pagedown_count):
            pyautogui.press("pagedown")
            time.sleep(settings.reviews_pagedown_interval_sec)

        # Поиск блока отзывов
        log(f"  🔎 Поиск блока отзывов по тексту: {settings.review_search_text!r}")
        pyautogui.hotkey("ctrl", "f")
        time.sleep(settings.find_dialog_open_wait_sec)

        set_clipboard(settings.review_search_text)
        time.sleep(settings.clipboard_settle_wait_sec)

        pyautogui.hotkey("ctrl", "v")
        time.sleep(settings.find_dialog_after_paste_wait_sec)

        for _ in range(find_iterations):
            pyautogui.press("enter")
            time.sleep(settings.find_iteration_interval_sec)

        pyautogui.press("esc")
        time.sleep(settings.find_dialog_close_wait_sec)

        # Раскрытие комментариев
        expand_comments_js(review_count)

        # Захват содержимого
        log("  📸 Захват данных...")
        pyautogui.hotkey("ctrl", "a")
        time.sleep(settings.before_capture_wait_sec)

        pyautogui.hotkey("ctrl", "c")
        time.sleep(settings.capture_wait_sec)

        raw_content = get_clipboard()

        log(f"  📦 Захвачено символов: {len(raw_content)}")

        # Закрытие вкладки
        pyautogui.hotkey("ctrl", "w")
        time.sleep(settings.after_tab_close_wait_sec)

        return {
            "raw_content": raw_content,
            "price": None,
            "name": "N/A",
        }

    def cleanup(self) -> None:
        log("  🧹 Очистка ресурсов...")
        # Firefox специально не убиваем: при постоянной работе воркера так быстрее.