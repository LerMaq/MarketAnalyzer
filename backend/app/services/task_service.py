from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from app.repositories import TaskRepository, UserRepository
from app.utils import extract_ozon_id
from app.models.user import User
from app.models.worker import Worker
from app.models.task import TaskStatus
from app.schemas.task import (
    ALLOWED_REVIEW_COUNTS,
    STask,
    STaskAddedResponse,
    STaskWorkerTake,
    STaskWorkerData,
)

from .ai_service import AIService
from .product_service import ProductService
from .user_service import UserService


class TaskService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db

    async def add_new_task(
        self,
        url_or_id: str,
        user: Optional[User],
        review_count: int = 50,
    ) -> STaskAddedResponse:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "task.analysis" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для запуска анализа")

        if review_count not in ALLOWED_REVIEW_COUNTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"review_count должен быть одним из {ALLOWED_REVIEW_COUNTS}",
            )

        if review_count != 50 and "task.priority_queue" not in user.active_permissions:
            review_count = 50

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
            return STaskAddedResponse(status=existing.status, task_id=existing.id)

        task = await self.task_repo.create(
            ozon_id, user_id=user.id, review_count=review_count
        )
        await self.user_repo.increment_usage(user.id, analysis=True)

        return STaskAddedResponse(status=task.status, task_id=task.id)

    async def take_task_for_worker(
        self, worker: Optional[Worker]
    ) -> Optional[STaskWorkerTake]:
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или неактивный X-Worker-Token",
            )

        # 1. Первая быстрая проверка (без ожидания)
        task = await self.task_repo.get_next_pending_and_assign(worker.id)
        if task:
            return STaskWorkerTake(
                task_id=task.id,
                ozon_id=task.ozon_id,
                review_count=task.review_count,
            )

        # 2. Если пусто — создаем отдельное соединение для ожидания
        # Используем raw_connection из того же движка, но не через сессию
        async with self.db.bind.connect() as conn:
            # Получаем доступ к низкоуровневому драйверу (asyncpg)
            raw_conn = await conn.get_raw_connection()
            driver_conn = raw_conn.driver_connection

            queue = asyncio.Queue()

            def on_notification(*args):
                queue.put_nowait(True)

            # Подписываемся на канал
            await driver_conn.add_listener("new_task_channel", on_notification)

            try:
                # Сразу после подписки проверяем ЕЩЕ РАЗ (чтобы не проспать задачу)
                task = await self.task_repo.get_next_pending_and_assign(worker.id)
                if task:
                    return STaskWorkerTake(
                        task_id=task.id,
                        ozon_id=task.ozon_id,
                        review_count=task.review_count,
                    )

                # Ждем уведомления ровно 25 секунд
                try:
                    await asyncio.wait_for(queue.get(), timeout=25.0)
                    # Как только "пинг" пришел — возвращаемся в основную сессию за задачей
                    task = await self.task_repo.get_next_pending_and_assign(worker.id)
                    if task:
                        return STaskWorkerTake(
                            task_id=task.id,
                            ozon_id=task.ozon_id,
                            review_count=task.review_count,
                        )
                except asyncio.TimeoutError:
                    return None  # Выходим по тайм-ауту, воркер перезайдет
            finally:
                await driver_conn.remove_listener("new_task_channel", on_notification)

        return None

    async def get_task_info(self, task_id: int) -> STask:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        return STask.model_validate(task)

    async def process_worker_complete(
        self,
        task_id: int,
        worker_data: STaskWorkerData,
        background_tasks,
        worker: Optional[Worker],
    ) -> dict:
        """Проверить raw_content, обработать повторную попытку/сбой или добавить анализ ИИ в очередь."""
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или неактивный X-Worker-Token",
            )

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

        if task.worker_id != worker.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Завершить задачу может только воркер, который её взял",
            )

        if task.status != TaskStatus.fetching:
            return {
                "status": "ignored", 
                "message": f"Задача уже находится в статусе {task.status.value}, обработка не требуется"
            }

        report_text = worker_data.raw_content
        if len(report_text) < 5000:
            retry_count = await self.task_repo.increment_retry(task_id)
            if retry_count < 3:
                await self.task_repo.update_status(
                    task_id, TaskStatus.pending, clear_worker=True
                )
                return {"status": "pending", "message": "Недостаточно данных, задача возвращена в очередь"}
            else:
                await self.task_repo.update_status(task_id, TaskStatus.failed)
                user_service = UserService(self.db)
                await user_service.refund_balance(task.user_id)
                return {"status": "failed", "message": "Превышено число попыток, возврат на баланс"}

        await self.task_repo.update_status(task_id, TaskStatus.processing)
        background_tasks.add_task(self.run_ai_analysis_and_finalize, task_id, worker_data)
        return {"status": "processing", "message": "Данные приняты, анализ запущен в фоне"}

    async def run_ai_analysis_and_finalize(self, task_id: int, worker_data: STaskWorkerData):
        """Фоновый процесс (права проверены на этапе вызова эндпоинта)"""
        task = await self.task_repo.get_by_id(task_id)
        if not task: return

        ai_service = AIService(self.db)
        product_service = ProductService(self.db)

        try:
            # Анализ через системные промпты и модели
            ai_result = await ai_service.get_report_completion(worker_data.raw_content)

            product = await product_service.create_full_product(
                ozon_id=task.ozon_id,
                raw_content=worker_data.raw_content,
                ai_result=ai_result,
            )

            await self.task_repo.update_status(
                task_id, status=TaskStatus.completed, product_id=product.id
            )
        except Exception:
            await self.task_repo.update_status(task_id, status=TaskStatus.failed)

    async def get_user_tasks(self, user_id: int) -> List[STask]:
        tasks = await self.task_repo.get_by_user_id(user_id)
        return [STask.model_validate(task) for task in tasks]

    async def process_stale_fetching_tasks(self) -> None:
        """Сбрасывает застрявшие fetching задачи: retry++, pending, clear worker. При 3-й попытке — failed + refund."""
        stale = await self.task_repo.get_stale_fetching_tasks(stale_seconds=80)
        for task in stale:
            current = await self.task_repo.get_by_id(task.id)
            if not current or current.status != TaskStatus.fetching:
                continue
            new_retry = await self.task_repo.increment_retry(task.id)
            if new_retry >= 3:
                await self.task_repo.update_status(task.id, TaskStatus.failed, clear_worker=True)
                user_service = UserService(self.db)
                await user_service.refund_balance(task.user_id)
            else:
                await self.task_repo.update_status(task.id, TaskStatus.pending, clear_worker=True)