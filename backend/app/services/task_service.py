from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import TaskRepository
from app.utils import extract_ozon_id
from app.schemas import STask, STaskAddedResponse, STaskWorkerTake


class TaskService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)

    async def add_new_task(self, url_or_id: str) -> STaskAddedResponse:
        try:
            ozon_id = extract_ozon_id(url_or_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        existing = await self.task_repo.get_active_by_ozon_id(ozon_id)
        if existing:
            return STaskAddedResponse(status="already_exists", task_id=existing.id)

        task = await self.task_repo.create(ozon_id, user_id=1)  # Пока статика
        return STaskAddedResponse(status="added", task_id=task.id)

    async def get_task_info(self, task_id: int) -> STask:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return STask.model_validate(task)

    async def take_task_for_worker(self) -> Optional[STaskWorkerTake]:
        task = await self.task_repo.get_next_pending()
        if not task:
            return None
        await self.task_repo.update_status(task.id, "processing")
        return STaskWorkerTake(task_id=task.id, ozon_id=task.ozon_id)