from typing import Optional

from fastapi import Depends, HTTPException, Request
from app.database import get_db
from app.models import User, Worker
from app.repositories.user_repository import UserRepository
from app.repositories.worker_repository import WorkerRepository
from datetime import datetime, timezone


async def get_current_user(request: Request, db=Depends(get_db)) -> Optional[User]:
    """Универсальный поиск пользователя. Если не нашел — возвращает None."""
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    else:
        token = request.cookies.get("session_token")

    if not token:
        return None

    repo = UserRepository(db)
    return await repo.get_user_by_session_token(token)


async def get_current_worker(request: Request, db=Depends(get_db)) -> Optional[Worker]:
    """Авторизация воркера-скрапера через заголовок X-Worker-Token."""
    token = request.headers.get("X-Worker-Token")
    if not token:
        return None

    repo = WorkerRepository(db)
    worker = await repo.get_by_token(token.strip())
    if worker is None or not worker.is_active:
        return None
    return worker
