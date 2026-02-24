import asyncio
import httpx


async def test_stream():
    """Рабочий пример получения потоковой генерации сообщения нейросети"""
    url = "http://127.0.0.1:8000/chat/stream"
    payload = {
        "chat_id": 2, # Взять из БД
        "message_text": "Расскажи супер много о товаре для доклада"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Статус: {response.status_code}")
                async for chunk in response.aiter_text():
                    print(chunk, end="", flush=True)
    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_stream())