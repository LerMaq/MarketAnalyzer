from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import TaskRepository, UserRepository
from app.utils import extract_ozon_id
from app.models.user import User
from app.schemas.task import STask, STaskAddedResponse, STaskWorkerTake, STaskWorkerData

from .ai_service import AIService
from .product_service import ProductService

class TaskService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db

    async def add_new_task(self, url_or_id: str, user: Optional[User]) -> STaskAddedResponse:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "task.analysis" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для запуска анализа")

        usage = await self.user_repo.get_or_create_today_usage(user.id)
        max_limit = user.daily_limits.get("analysis", 0)
        
        if usage.analysis_count >= max_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail=f"Дневной лимит анализа ({max_limit}) исчерпан"
            )

        try:
            ozon_id = extract_ozon_id(url_or_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        existing = await self.task_repo.get_active_by_ozon_id(ozon_id)
        if existing:
            return STaskAddedResponse(status="already_exists", task_id=existing.id)

        task = await self.task_repo.create(ozon_id, user_id=user.id)
        await self.user_repo.increment_usage(user.id, analysis=True)
        
        return STaskAddedResponse(status="added", task_id=task.id)

    async def verify_worker_access(self, user: Optional[User]):
        """Вспомогательный метод для проверки прав воркера"""
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "task.worker" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для воркеров")

    async def take_task_for_worker(self, user: Optional[User]) -> Optional[STaskWorkerTake]:
        await self.verify_worker_access(user)
        
        task = await self.task_repo.get_next_pending()
        if not task:
            return None
        await self.task_repo.update_status(task.id, "processing")
        return STaskWorkerTake(task_id=task.id, ozon_id=task.ozon_id)

    async def get_task_info(self, task_id: int) -> STask:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        return STask.model_validate(task)

    async def run_ai_analysis_and_finalize(self, task_id: int, worker_data: STaskWorkerData):
        """Фоновый процесс (права проверены на этапе вызова эндпоинта)"""
        task = await self.task_repo.get_by_id(task_id)
        if not task: return

        ai_service = AIService(self.db)
        product_service = ProductService(self.db)

        # Анализ через системные промпты и модели
        ai_result = await ai_service.get_report_completion(worker_data.raw_content)

        product = await product_service.create_full_product(
            ozon_id=task.ozon_id,
            raw_content=worker_data.raw_content,
            ai_result=ai_result
        )

        await self.task_repo.update_status(task_id, status="completed", product_id=product.id)

    async def get_user_tasks(self, user_id: int) -> List[STask]:
        tasks = await self.task_repo.get_by_user_id(user_id)
        return [STask.model_validate(task) for task in tasks]