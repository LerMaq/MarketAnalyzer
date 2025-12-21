async def generate_ai_summary(reviews: list) -> str:
    # Здесь будет вызов OpenAI / DeepSeek
    return "Общая оценка: Товар отличный, но есть нюансы..."

async def calculate_metrics(reviews: list) -> list:
    # Здесь логика подсчета баллов
    return [{"name": "Качество", "score": 85, "explanation": "Хорошо"}]