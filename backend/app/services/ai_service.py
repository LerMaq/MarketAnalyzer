import json
from typing import Optional

from openai import AsyncOpenAI
import httpx

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models import User
from app.repositories import AiRepository, ProductRepository
from app.schemas import SAiAnalysisResponse, SModelPreset, SSystemAiKeyCreate, ApiProviderPreset


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

    async def _assemble_prompt(self, config_instruction: str, raw_content: str) -> str:
        """Собирает финальный промпт со справочником метрик"""
        standards = await self.prod_repo.get_standard_metrics()
        customs = await self.prod_repo.get_random_custom_metrics(30)

        standards_text = "\n".join([f"- {m.name}: {m.description}. Вес метрики: {m.weight}" for m in standards])
        customs_text = "\n".join([f"- {m.name}: {m.description}. Вес метрики: {m.weight}" for m in customs])

        full_prompt = (
            f"{config_instruction}\n\n"
            f"СПРАВОЧНИК МЕТРИК, ИМЕЮЩИХСЯ В БАЗЕ ДАННЫХ:\n\n"
            f"Стандартные метрики (is_custom: false) — выбери любые 5:\n{standards_text}\n\n"
            f"Метрики, ранее созданные нейросетью (is_custom: true) — можешь использовать некоторые "
            f"отсюда, если они подходят. Если нет — придумай новую:\n{customs_text}\n\n"
            f"ДАННЫЕ ТОВАРА ДЛЯ АНАЛИЗА:\n{raw_content}"
        )
        return full_prompt

    async def get_report_completion(self, raw_content: str) -> SAiAnalysisResponse:
        config = await self.repo.get_config("report_generation")
        if not config:
            raise HTTPException(status_code=500, detail="AI Config 'report_generation' not found")

        messages = [{"role": "user", "content": raw_content}]

        # Попытки валидации
        for v_attempt in range(3):
            try:
                raw_response = await self.execute(config=config, messages=messages)
                validated_data = SAiAnalysisResponse.model_validate(raw_response)
                return validated_data

            except ValidationError as ve:
                print(f"Попытка валидации {v_attempt + 1} провалена: {ve}")
                continue
            except Exception as e:
                # Если даже execute поднял исключение после всех переборов
                raise HTTPException(status_code=503, detail=f"Критическая ошибка ИИ: {str(e)}")

        raise HTTPException(status_code=500, detail="ИИ не смог выдать валидный результат после нескольких попыток")

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

            http_client = httpx.AsyncClient(proxy="http://127.0.0.1:2080")
            try:
                client = AsyncOpenAI(
                    api_key=api_key_val,
                    base_url=base_url_val,
                    http_client=http_client
                )

                request_params = {
                    "model": model_name_val,
                    "messages": [{"role": "system", "content": config.system_instruction}] + messages,
                    "temperature": config.temperature,
                    "stream": config.is_stream
                }

                if config.is_json and not config.is_stream:
                    request_params["response_format"] = {"type": "json_object"}

                response = await client.chat.completions.create(**request_params)

                # Обработка стриминга
                if config.is_stream:
                    return self.create_stream_generator(response, http_client)

                # Обработка обычного ответа
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
        async def stream_generator():
            try:
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            finally:
                await http_client.aclose()

        return stream_generator()

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
