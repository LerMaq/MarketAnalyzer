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
                SModelPreset(model_name="gemini-3-flash", priority=8),
                SModelPreset(model_name="gemini-2.5-flash-lite", priority=10),
                SModelPreset(model_name="gemma-3-27b-it", priority=3),
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

        standards = await self.prod_repo.get_standard_metrics()
        standards_text = "\n".join([f"- {m.name}: {m.description}. Вес: {m.weight}" for m in standards])

        # Определяем tools для поиска метрик
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_metrics",
                    "description": "Поиск кастомных метрик в базе данных по названию или описанию. Используй этот инструмент для поиска существующих метрик перед созданием новых.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Поисковый запрос: название метрики или ключевые слова из описания (например, 'прочность', 'качество звука', 'удобство использования')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Максимальное количество результатов поиска",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        user_content = (
            f"СПРАВОЧНИК СТАНДАРТНЫХ МЕТРИК:\n\n"
            f"Стандартные метрики (product_metrics_standard) — выбери любые 5:\n{standards_text}\n\n"
            f"ИНСТРУМЕНТ ДЛЯ ПОИСКА КАСТОМНЫХ МЕТРИК:\n"
            f"У тебя есть доступ к функции search_metrics для поиска кастомных метрик в базе данных. "
            f"ОБЯЗАТЕЛЬНО используй её перед созданием новых метрик! Сделай несколько поисковых запросов "
            f"с разными ключевыми словами, связанными с товаром (например, для наушников: 'звук', 'качество звука', "
            f"'удобство', 'батарея', 'шумоподавление'). Если найдёшь подходящие метрики — используй их. "
            f"Создавай новые метрики только если поиск не дал релевантных результатов.\n\n"
            f"ДАННЫЕ ТОВАРА ДЛЯ АНАЛИЗА:\n{raw_content}\n\n"
            f"ЗАДАНИЕ: Проанализируй товар и выдай JSON строго по структуре из системной инструкции."
        )

        messages = [
            {"role": "user", "content": user_content}
        ]
        print(f"В нейросеть отправляются данные о товаре для анализа...")
        # print(f"В нейросеть отправляются следующие данные о товаре для анализа:"
        #       f"{messages}")

        for v_attempt in range(3):
            try:
                raw_response = await self.execute(config=config, messages=messages, tools=tools)
                print(f"Нейросеть сгенерировала отчёт! Вот её чистый ответ: {raw_response}")

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
                return validated_data

            except ValidationError as ve:
                print(f"Ошибка валидации Pydantic: {ve}")
                # Можно добавить небольшую подсказку в messages для следующей попытки,
                # но пока просто пробуем еще раз
                continue
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"Ошибка провайдера ИИ: {str(e)}")

        raise HTTPException(status_code=500, detail="ИИ не смог выдать валидный JSON после 3 попыток")

    async def execute(self, config, messages, tools=None, model_record=None):
        """
        Выполняет запрос к ИИ.
        Если model_record не передан или не работает, перебирает лучшие системные модели.
        Поддерживает function calling через параметр tools.
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

            http_client = httpx.AsyncClient(proxy=settings.HTTP_PROXY if settings.HTTP_PROXY else None)
            try:
                client = AsyncOpenAI(
                    api_key=api_key_val,
                    base_url=base_url_val,
                    http_client=http_client
                )

                # Копируем messages для работы с tool calls
                working_messages = [{"role": "system", "content": config.system_instruction}] + messages.copy()

                request_params = {
                    "model": model_name_val,
                    "messages": working_messages,
                    "temperature": config.temperature,
                    "stream": config.is_stream
                }

                # Добавляем tools если они переданы
                if tools:
                    request_params["tools"] = tools
                    request_params["tool_choice"] = "auto"

                if config.is_json and not config.is_stream:
                    request_params["response_format"] = {"type": "json_object"}

                response = await client.chat.completions.create(**request_params)

                # Обработка стриминга
                if config.is_stream:
                    return self.create_stream_generator(response, http_client)

                # ЦИКЛ обработки tool calls
                max_tool_iterations = 10
                tool_iteration = 0
                
                while response.choices[0].finish_reason == "tool_calls" and tool_iteration < max_tool_iterations:
                    tool_iteration += 1
                    
                    # Добавляем ответ ИИ с tool_calls в историю
                    assistant_message = response.choices[0].message
                    working_messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Выполняем каждый запрошенный tool
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        print(f"ИИ вызывает tool: {function_name} с аргументами: {arguments}")
                        
                        # Выполняем функцию
                        if function_name == "search_metrics":
                            query_text = arguments.get("query", "")
                            limit = arguments.get("limit", 10)

                            try:
                                # Генерируем эмбеддинг для поискового запроса
                                query_embedding = await self.embedding_service.generate_embedding(query_text)

                                # Векторный поиск по эмбеддингам
                                result = await self.prod_repo.vector_search_metrics(
                                    query_embedding=query_embedding,
                                    limit=limit,
                                    is_custom=True  # Ищем только кастомные метрики
                                )

                                # Если векторный поиск не дал результатов, используем текстовый
                                if not result:
                                    result = await self.prod_repo.search_metrics(
                                        query=query_text,
                                        limit=limit
                                    )
                            except Exception as e:
                                print(f"Ошибка векторного поиска, используем текстовый: {e}")
                                # Fallback на текстовый поиск при ошибке
                                result = await self.prod_repo.search_metrics(
                                    query=query_text,
                                    limit=limit
                                )

                            result_str = json.dumps([{
                                "name": m.name,
                                "description": m.description,
                                "weight": m.weight
                            } for m in result], ensure_ascii=False)
                        else:
                            result_str = json.dumps({"error": f"Unknown function: {function_name}"})
                        
                        print(f"Результат tool {function_name}: {result_str[:200]}...")
                        
                        # Добавляем результат в историю
                        working_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str
                        })
                    
                    # ПРОДОЛЖАЕМ тот же запрос с новыми данными
                    request_params["messages"] = working_messages
                    response = await client.chat.completions.create(**request_params)

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
