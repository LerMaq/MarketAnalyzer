from typing import Optional

from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import SUserFullProfile


class UserService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    async def get_my_profile(self, user: Optional[User]) -> SUserFullProfile:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        # Собираем права
        perms = user.active_permissions

        # Подготовка данных для схемы
        profile_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "permissions": list(perms)
        }

        return SUserFullProfile.model_validate(profile_data)