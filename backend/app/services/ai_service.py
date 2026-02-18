import json

from openai import AsyncOpenAI
import httpx

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

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

        standards_text = "\n".join([f"- {m.name}: {m.description}" for m in standards])
        customs_text = "\n".join([f"- {m.name}: {m.description}" for m in customs])

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

        # Слой 1: Попытки валидации
        for v_attempt in range(3):
            # Слой 2: Попытки перебора моделей
            for m_attempt in range(10):
                model_record = await self.repo.get_best_model_with_key()
                if not model_record:
                    raise HTTPException(status_code=503, detail="Нет доступных рабочих моделей ИИ")

                try:
                    raw_response = await self._execute(model_record, config, messages)

                    try:
                        validated_data = SAiAnalysisResponse.model_validate(raw_response)
                        return validated_data
                    except ValidationError as ve:
                        print(f"Попытка валидации {v_attempt + 1} провалена: {ve}")
                        # Если JSON сломан, возможно стоит добавить подсказку для ИИ в следующую попытку
                        break

                except Exception as e:
                    print(f"Ошибка API модели {model_record.model_name}: {e}")
                    await self.repo.mark_model_broken(model_record.id)
                    continue

        raise HTTPException(status_code=500, detail="ИИ не смог выдать валидный результат")

    async def _execute(self, model_record, config, messages):

        http_client = httpx.AsyncClient(proxy="http://127.0.0.1:2080")

        client = AsyncOpenAI(
            api_key=model_record.api_key.key,
            base_url=model_record.api_key.provider_url,
            http_client=http_client
        )

        full_messages = [
                            {"role": "system", "content": config.system_instruction}
                        ] + messages

        request_params = {
            "model": model_record.model_name,
            "messages": full_messages,
            "temperature": config.temperature,
            "stream": config.is_stream
        }

        if config.is_json and not config.is_stream:
            request_params["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**request_params)

        if config.is_stream:
            async def stream_generator():
                try:
                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                finally:
                    # Закрываем клиенты после завершения стрима
                    await http_client.aclose()

            return stream_generator()

        result = response.choices[0].message.content
        await http_client.aclose()
        return json.loads(result) if config.is_json else result

    async def add_key_with_preset(self, data: SSystemAiKeyCreate):
        template = self.PRESET_TEMPLATES.get(data.preset.value)

        if data.preset == ApiProviderPreset.custom:
            url = data.provider_url
        else:
            url = template["url"] if template else data.provider_url

        if url == "string" or not url:
            raise HTTPException(status_code=400, detail="Укажите корректный URL или выберите пресет")

        key_payload = {
            "key": data.key,
            "provider_url": url
        }

        models = template["models"] if template else []
        return await self.repo.create_system_key_with_models(key_payload, models)