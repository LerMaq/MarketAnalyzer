from typing import Optional

from fastapi import HTTPException, status

from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import SUserFullProfile, SSimpleMessage, SUserLimits, SUserUsage
from app.auth.security import hash_password, verify_password


class UserService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    def _get_tariff(self, user: User) -> str:
        # expires_at хранится как naive (TIMESTAMP WITHOUT TIME ZONE)
        now = datetime.now()
        rank_names = {
            ur.rank.name for ur in user.user_ranks
            if ur.rank and (ur.expires_at is None or ur.expires_at > now)
        }
        if "premium" in rank_names:
            return "premium"
        return "free"

    async def get_my_profile(self, user: Optional[User]) -> SUserFullProfile:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        perms = user.active_permissions
        limits = user.daily_limits
        usage = await self.repo.get_or_create_today_usage(user.id)
        tariff = self._get_tariff(user)

        profile_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "permissions": list(perms),
            "tariff": tariff,
            "limits": SUserLimits(analysis=limits["analysis"], chat=limits["chat"]),
            "usage": SUserUsage(analysis=usage.analysis_count, chat=usage.chat_count),
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
        limits = updated.daily_limits
        usage = await self.repo.get_or_create_today_usage(updated.id)
        tariff = self._get_tariff(updated)

        profile_data = {
            "id": updated.id,
            "name": updated.name,
            "email": updated.email,
            "permissions": list(perms),
            "tariff": tariff,
            "limits": SUserLimits(analysis=limits["analysis"], chat=limits["chat"]),
            "usage": SUserUsage(analysis=usage.analysis_count, chat=usage.chat_count),
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

    async def subscribe_premium(self, user: Optional[User], amount: int) -> SSimpleMessage:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if amount < 300:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Минимальная сумма 300 ₽")
        await self.repo.upgrade_to_premium(user.id, days=30)
        return SSimpleMessage.model_validate({"detail": "Подписка оформлена"})

    async def delete_my_account(self, user: Optional[User]) -> SSimpleMessage:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        await self.repo.delete_user(user.id)

        return SSimpleMessage.model_validate({"detail": "Account deleted"})
