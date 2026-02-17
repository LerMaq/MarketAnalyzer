import json

from openai import AsyncOpenAI
import httpx
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.repositories import AiRepository, ProductRepository
from app.schemas import SAiAnalysisResponse


class AIService:
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

        full_prompt = await self._assemble_prompt(config.system_instruction, raw_content)

        # Слой 1: Попытки валидации
        for v_attempt in range(3):
            # Слой 2: Попытки перебора моделей
            for m_attempt in range(10):
                model_record = await self.repo.get_best_model_with_key()
                if not model_record:
                    raise HTTPException(status_code=503, detail="Нет доступных рабочих моделей ИИ")

                try:
                    raw_response = await self._execute(model_record, config, full_prompt)
                    try:
                        validated_data = SAiAnalysisResponse.model_validate(raw_response)
                        return validated_data
                    except ValidationError as ve:
                        print(f"Попытка валидации {v_attempt + 1} провалена: {ve}")
                        break

                except Exception as e:
                    # Ошибка API (тайм-аут, 429, 500 от провайдера)
                    print(f"Ошибка API модели {model_record.model_name}: {e}")
                    await self.repo.mark_model_broken(model_record.id)
                    continue  # Следующая модель

        raise HTTPException(status_code=500, detail="ИИ не смог выдать валидный результат после всех попыток")

    async def _execute(self, model_record, config, prompt: str) -> dict:
        async with httpx.AsyncClient(proxy="http://127.0.0.1:2080") as http_client:
            client = AsyncOpenAI(
                api_key=model_record.api_key.key,
                base_url=model_record.api_key.provider_url,
                http_client=http_client
            )

            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": config.system_instruction},
                {"role": "user", "content": prompt}
            ]

            response = await client.chat.completions.create(
                model=model_record.model_name,
                messages=messages,
                temperature=config.temperature,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("ИИ вернул пустой ответ")

            return json.loads(content)