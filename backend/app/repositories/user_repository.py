from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timezone, timedelta

from app.models.user import User, Session, UserRank, Rank, RankPermission, Permission, UserUsage
from app.auth.security import get_token_hash


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_session(self, session_data: dict):
        session_data['created_at'] = datetime.utcnow()
        new_session = Session(**session_data)
        self.db.add(new_session)
        await self.db.commit()

    async def get_user_by_session_token(self, token: str) -> Optional[User]:
        t_hash = get_token_hash(token)
        now = datetime.utcnow()

        query = (
            select(Session)
            .options(
                joinedload(Session.user)
                .selectinload(User.user_ranks)
                .joinedload(UserRank.rank)
                .selectinload(Rank.rank_permissions)
                .joinedload(RankPermission.permission)
            )
            .where(
                Session.token_hash == t_hash,
                Session.is_active == True,
                Session.expires_at > now
            )
        )
        result = await self.db.execute(query)
        session_obj = result.scalar_one_or_none()
        return session_obj.user if session_obj else None

    async def deactivate_session(self, token: str):
        t_hash = get_token_hash(token)
        await self.db.execute(
            update(Session).where(Session.token_hash == t_hash).values(is_active=False)
        )
        await self.db.commit()

    async def get_or_create_today_usage(self, user_id: int) -> UserUsage:
        today = datetime.now(timezone.utc).date()

        query = select(UserUsage).where(
            UserUsage.user_id == user_id,
            UserUsage.usage_date == today
        )
        result = await self.db.execute(query)
        usage = result.scalar_one_or_none()

        if not usage:
            usage = UserUsage(user_id=user_id, usage_date=today)
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)

        return usage

    async def increment_usage(self, user_id: int, analysis: bool = False, chat: bool = False):
        today = datetime.now(timezone.utc).date()
        update_data = {}

        if analysis:
            update_data[UserUsage.analysis_count] = UserUsage.analysis_count + 1
        if chat:
            update_data[UserUsage.chat_count] = UserUsage.chat_count + 1

        if not update_data:
            return

        query = update(UserUsage).where(
            UserUsage.user_id == user_id,
            UserUsage.usage_date == today
        ).values(update_data)

        await self.db.execute(query)
        await self.db.commit()

    async def refund_analysis(self, user_id: int) -> None:
        """Уменьшить значение analysis_count на 1 за сегодня (минимум 0)"""
        today = datetime.now(timezone.utc).date()
        await self.db.execute(
            update(UserUsage)
            .where(
                UserUsage.user_id == user_id,
                UserUsage.usage_date == today,
                UserUsage.analysis_count > 0,
            )
            .values(analysis_count=UserUsage.analysis_count - 1)
        )
        await self.db.commit()

    async def update_user(self, user_id: int, update_data: dict) -> User:
        await self.db.execute(update(User).where(User.id == user_id).values(**update_data))
        await self.db.commit()

        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one()

    async def change_password(self, user_id: int, new_hashed_password: str):
        await self.db.execute(update(User).where(User.id == user_id).values(password=new_hashed_password))
        await self.db.commit()

    async def upgrade_to_premium(self, user_id: int, days: int = 30):
        res = await self.db.execute(select(Rank).where(Rank.name == "premium"))
        premium_rank = res.scalar_one_or_none()
        if not premium_rank:
            raise ValueError("Rank 'premium' not found in database")
        # БД хранит TIMESTAMP WITHOUT TIME ZONE — нужен naive datetime
        expires_at = (datetime.now(timezone.utc) + timedelta(days=days)).replace(tzinfo=None)
        ur = UserRank(user_id=user_id, rank_id=premium_rank.id, expires_at=expires_at)
        self.db.add(ur)
        await self.db.commit()

    async def delete_user(self, user_id: int):
        # Удаляем все сессии пользователя
        await self.db.execute(delete(Session).where(Session.user_id == user_id))
        # Удаляем статистику использования
        await self.db.execute(delete(UserUsage).where(UserUsage.user_id == user_id))
        # Удаляем связи с ролями
        await self.db.execute(delete(UserRank).where(UserRank.user_id == user_id))
        # Удаляем пользователя
        user = await self.db.get(User, user_id)
        if user:
            await self.db.delete(user)
        await self.db.commit()