import json
import re
from typing import Optional

from openai import AsyncOpenAI
import httpx

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.config import settings
from app.models import User
from app.repositories import AiRepository, ProductRepository
from app.services.embedding_service import EmbeddingService
from app.schemas import SAiAnalysisResponse, SModelPreset, SSystemAiKeyCreate, ApiProviderPreset


def extract_json_from_text(text: str) -> dict:
    """
    Извлекает JSON из текста, который может содержать markdown-обёртку или другой текст.
    Поддерживает форматы:
    - ```json {...} ```
    - ```{...}```
    - {...}
    - Текст до/после JSON
    """
    if isinstance(text, dict):
        return text
    
    # Попытка 1: Поиск JSON в markdown блоке ```json ... ```
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    
    # Попытка 2: Поиск JSON в обычном markdown блоке ``` ... ```
    json_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    
    # Попытка 3: Поиск JSON без обёртки
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    
    # Попытка 4: Парсинг всей строки как JSON
    return json.loads(text)


class AIService:
    PRESET_TEMPLATES = {
        "google": {
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "models": [
                SModelPreset(model_name="gemini-2.5-flash", priority=8),
                SModelPreset(model_name="gemini-3.5-flash", priority=8),
                SModelPreset(model_name="gemini-2.5-flash-lite", priority=10),
                SModelPreset(model_name="gemini-3.1-flash-lite", priority=11),
            ]
        },
        "openai": {
            "url": "https://api.openai.com/v1",
            "models": [
                SModelPreset(model_name="gpt-4o", priority=9),
                SModelPreset(model_name="gpt-4o-mini", priority=8),
                SModelPreset(model_name="gpt-5-mini", priority=10),
                SModelPreset(model_name="o1-preview", priority=1),
            ]
        }
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AiRepository(db)
        self.prod_repo = ProductRepository(db)
        self.embedding_service = EmbeddingService()

    async def get_report_completion(self, raw_content: str) -> SAiAnalysisResponse:
        config = await self.repo.get_config("report_generation")
        if not config:
            raise HTTPException(status_code=500, detail="AI Config 'report_generation' not found")

        search_context = raw_content[:1000]

        print(f"Генерация эмбеддинга для анализа: len(raw_content)={len(raw_content)}, len(search_context)={len(search_context)}")
        try:
            query_vector = await self.embedding_service.get_vector(search_context)
            print(f"Эмбеддинг успешно сгенерирован: dim={len(query_vector)}")
        except Exception as e:
            print(f"Ошибка генерации эмбеддинга перед анализом: {e}")
            raise

        relevant_metrics = await self.prod_repo.get_metrics_with_similarity(query_vector, limit=40)
        quality_metrics_count = sum(1 for m in relevant_metrics if m['score'] > settings.METRIC_SIMILARITY_THRESHOLD)
        strict_mode = quality_metrics_count >= settings.MIN_QUALITY_METRICS_COUNT

        if strict_mode:
            custom_instruction = (
                "БАЗА ДАННЫХ ПОЛНОСТЬЮ УКОМПЛЕКТОВАНА. Тебе КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО создавать новые кастомные метрики. "
                "Используй только предоставленные метрики из списка ниже."
            )
        else:
            custom_instruction = (
                "Ты можешь использовать предоставленные метрики или создать новые, "
                "но только если среди предложенных нет ничего подходящего."
            )

        standards = await self.prod_repo.get_standard_metrics()
        standards_text = "\n".join([f"- {m.name}: {m.description}. Вес: {m.weight}" for m in standards[:10]])
        
        customs_text = "\n".join([
            f"- {m['metric'].name}: {m['metric'].description}. Вес: {m['metric'].weight} (similarity: {m['score']:.3f})"
            for m in relevant_metrics
        ])

        user_content = (
            f"СПРАВОЧНИК СТАНДАРТНЫХ МЕТРИК (выбери любые 5):\n{standards_text}\n\n"
            f"КАСТОМНЫЕ МЕТРИКИ (найдено {len(relevant_metrics)}, из них качественных: {quality_metrics_count}):\n{customs_text}\n\n"
            f"ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ МЕТРИК:\n{custom_instruction}\n\n"
            f"ДАННЫЕ ТОВАРА ДЛЯ АНАЛИЗА:\n{raw_content}\n\n"
            f"ЗАДАНИЕ: Проанализируй товар и выдай JSON строго по структуре из системной инструкции. "
            f"В поле 'thinking' объясни, какие кастомные метрики ты выбрал и почему отбросил другие."
        )

        messages = [
            {"role": "user", "content": user_content}
        ]
        
        print(f"В нейросеть отправляются данные о товаре для анализа...")
        print(f"Режим: {'STRICT (запрет создания новых метрик)' if strict_mode else 'FLEXIBLE (можно создавать новые)'}")
        print(f"Найдено релевантных метрик: {len(relevant_metrics)}, качественных: {quality_metrics_count}")

        for v_attempt in range(3):
            try:
                print(f"Попытка {v_attempt + 1}/3: выполнить AI-вызов для задачи")
                raw_response = await self.execute(config=config, messages=messages)
                print(f"Нейросеть вернула ответ: {raw_response}")

                # Извлекаем JSON из текста (если он обёрнут в markdown или содержит лишний текст)
                if isinstance(raw_response, str):
                    try:
                        parsed_json = extract_json_from_text(raw_response)
                        print(f"JSON успешно извлечён из текста")
                    except Exception as parse_error:
                        print(f"Ошибка извлечения JSON: {parse_error}")
                        raise
                else:
                    parsed_json = raw_response

                validated_data = SAiAnalysisResponse.model_validate(parsed_json)
                print(f"Анализ успешно валидирован Pydantic.")
                return validated_data

            except ValidationError as ve:
                print(f"Ошибка валидации Pydantic: {ve}")
                # Можно добавить небольшую подсказку в messages для следующей попытки,
                # но пока просто пробуем еще раз
                continue
            except Exception as e:
                print(f"Ошибка на этапе AI-анализа: {e}")
                raise HTTPException(status_code=503, detail=f"Ошибка провайдера ИИ: {str(e)}")

        raise HTTPException(status_code=500, detail="ИИ не смог выдать валидный JSON после 3 попыток")

    async def execute(self, config, messages, model_record=None):
        """
        Выполняет запрос к ИИ.
        Если model_record не передан или не работает, перебирает лучшие системные модели.
        """
        # Слой перебора моделей
        for m_attempt in range(10):
            # Если модель не передана или это повторная попытка после ошибки
            if not model_record:
                model_record = await self.repo.get_best_model_with_key()
                if not model_record:
                    raise Exception("Нет доступных системных моделей")

            if hasattr(model_record, "api_key"):  # Это системная модель (SystemAiModel)
                api_key_val = model_record.api_key.key
                base_url_val = model_record.api_key.provider_url
                model_name_val = model_record.model_name
            else: # Это пользовательская модель (AiApiKey)
                api_key_val = model_record.key
                base_url_val = model_record.provider_url
                model_name_val = model_record.model_name

            print(f"Попытка модели {m_attempt + 1}/10: модель={model_name_val}, base_url={base_url_val}")
            http_client = httpx.AsyncClient(proxy=settings.HTTP_PROXY if settings.HTTP_PROXY else None)
            try:
                client = AsyncOpenAI(
                    api_key=api_key_val,
                    base_url=base_url_val,
                    http_client=http_client
                )

                # Копируем messages для работы
                working_messages = [{"role": "system", "content": config.system_instruction}] + messages.copy()

                request_params = {
                    "model": model_name_val,
                    "messages": working_messages,
                    "temperature": config.temperature,
                    "stream": config.is_stream
                }

                if config.is_json and not config.is_stream:
                    request_params["response_format"] = {"type": "json_object"}

                print(f"Запрос к модели: {request_params}")
                response = await client.chat.completions.create(**request_params)
                print(f"Ответ от модели получен, response type={type(response)}")

                # Обработка стриминга
                if config.is_stream:
                    return self.create_stream_generator(response, http_client)

                # Обработка финального ответа
                result = response.choices[0].message.content
                await http_client.aclose()

                if not result:
                    raise ValueError("Пустой ответ от модели")

                return json.loads(result) if config.is_json else result

            except Exception as e:
                await http_client.aclose()
                print(f"Ошибка модели {model_record.model_name}: {e}")

                if hasattr(model_record, 'id'): # Если модель системная
                    await self.repo.mark_model_broken(model_record.id)

                # Сбрасываем текущую модель, чтобы на следующей итерации взялась новая системная
                model_record = None
                continue

        raise Exception("Слой перебора моделей исчерпал все попытки")

    async def create_stream_generator(self, response, http_client):
        try:
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        finally:
            await http_client.aclose()

    async def add_key_with_preset(self, data: SSystemAiKeyCreate, user: Optional[User]):
        if not user:
            raise HTTPException(status_code=401, detail="Log in required")

        if "ai.manage_keys" not in user.active_permissions:
            raise HTTPException(status_code=403, detail="Недостаточно прав для управления ключами")

        template = self.PRESET_TEMPLATES.get(data.preset.value)

        if data.preset == ApiProviderPreset.custom:
            url = data.provider_url
        else:
            url = template["url"] if template else data.provider_url

        if not url or url == "string":
            raise HTTPException(status_code=400, detail="Укажите корректный URL или выберите пресет")

        key_payload = {
            "key": data.key,
            "provider_url": url
        }

        models = template["models"] if template else []
        new_key = await self.repo.create_system_key_with_models(key_payload, models)

        return {
            "status": "success",
            "key_id": new_key.id,
            "models_created": len(models)
        }
