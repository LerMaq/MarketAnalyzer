from __future__ import annotations

import asyncio
import re
import time
from typing import Any

import httpx

from core.config import settings
from core.controller import BrowserControllerImpl


def log(message: str) -> None:
    print(message, flush=True)


def preprocess_raw_content(text: str) -> str:
    """
    Очищает сырой текст страницы Ozon от UI-мусора, рекламы и футера,
    сохраняя полезный контекст: отзывы, даты, характеристики, оценки полезности.
    """
    if not text:
        return ""

    orig_len = len(text)

    regex_keep = [
        re.compile(r"^(Да|Нет)\s+\d+$", re.IGNORECASE),
        re.compile(r"^(Срок использования|Цвет|Размер|Вес|Объем|SSD|RAM|Память):.*", re.IGNORECASE),
        re.compile(
            r"^\d{1,2}\s+"
            r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
            r"\s+\d{4}",
            re.IGNORECASE,
        ),
    ]

    regex_noise = [
        re.compile(r"^\+\d+$"),
        re.compile(r"^\d+\s*вопрос.*", re.IGNORECASE),
        re.compile(r"^\d+.*осталось", re.IGNORECASE),
        re.compile(r"^[А-ЯЁA-Z]$"),
    ]

    ui_noise = {
        "Везде Искать на Ozon",
        "Пункт Ozon",
        "Каталог",
        "Реклама",
        "В сравнение",
        "Поделиться",
        "Постоплата",
        "Цена что надо",
        "Больше 99% выкупа",
        "Оплата после получения",
        "При заказе в пункт выдачи",
        "Перейти к описанию",
        "Фото и видео покупателей",
        "c Ozon Картой",
        "без Ozon Карты",
        "Стало дешевле",
        "Оплатить позже",
        "без % до",
        "Хочу скидку",
        "Добавить в корзину",
        "Доставим завтра",
        "Купить в один клик",
        "Информация о доставке",
        "Со склада Ozon",
        "Курьером Ozon",
        "Без доплат",
        "Перейти в магазин",
        "Написать в магазин",
        "Доставка и сервис Ozon",
        "Безопасная оплата онлайн",
        "Возврат 21 день",
        "Вам помог этот отзыв?",
        "Ответить",
        "Показать сначала",
        "Подборки товаров в категории",
        "Избранное",
        "Корзина",
        "Ozon Карта",
        "Билеты, отели",
        "Для бизнеса",
        "Одежда, обувь",
        "Электроника",
        "Товары за 1₽",
        "Сертификаты",
        "Premium-магазин",
        "Распродажа",
        "Отзывы могут оставлять",
        "Рейтинг формируется",
        "Сравнивать",
        "Заказы",
        "Вопросы о товаре",
        "баллов за отзыв",
    }

    footer_markers = [
        "Ozon Job",
        "Ozon маркетплейс",
        "© 1998",
        "Для слабовидящих",
    ]

    spam_triggers = [
        "Рекомендуем также",
        "Покупают вместе",
        "Подобрали для вас",
        "У других продавцов",
    ]

    stop_spam_triggers = [
        "Описание",
        "Комплектация",
        "Характеристики",
        "Отзывы о товаре",
    ]

    lines = text.splitlines()
    cleaned_lines: list[str] = []
    is_spam_block = False

    for line in lines:
        line = line.strip()

        if not line or (len(line) < 2 and not any(pattern.match(line) for pattern in regex_keep)):
            continue

        if any(marker in line for marker in footer_markers):
            break

        if any(trigger in line for trigger in spam_triggers):
            is_spam_block = True
            continue

        if is_spam_block:
            if any(stop in line for stop in stop_spam_triggers) or regex_keep[2].match(line):
                is_spam_block = False
            else:
                continue

        lowered = line.lower()

        if any(noise.lower() in lowered for noise in ui_noise):
            continue

        if any(pattern.match(line) for pattern in regex_noise):
            continue

        cleaned_lines.append(line)

    final_result: list[str] = []
    for index, line in enumerate(cleaned_lines):
        if index == 0 or line != cleaned_lines[index - 1]:
            final_result.append(line)

    result_text = "\n".join(final_result)
    new_len = len(result_text)

    if orig_len > 0:
        compression = 100 - (new_len / orig_len * 100)
        log(f"Статистика сжатия: {orig_len} -> {new_len} симв. (-{compression:.1f}%)")

    return result_text


