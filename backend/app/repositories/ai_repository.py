from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import joinedload
from app.models.ai import SystemAiModel, AiConfig


class AiRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_best_model_with_key(self) -> SystemAiModel:
        """Выбирает лучшую рабочую модель вместе с ключом"""
        query = (
            select(SystemAiModel)
            .options(joinedload(SystemAiModel.api_key))
            .where(SystemAiModel.works == True)
            .order_by(desc(SystemAiModel.priority))
            .limit(1)
        )
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        # Если рабочих моделей не осталось — сбрасываем всё
        if not model:
            await self.reset_all_models()
            return await self.get_best_model_with_key()

        return model

    async def mark_model_broken(self, model_id: int):
        """Помечает модель как нерабочую"""
        query = update(SystemAiModel).where(SystemAiModel.id == model_id).values(works=False)
        await self.db.execute(query)
        await self.db.commit()

    async def reset_all_models(self):
        """Сброс всех моделей в состояние works=True"""
        query = update(SystemAiModel).values(works=True)
        await self.db.execute(query)
        await self.db.commit()

    async def get_config(self, name: str) -> AiConfig:
        result = await self.db.execute(select(AiConfig).where(AiConfig.name == name))
        return result.scalar_one_or_none()