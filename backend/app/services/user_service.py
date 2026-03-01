from typing import Optional

from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import SUserFullProfile, SSimpleMessage
from app.auth.security import hash_password, verify_password


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

    async def update_my_profile(self, user: Optional[User], update_data: dict) -> SUserFullProfile:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # Отфильтруем поля, которые можно обновлять
        allowed = {k: v for k, v in update_data.items() if k in ("name",) and v is not None}

        if allowed:
            updated = await self.repo.update_user(user.id, allowed)
        else:
            updated = user

        perms = updated.active_permissions

        profile_data = {
            "id": updated.id,
            "name": updated.name,
            "email": updated.email,
            "permissions": list(perms)
        }

        return SUserFullProfile.model_validate(profile_data)

    async def change_my_password(self, user: Optional[User], payload: dict) -> SSimpleMessage:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        old = payload.get('old_password')
        new = payload.get('new_password')

        if not old or not new:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old and new passwords required")

        if not verify_password(old, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

        hashed = hash_password(new)
        await self.repo.change_password(user.id, hashed)

        return SSimpleMessage.model_validate({"detail": "ok"})