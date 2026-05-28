import asyncio
import sys
import httpx


async def worker_send_data():
    print("=== Эмулятор Воркера: Отправка данных на анализ ===")

    # 1. Сбор метаданных
    base_url = input("Введите Base URL (по умолчанию http://localhost:8000): ").strip() or "http://localhost:8000"
    task_id = input("Введите task_id: ").strip()
    token = input("Введите worker token (X-Worker-Token): ").strip()

    if not task_id or not token:
        print("Ошибка: task_id и токен обязательны!")
        return

    # 2. Сбор контента (через Ctrl+D / Ctrl+Z)
    print("\n--- Вставьте raw_content (текст со страницы Ozon) ---")
    print("--- (Для завершения: Ctrl+D в Linux/Mac или Ctrl+Z в Windows на новой строке) ---")

    raw_content = sys.stdin.read().strip()

    if not raw_content:
        print("Ошибка: Контент пуст!")
        return

    # 3. Подготовка запроса
    url = f"{base_url}/tasks/complete/{task_id}"
    headers = {
        "X-Worker-Token": token,
        "Content-Type": "application/json"
    }
    # Мы передаем словарь в параметр json, httpx сам корректно его сериализует
    payload = {
        "raw_content": raw_content,
        "price": 0,  # Заглушки, так как схемы STaskWorkerData могут их требовать
        "name": "string"
    }

    # 4. Выполнение запроса
    print(f"\nОтправка запроса на {url}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                print("\n✅ УСПЕХ!")
                print("Ответ сервера:", response.json())
            else:
                print(f"\n❌ ОШИБКА (Статус {response.status_code})")
                print("Детали:", response.text)

    except Exception as e:
        print(f"\n☢️ Критическая ошибка при отправке: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(worker_send_data())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")