def create_http_client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        settings.http_timeout_sec,
        connect=settings.http_connect_timeout_sec,
    )

    return httpx.AsyncClient(
        headers={
            settings.worker_auth_header: settings.worker_token,
        },
        timeout=timeout,
        verify=settings.backend_ssl_verify,
    )


async def take_task(client: httpx.AsyncClient) -> dict[str, Any] | None:
    response = await client.get(f"{settings.api_base_url}/tasks/take")

    if response.status_code in {204, 404}:
        return None

    if response.status_code == 200:
        if not response.content:
            return None
        return response.json()

    if response.status_code in {401, 403}:
        raise RuntimeError(
            f"Worker auth failed: backend returned {response.status_code}. "
            f"Check WORKER_TOKEN and {settings.worker_auth_header}."
        )

    raise RuntimeError(
        f"Unexpected /tasks/take response: {response.status_code}, body={response.text[:500]}"
    )


async def complete_task_with_retry(
    client: httpx.AsyncClient,
    task_id: int,
    payload: dict[str, Any],
) -> bool:
    for attempt in range(1, settings.complete_retries + 1):
        try:
            response = await client.post(
                f"{settings.api_base_url}/tasks/complete/{task_id}",
                json=payload,
            )

            if response.status_code == 200:
                log(f"Задача #{task_id} успешно сдана.")
                return True

            log(
                f"Backend ответил {response.status_code} при сдаче задачи #{task_id}. "
                f"Попытка {attempt}/{settings.complete_retries}. Body={response.text[:500]}"
            )

        except Exception as exc:
            log(
                f"Ошибка сети при сдаче задачи #{task_id}. "
                f"Попытка {attempt}/{settings.complete_retries}: {exc}"
            )

        await asyncio.sleep(2 * attempt)

    return False


def normalize_task(task: dict[str, Any]) -> tuple[int, int, int]:
    task_id = int(task["task_id"])
    ozon_id = int(task["ozon_id"])
    review_count = int(task.get("review_count") or 50)

    return task_id, ozon_id, review_count


async def main() -> None:
    settings.require_valid()

    log("MarketAnalyzer Scraper запущен")
    log(f"Backend: {settings.api_base_url}")
    log(f"Worker auth header: {settings.worker_auth_header}")
    log(f"Display: {settings.display}")

    browser = BrowserControllerImpl()

    log("Инициализация браузера...")
    if not browser.initialize():
        log("Не удалось инициализировать браузер. Выход.")
        return

    log("Браузер готов.")

    async with create_http_client() as client:
        while True:
            try:
                log(f"\n[{time.strftime('%H:%M:%S')}] Ожидание задачи...")

                task = await take_task(client)

                if not task:
                    await asyncio.sleep(settings.no_task_sleep_sec)
                    continue

                task_id, ozon_id, review_count = normalize_task(task)

                log(
                    f"В работе задача #{task_id}: "
                    f"ozon_id={ozon_id}, review_count={review_count}"
                )

                scraped = browser.scrape_product(
                    ozon_id=ozon_id,
                    review_count=review_count,
                )

                raw_content = scraped.get("raw_content") or ""
                clean_content = preprocess_raw_content(raw_content)

                payload = {
                    "raw_content": clean_content,
                    "price": scraped.get("price"),
                    "name": scraped.get("name") or "N/A",
                }

                success = await complete_task_with_retry(client, task_id, payload)

                if not success:
                    log(f"!!! Критическая ошибка: не удалось сдать задачу #{task_id}")

                await asyncio.sleep(settings.task_poll_interval_sec)

            except KeyboardInterrupt:
                log("\nОстановка по Ctrl+C.")
                browser.cleanup()
                break

            except Exception as exc:
                log(f"Ошибка в главном цикле: {exc}")
                await asyncio.sleep(settings.error_retry_interval_sec)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\nОстановка.")