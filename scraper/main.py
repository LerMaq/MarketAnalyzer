"""
OzonAI Scraper — Главная программа.

Платформо-независимая логика:
- Авторизация на бэкенде
- Получение задач
- Вызов платформо-специфичного скрапера
- Обработка и отправка результатов
"""

import asyncio
import os
import re
import sys
import time
from typing import Optional, Dict, Any

# Добавляем директорию скрипта и родительскую в путь для импортов
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

import httpx
from dotenv import load_dotenv

# Загружаем переменные окружения из .env в директории скрипта
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PLATFORM = os.getenv("PLATFORM", "debian")


def get_browser_controller():
    """
    Динамический импорт контроллера для указанной платформы.

    Returns:
        BrowserController: Реализация для текущей платформы.
    """
    # Используем явный импорт через scraper.platform, чтобы избежать конфликта с built-in platform
    if PLATFORM == "debian":
        from scraper.platform.debian.controller import BrowserControllerImpl
    elif PLATFORM == "ubuntu":
        from scraper.platform.ubuntu.controller import BrowserControllerImpl
    elif PLATFORM == "windows":
        from scraper.platform.windows.controller import BrowserControllerImpl
    else:
        raise ValueError(f"Неизвестная платформа: {PLATFORM}")

    return BrowserControllerImpl()


def preprocess_raw_content(text: str) -> str:
    """
    Очищает сырой текст страницы Ozon от UI-мусора, рекламы и футера,
    сохраняя при этом важный контекст (отзывы, даты, оценки полезности и характеристики).
    """
    if not text:
        return ""

    orig_len = len(text)
    regex_keep = [
        re.compile(r"^(Да|Нет)\s+\d+$", re.IGNORECASE),
        re.compile(r"^(Срок использования|Цвет|Размер|Вес|Объем|SSD|RAM):.*", re.IGNORECASE),
        re.compile(
            r"^\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}"),
    ]

    regex_noise = [
        re.compile(r"^\+\d+$"),
        re.compile(r"^\d+\s*вопрос.*", re.IGNORECASE),
        re.compile(r"^\d+.*осталось", re.IGNORECASE),
        re.compile(r"^[А-ЯЁA-Z]$"),
    ]

    ui_noise = {
        "Везде Искать на Ozon", "Пункт Ozon", "Каталог", "Реклама", "В сравнение",
        "Поделиться", "Постоплата", "Цена что надо", "Больше 99% выкупа",
        "Оплата после получения", "При заказе в пункт выдачи", "Перейти к описанию",
        "Фото и видео покупателей", "c Ozon Картой", "без Ozon Карты", "Стало дешевле",
        "Оплатить позже", "без % до", "Хочу скидку", "Добавить в корзину", "Доставим завтра",
        "Купить в один клик", "Информация о доставке", "Со склада Ozon", "Курьером Ozon",
        "Без доплат", "Перейти в магазин", "Написать в магазин", "Доставка и сервис Ozon",
        "Безопасная оплата онлайн", "Возврат 21 день", "Вам помог этот отзыв?", "Ответить",
        "Показать сначала", "Подборки товаров в категории", "Избранное", "Корзина",
        "Ozon Карта", "Билеты, отели", "Для бизнеса", "Одежда, обувь", "Электроника",
        "Товары за 1₽", "Сертификаты", "Premium-магазин", "Распродажа",
        "Отзывы могут оставлять", "Рейтинг формируется", "Сравнивать", "Заказы",
        "Данил", "Вопросы о товаре", "баллов за отзыв"
    }

    footer_markers = ["Ozon Job", "Ozon маркетплейс", "© 1998", "Для слабовидящих"]
    spam_triggers = ["Рекомендуем также", "Покупают вместе", "Подобрали для вас", "У других продавцов"]
    stop_spam_triggers = ["Описание", "Комплектация", "Характеристики", "Отзывы о товаре"]

    lines = text.splitlines()
    cleaned_lines = []
    is_spam_block = False

    for line in lines:
        line = line.strip()

        if not line or (len(line) < 2 and not any(p.match(line) for p in regex_keep)):
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

        if any(noise.lower() in line.lower() for noise in ui_noise):
            continue

        if any(p.match(line) for p in regex_noise):
            continue
        cleaned_lines.append(line)

    final_result = []
    for i, line in enumerate(cleaned_lines):
        if i == 0 or line != cleaned_lines[i - 1]:
            final_result.append(line)

    result_text = "\n".join(final_result)
    new_len = len(result_text)

    if orig_len > 0:
        compression = 100 - (new_len / orig_len * 100)
        print(f"📊 Статистика сжатия: {orig_len} -> {new_len} симв. (Уменьшено на {compression:.1f}%)")

    return result_text


