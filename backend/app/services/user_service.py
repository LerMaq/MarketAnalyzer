from datetime import datetime, timezone
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import SUserFullProfile


class UserService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    async def get_my_profile(self, user: User) -> SUserFullProfile:
        # Собираем права
        perms = set()
        now = datetime.now(timezone.utc)

        for ur in user.user_ranks:
            if ur.expires_at is None or ur.expires_at > now:
                for rp in ur.rank.rank_permissions:
                    perms.add(rp.permission.name)

        # Подготовка данных для схемы
        profile_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "permissions": list(perms)
        }

        return SUserFullProfile.model_validate(profile_data)