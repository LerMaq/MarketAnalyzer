from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SCRAPER_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = SCRAPER_ROOT / ".env"

# Для локального запуска вне Docker. В Docker переменные обычно приходят через --env-file.
load_dotenv(ENV_PATH)


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class ScraperSettings:
    # Backend
    base_url: str = env_str("BASE_URL", "http://localhost:8000")
    worker_token: str = env_str("WORKER_TOKEN", "")
    worker_auth_header: str = env_str("WORKER_AUTH_HEADER", "X-Worker-Token")

    backend_ssl_verify: bool = env_bool("BACKEND_SSL_VERIFY", True)
    http_timeout_sec: float = env_float("HTTP_TIMEOUT_SEC", 60.0)
    http_connect_timeout_sec: float = env_float("HTTP_CONNECT_TIMEOUT_SEC", 15.0)

    # Worker loop
    task_poll_interval_sec: float = env_float("TASK_POLL_INTERVAL_SEC", 2.0)
    no_task_sleep_sec: float = env_float("NO_TASK_SLEEP_SEC", 2.0)
    error_retry_interval_sec: float = env_float("ERROR_RETRY_INTERVAL_SEC", 5.0)
    complete_retries: int = env_int("COMPLETE_RETRIES", 5)

    # Display / browser
    display: str = env_str("DISPLAY", ":99")
    screen_width: int = env_int("SCREEN_WIDTH", 1280)
    screen_height: int = env_int("SCREEN_HEIGHT", 720)
    screen_depth: int = env_int("SCREEN_DEPTH", 24)

    firefox_bin: str = env_str("FIREFOX_BIN", "firefox-esr")
    firefox_profile_dir: str = env_str("FIREFOX_PROFILE_DIR", "/tmp/firefox-profile")
    browser_startup_wait_sec: float = env_float("BROWSER_STARTUP_WAIT_SEC", 35.0)

    # Page timings
    new_tab_wait_sec: float = env_float("NEW_TAB_WAIT_SEC", 1.0)
    url_paste_wait_sec: float = env_float("URL_PASTE_WAIT_SEC", 0.3)
    page_initial_load_wait_sec: float = env_float("PAGE_INITIAL_LOAD_WAIT_SEC", 5.0)

    recommendations_pagedown_count: int = env_int("RECOMMENDATIONS_PAGEDOWN_COUNT", 4)
    recommendations_pagedown_interval_sec: float = env_float(
        "RECOMMENDATIONS_PAGEDOWN_INTERVAL_SEC",
        0.3,
    )
    after_recommendations_wait_sec: float = env_float(
        "AFTER_RECOMMENDATIONS_WAIT_SEC",
        5.0,
    )

    # fixed number of PageDown presses for scrolling from recommendations to reviews
    reviews_pagedown_count: int = env_int("REVIEWS_PAGEDOWN_COUNT", 6)
    reviews_pagedown_interval_sec: float = env_float("REVIEWS_PAGEDOWN_INTERVAL_SEC", 1.4)

    # Поиск блока отзывов
    review_search_text: str = env_str("REVIEW_SEARCH_TEXT", "Вам помог")
    find_min_iterations: int = env_int("FIND_MIN_ITERATIONS", 20)
    find_max_iterations: int = env_int("FIND_MAX_ITERATIONS", 250)
    find_iteration_interval_sec: float = env_float("FIND_ITERATION_INTERVAL_SEC", 0.3)

    # JS раскрытие комментариев
    devtools_open_wait_sec: float = env_float("DEVTOOLS_OPEN_WAIT_SEC", 3.0)
    devtools_close_wait_sec: float = env_float("DEVTOOLS_CLOSE_WAIT_SEC", 3.0)

    # PyAutoGUI
    pyautogui_pause_sec: float = env_float("PYAUTOGUI_PAUSE_SEC", 0.01)

    # Window activation
    window_activate_wait_sec: float = env_float("WINDOW_ACTIVATE_WAIT_SEC", 1.0)

    # Comments expansion
    comments_click_interval_sec: float = env_float("COMMENTS_CLICK_INTERVAL_SEC", 0.5)
    comments_click_max_limit: int = env_int("COMMENTS_CLICK_MAX_LIMIT", 100)

    # Clipboard
    clipboard_settle_wait_sec: float = env_float("CLIPBOARD_SETTLE_WAIT_SEC", 0.2)

    # DevTools interaction
    devtools_after_paste_wait_sec: float = env_float("DEVTOOLS_AFTER_PASTE_WAIT_SEC", 0.5)
    devtools_after_enter_wait_sec: float = env_float("DEVTOOLS_AFTER_ENTER_WAIT_SEC", 1.0)

    # Find dialog
    find_dialog_open_wait_sec: float = env_float("FIND_DIALOG_OPEN_WAIT_SEC", 0.5)
    find_dialog_after_paste_wait_sec: float = env_float("FIND_DIALOG_AFTER_PASTE_WAIT_SEC", 0.2)
    find_dialog_close_wait_sec: float = env_float("FIND_DIALOG_CLOSE_WAIT_SEC", 0.3)

    # Capture
    before_capture_wait_sec: float = env_float("BEFORE_CAPTURE_WAIT_SEC", 1.0)
    capture_wait_sec: float = env_float("CAPTURE_WAIT_SEC", 2.0)
    after_tab_close_wait_sec: float = env_float("AFTER_TAB_CLOSE_WAIT_SEC", 0.5)

    # API base URL (derived from base_url)
    @property
    def api_base_url(self) -> str:
        return self.base_url.rstrip("/")

    def require_valid(self) -> None:
        errors: list[str] = []

        if not self.base_url:
            errors.append("BASE_URL is required")

        if not self.worker_token:
            errors.append("WORKER_TOKEN is required")

        if not self.worker_auth_header:
            errors.append("WORKER_AUTH_HEADER is required")

        if self.find_max_iterations < self.find_min_iterations:
            errors.append("FIND_MAX_ITERATIONS must be >= FIND_MIN_ITERATIONS")

        if errors:
            raise RuntimeError("Invalid scraper config:\n- " + "\n- ".join(errors))

    def find_iterations_for(self, review_count: int) -> int:
        """
        Старый FIND_ITERATIONS=50 заменён на расчёт от review_count.
        Safety-limit остаётся в env, чтобы скрапер не зависал бесконечно.
        """
        review_count = max(1, review_count)
        return min(
            self.find_max_iterations,
            max(self.find_min_iterations, review_count),
        )

    def comments_click_limit_for(self, review_count: int) -> int:
        review_count = max(1, review_count)
        return min(review_count, self.comments_click_max_limit)


settings = ScraperSettings()