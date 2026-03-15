from datetime import datetime, timedelta
from sqlalchemy import select, update, or_, case, exists, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskStatus
from app.models.user import UserRank, Rank, RankPermission, Permission
from typing import Optional, List, Any


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ozon_id: int, user_id: int) -> Task:
        new_task = Task(ozon_id=ozon_id, user_id=user_id, status=TaskStatus.pending)
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)
        return new_task

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        return await self.db.get(Task, task_id)

    async def get_active_by_ozon_id(self, ozon_id: int) -> Optional[Task]:
        active_statuses = [
            TaskStatus.pending,
            TaskStatus.fetching,
            TaskStatus.processing,
        ]
        query = select(Task).where(
            Task.ozon_id == ozon_id,
            Task.status.in_(active_statuses),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_next_pending_and_assign(self, worker_id: int) -> Optional[Task]:
        """Атомарно получает задачу и назначает её воркеру."""
        now = datetime.now()
        priority_exists = exists().where(
            and_(
                UserRank.user_id == Task.user_id,
                or_(UserRank.expires_at.is_(None), UserRank.expires_at > now),
                Rank.id == UserRank.rank_id,
                RankPermission.rank_id == Rank.id,
                Permission.id == RankPermission.permission_id,
                Permission.name == "task.priority_queue",
            )
        ).correlate(Task)

        order_priority = case((priority_exists, 0), else_=1)
        
        # 1. Находим подходящую задачу
        query = (
            select(Task)
            .where(Task.status == TaskStatus.pending)
            .order_by(order_priority, Task.id.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task:
            # 2. Обновляем её, присваивая worker_id
            task.worker_id = worker_id
            task.status = TaskStatus.fetching
            await self.db.commit()
            await self.db.refresh(task)
            return task
        
        return None

    async def update_status(
        self,
        task_id: int,
        status: str | TaskStatus,
        product_id: Optional[int] = None,
        worker_id: Optional[int] = None,
        clear_worker: bool = False,
    ):
        values: dict[str, Any] = {"status": status}
        if product_id is not None:
            values["product_id"] = product_id
        if clear_worker:
            values["worker_id"] = None
        elif worker_id is not None:
            values["worker_id"] = worker_id
        query = update(Task).where(Task.id == task_id).values(**values)
        await self.db.execute(query)
        await self.db.commit()

    async def get_stale_fetching_tasks(self, stale_seconds: int = 80) -> List[Task]:
        """Возвращает задачи в статусе fetching, у которых updated_at старше stale_seconds секунд."""
        threshold = func.now() - timedelta(seconds=stale_seconds)
        query = select(Task).where(
            Task.status == TaskStatus.fetching,
            Task.updated_at < threshold,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def increment_retry(self, task_id: int) -> int:
        """Увеличить retry_count на 1 и вернуть новое значение."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id).with_for_update()
        )
        task = result.scalar_one_or_none()
        if not task:
            return 0
        new_count = task.retry_count + 1
        await self.db.execute(
            update(Task).where(Task.id == task_id).values(retry_count=new_count)
        )
        await self.db.commit()
        return new_count

    async def get_by_user_id(self, user_id: int) -> List[Task]:
        query = select(Task).where(Task.user_id == user_id).order_by(Task.id.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
