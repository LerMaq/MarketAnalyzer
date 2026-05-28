import secrets
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.worker import Worker


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


class WorkerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, created_by_user_id: Optional[int]) -> Worker:
        worker = Worker(
            name=name,
            token=_generate_token(),
            is_active=True,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(worker)
        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def list_all(self) -> List[Worker]:
        result = await self.db.execute(select(Worker).order_by(Worker.id.asc()))
        return list(result.scalars().all())

    async def get_by_id(self, worker_id: int) -> Optional[Worker]:
        return await self.db.get(Worker, worker_id)

    async def get_by_token(self, token: str) -> Optional[Worker]:
        result = await self.db.execute(select(Worker).where(Worker.token == token))
        return result.scalar_one_or_none()

    async def regenerate_token(self, worker_id: int) -> Optional[Worker]:
        worker = await self.db.get(Worker, worker_id)
        if not worker:
            return None
        worker.token = _generate_token()
        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def update_fields(
        self,
        worker_id: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Worker]:
        values: dict = {}
        if name is not None:
            values["name"] = name
        if is_active is not None:
            values["is_active"] = is_active
        if not values:
            return await self.db.get(Worker, worker_id)
        await self.db.execute(
            update(Worker).where(Worker.id == worker_id).values(**values)
        )
        await self.db.commit()
        return await self.db.get(Worker, worker_id)

    async def delete(self, worker_id: int) -> bool:
        worker = await self.db.get(Worker, worker_id)
        if not worker:
            return False
        await self.db.delete(worker)
        await self.db.commit()
        return True
