import asyncio
import re
import os
import random
import time
import subprocess
import httpx
import pyautogui
import pyperclip
import pygetwindow as gw
import win32gui
import win32con
import win32com.client
from dotenv import load_dotenv, set_key

ENV_FILE = ".env"
load_dotenv(ENV_FILE)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # Небольшая задержка между командами для стабильности

async def login():
    """Первичная авторизация"""
    print("\nТребуется вход в систему")
    email = input("Введите email: ")
    password = input("Введите пароль: ")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                token = data.get("session_token")
                set_key(ENV_FILE, "SESSION_TOKEN", token)
                os.environ["SESSION_TOKEN"] = token
                print("Авторизация успешна.")
                return token
            else:
                print(f"Ошибка входа: {response.text}")
                return None
        except Exception as e:
            print(f"Ошибка сети: {e}")
            return None

async def get_valid_token():
    token = os.getenv("SESSION_TOKEN")
    if not token:
        token = await login()
    return token


def force_activate_chrome():
    """Улучшенная активация с гарантированным фокусом ввода."""
    def is_chrome_normal(window):
        return "Google Chrome" in window.title and "Incognito" not in window.title and "Инкогнито" not in window.title

    chrome_windows = [w for w in gw.getAllWindows() if is_chrome_normal(w)]
    
    if not chrome_windows:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        subprocess.Popen([chrome_path])
        time.sleep(5)
        chrome_windows = [w for w in gw.getAllWindows() if is_chrome_normal(w)]
        if not chrome_windows: return False

    win = chrome_windows[0]
    hwnd = win._hWnd

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('^') 

    try:
        win32gui.SetForegroundWindow(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        pyautogui.click(rect[0] + 150, rect[1] + 10) 
    except:
        pass

    time.sleep(0.5)
    # Имитируем реальную активность
    pyautogui.press('f6')  # Фокус на адресную строку
    time.sleep(0.2)
    return True

def run_ozon_scraping(ozon_id):
    print(f"Скрапинг товара {ozon_id}...")

    if not force_activate_chrome():
        return None

    pyautogui.press('alt')
    time.sleep(0.1)
    pyautogui.press('esc')
    time.sleep(0.2)

    pyautogui.hotkey('ctrl', 't')
    time.sleep(1.2)
    url = f"https://www.ozon.ru/product/{ozon_id}/"
    pyperclip.copy(url)
    pyautogui.hotkey('ctrl', 'v')
    pyautogui.press('enter')

    print("Загрузка страницы...")
    time.sleep(7)

    print("Спускаемся к блоку отзывов...")
    for _ in range(5):
        pyautogui.press('pgdn')
        time.sleep(random.uniform(0.3, 0.5))

    print("Прогружаем отзывы (50 итераций без остановок)...")
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    pyperclip.copy("Вам помог")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

    for _ in range(50):
        pyautogui.press('enter')
        time.sleep(0.13)

    print("Считаем комментарии...")
    pyautogui.press('esc')
    time.sleep(0.1)
    pyautogui.press('esc')
    time.sleep(0.2)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1.2)
    
    current_page_text = pyperclip.paste().lower()
    import re
    found_matches = re.findall(r'комментари', current_page_text)
    comment_limit = min(len(found_matches), 10)
    print(f"Найдено веток для раскрытия: {comment_limit}")

    if comment_limit > 0:
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyperclip.copy("комментари")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        for _ in range(comment_limit):
            pyautogui.press('enter')
            time.sleep(0.01)
            pyautogui.press('esc')
            time.sleep(0.01)
            pyautogui.press('enter')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.01)

    print("Финальный захват данных...")
    pyautogui.press('esc')
    time.sleep(0.1)
    pyautogui.press('esc')
    time.sleep(0.3)

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(1.2)

    final_text = pyperclip.paste()
    pyautogui.hotkey('ctrl', 'w')
    clean_content = preprocess_raw_content(final_text)

    return {
        "raw_content": clean_content
    }


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
        re.compile(r"^\+\d+$"),  # Блоки типа "+81" (доп. Фото)
        re.compile(r"^\d+\s*вопрос.*", re.IGNORECASE),  # "21 вопрос"
        re.compile(r"^\d+.*осталось", re.IGNORECASE),  # "17 шт. Осталось"
        re.compile(r"^[А-ЯЁA-Z]$"),  # Одиночные буквы-аватарки
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
        "Дом и сад", "Товары за 1₽", "Сертификаты", "Premium-магазин", "Распродажа",
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

        if any(p.match(line) for p in regex_keep):
            cleaned_lines.append(line)
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
        print(f"Статистика сжатия: {orig_len} -> {new_len} симв. (Уменьшено на {compression:.1f}%)")

    return result_text

async def complete_task_with_retry(client, task_id, payload, retries=5):
    """Пытается отправить результат несколько раз прежде чем сдаться"""
    for i in range(retries):
        try:
            resp = await client.post(f"{BASE_URL}/tasks/complete/{task_id}", json=payload)
            if resp.status_code == 200:
                print(f"✅ Задача #{task_id} успешно сдана!")
                return True
            print(f"⚠️ Сервер ответил {resp.status_code} при сдаче. Попытка {i+1}")
        except Exception as e:
            print(f"❌ Ошибка сети при сдаче #{task_id} (попытка {i+1}): {e}")
        
        await asyncio.sleep(2 * (i + 1)) # Экспоненциальная задержка
    return False


async def main():
    print("Воркер запущен...")
    token = await get_valid_token()
    if not token: return

    timeout = httpx.Timeout(45.0, connect=10.0)
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=timeout) as client:
        while True:
            try:
                print(f"\n📡 [{time.strftime('%H:%M:%S')}] Ожидание задачи...")
                response = await client.get(f"{BASE_URL}/tasks/take")
                
                if response.status_code == 200:
                    task = response.json()
                    if task:
                        task_id, ozon_id = task["task_id"], task["ozon_id"]
                        print(f"🚀 В работе задача #{task_id}")

                        scraped = run_ozon_scraping(ozon_id)
                        if scraped:
                            payload = {
                                "raw_content": scraped["raw_content"],
                                "price": 0, "name": "N/A"
                            }
                            # Отправляем с повторами
                            success = await complete_task_with_retry(client, task_id, payload)
                            if not success:
                                print(f"!!! Критиченская ошибка: Не удалось сдать задачу {task_id}")
                        continue 
                    else:
                        await asyncio.sleep(1)
                
                elif response.status_code == 401:
                    print("Получен 401 Unauthorized. Требуется повторная авторизация.")
                    new_token = await login()
                    if new_token:
                        token = new_token
                        client.headers["Authorization"] = f"Bearer {new_token}"
                        print("Токен обновлен. Продолжаем работу.")
                    else:
                        print("Авторизация не удалась. Повтор через 5 секунд.")
                    await asyncio.sleep(5)
                    continue
                else:
                    print(f"Сервер ответил: {response.status_code}")
                    await asyncio.sleep(5)

            except Exception as e:
                print(f"🛑 Ошибка в главном цикле: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка.")