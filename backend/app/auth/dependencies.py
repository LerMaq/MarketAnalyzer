from typing import Optional

from fastapi import Depends, HTTPException, Request
from app.database import get_db
from app.models import User
from app.repositories.user_repository import UserRepository
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