async def login(retries: int = 5) -> Optional[str]:
    """Первичная авторизация на бэкенде с повторными попытками."""
    
    while True:  # Цикл до успешной авторизации или отмены пользователем
        print("\n🔐 Требуется вход в систему")
        email = input("Введите email: ")
        password = input("Введите пароль: ")

        for i in range(retries):
            # Отключаем проверку SSL для самоподписанных сертификатов
            async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(30.0, connect=15.0)) as client:
                try:
                    print(f"\n📡 Попытка авторизации {i + 1}/{retries}...")
                    response = await client.post(
                        f"{BASE_URL}/auth/login",
                        json={"email": email, "password": password}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        token = data.get("session_token")
                        if token:
                            # Сохраняем токен в .env в директории скрипта
                            env_path = os.path.join(os.path.dirname(__file__), ".env")
                            with open(env_path, "r") as f:
                                content = f.read()
                            if "SESSION_TOKEN=" in content:
                                content = re.sub(
                                    r"SESSION_TOKEN=.*",
                                    f"SESSION_TOKEN={token}",
                                    content
                                )
                            else:
                                content += f"\nSESSION_TOKEN={token}"
                            with open(env_path, "w") as f:
                                f.write(content)
                            os.environ["SESSION_TOKEN"] = token
                            print("✅ Авторизация успешна.")
                            return token
                    # Ошибка авторизации (неверный логин/пароль)
                    print(f"❌ Ошибка входа: {response.text}")
                    print("Попробуйте ввести данные заново.")
                    break  # Выход из цикла попыток, возврат к вводу email/пароля
                except Exception as e:
                    print(f"⚠️ Ошибка сети: {e}")
                    if i < retries - 1:
                        wait_time = 2 * (i + 1)
                        print(f"🔄 Повторная попытка через {wait_time} сек...")
                        await asyncio.sleep(wait_time)
                    else:
                        print("❌ Все попытки авторизации исчерпаны.")
                        print("Попробуйте ввести данные заново.")
                        break  # Выход из цикла попыток, возврат к вводу email/пароля
        
        # Спрашиваем, хочет ли пользователь продолжить
        print("")
        retry = input("Продолжить попытку входа? (y/n): ").strip().lower()
        if retry != 'y' and retry != 'Y' and retry != 'н' and retry != 'Н':
            print("❌ Авторизация отменена пользователем.")
            return None
    
    return None


async def get_valid_token() -> Optional[str]:
    """Получение валидного токена (из env или через авторизацию)."""
    token = os.getenv("SESSION_TOKEN")
    if not token:
        token = await login(retries=5)
    return token


async def complete_task_with_retry(
    client: httpx.AsyncClient,
    task_id: int,
    payload: Dict[str, Any],
    retries: int = 5
) -> bool:
    """Попытка отправить результат задачи с повторами."""
    for i in range(retries):
        try:
            resp = await client.post(
                f"{BASE_URL}/tasks/complete/{task_id}",
                json=payload
            )
            if resp.status_code == 200:
                print(f"✅ Задача #{task_id} успешно сдана!")
                return True
            print(f"⚠️ Сервер ответил {resp.status_code} при сдаче. Попытка {i + 1}")
        except Exception as e:
            print(f"❌ Ошибка сети при сдаче #{task_id} (попытка {i + 1}): {e}")
        await asyncio.sleep(2 * (i + 1))
    return False


async def main():
    """Главный цикл работы скрапера."""
    print(f"🚀 OzonAI Scraper запущен (платформа: {PLATFORM})")

    # Получаем токен
    token = await get_valid_token()
    if not token:
        print("❌ Не удалось авторизоваться. Выход.")
        return

    # Инициализируем браузер через платформо-специфичный контроллер
    print("🌐 Инициализация браузера...")
    browser = get_browser_controller()
    if not browser.initialize():
        print("❌ Не удалось инициализировать браузер. Выход.")
        return
    print("✅ Браузер готов.")

    # Основной цикл
    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
        verify=False
    ) as client:
        while True:
            try:
                print(f"\n📡 [{time.strftime('%H:%M:%S')}] Ожидание задачи...")
                response = await client.get(f"{BASE_URL}/tasks/take")

                if response.status_code == 200:
                    task = response.json()
                    if task:
                        task_id = task["task_id"]
                        ozon_id = task["ozon_id"]
                        print(f"🔍 В работе задача #{task_id} (ozon_id: {ozon_id})")

                        # Вызов платформо-специфичного скрапинга
                        scraped = browser.scrape_product(ozon_id)
                        if scraped and scraped.get("raw_content"):
                            # Обработка данных (общая для всех платформ)
                            clean_content = preprocess_raw_content(scraped["raw_content"])

                            payload = {
                                "raw_content": clean_content,
                                "price": 0,
                                "name": "N/A"
                            }

                            # Отправка результата
                            success = await complete_task_with_retry(
                                client, task_id, payload
                            )
                            if not success:
                                print(f"!!! Критическая ошибка: Не удалось сдать задачу #{task_id}")
                        continue
                    else:
                        await asyncio.sleep(2)

                elif response.status_code == 401:
                    print("⚠️ Получен 401 Unauthorized. Повторная авторизация...")
                    new_token = await login(retries=5)
                    if new_token:
                        token = new_token
                        client.headers["Authorization"] = f"Bearer {new_token}"
                        print("✅ Токен обновлён.")
                    else:
                        print("❌ Авторизация не удалась. Повтор через 10 секунд.")
                    await asyncio.sleep(10)
                    continue

                else:
                    print(f"⚠️ Сервер ответил: {response.status_code}")
                    await asyncio.sleep(10)

            except KeyboardInterrupt:
                print("\n🛑 Остановка по сигналу Ctrl+C.")
                browser.cleanup()
                break
            except Exception as e:
                print(f"🛑 Ошибка в главном цикле: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка.")
