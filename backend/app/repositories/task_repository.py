from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from typing import Optional, List

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ozon_id: int, user_id: int) -> Task:
        new_task = Task(ozon_id=ozon_id, user_id=user_id, status="pending")
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)
        return new_task

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        return await self.db.get(Task, task_id)

    async def get_active_by_ozon_id(self, ozon_id: int) -> Optional[Task]:
        query = select(Task).where(Task.ozon_id == ozon_id, Task.status.in_(["pending", "processing"]))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_next_pending(self) -> Optional[Task]:
        query = select(Task).where(Task.status == "pending").order_by(Task.id.asc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_status(self, task_id: int, status: str, product_id: Optional[int] = None):
        query = update(Task).where(Task.id == task_id).values(status=status, product_id=product_id)
        await self.db.execute(query)
        await self.db.commit()

    async def get_by_user_id(self, user_id: int) -> List[Task]:
        query = select(Task).where(Task.user_id == user_id).order_by(Task.id.desc())
        result = await self.db.execute(query)
        return result.scalars().all()