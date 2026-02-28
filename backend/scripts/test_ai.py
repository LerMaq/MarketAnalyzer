import asyncio
import httpx


async def test_stream(chat_id: str, message_text: str, token: str):
    """Пример получения потоковой генерации с динамическими данными"""
    url = "http://127.0.0.1:8000/chat/stream"

    payload = {
        "chat_id": int(chat_id),  # Преобразуем в число, если API ждет int
        "message_text": message_text
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("\n--- Ответ нейросети ---")
    try:
        # Увеличили timeout, так как генерация может быть долгой
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    print(f"Ошибка сервера: {response.status_code}")
                    return

                async for chunk in response.aiter_text():
                    print(chunk, end="", flush=True)
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")


async def main():
    # Собираем данные от пользователя
    print("=== Настройка подключения ===")
    token = input("Введите ваш Bearer токен: ").strip()
    chat_id = input("Введите chat_id: ").strip()
    message_text = input("Введите сообщение для нейросети: ").strip()

    if not token or not chat_id or not message_text:
        print("Ошибка: Все поля должны быть заполнены!")
        return

    await test_stream(chat_id, message_text, token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")