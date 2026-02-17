from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import TaskRepository
from app.utils import extract_ozon_id
from app.schemas import STask, STaskAddedResponse, STaskWorkerTake, STaskWorkerData

from .ai_service import AIService
from .product_service import ProductService


class TaskService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)
        self.db = db

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

    async def run_ai_analysis_and_finalize(self, task_id: int, worker_data: STaskWorkerData):
        """Выполняется в фоне после ответа воркеру"""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return

        ai_service = AIService(self.db)
        product_service = ProductService(self.db)


        # 1. Получаем строго валидированный JSON через каскад попыток
        ai_result = await ai_service.get_report_completion(worker_data.raw_content)

        # 2. Сохраняем продукт (передаем и сырой текст, и объект анализа)
        product = await product_service.create_full_product(
            ozon_id=task.ozon_id,
            raw_content=worker_data.raw_content,
            ai_result=ai_result
        )

        # 3. Закрываем задачу
        await self.task_repo.update_status(task_id, status="completed", product_id=product.id)
        print(f"Задача {task_id} успешно завершена. Продукт ID: {product.id}")

