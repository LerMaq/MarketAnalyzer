from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import joinedload
from typing import List
from app.models.ai import SystemAiModel, AiConfig, SystemAiApiKey
from app.schemas import SModelPreset


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

    async def create_system_key_with_models(self, key_data: dict, models: List[SModelPreset]):
        new_system_key = SystemAiApiKey(**key_data)
        self.db.add(new_system_key)
        await self.db.flush()

        for m_data in models:
            new_model = SystemAiModel(
                **m_data.model_dump(),
                api_key_id=new_system_key.id
            )
            self.db.add(new_model)

        await self.db.commit()
        await self.db.refresh(new_system_key)
        return new_system_key

    async def get_config_by_name(self, name: str):
        query = select(AiConfig).where(AiConfig.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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