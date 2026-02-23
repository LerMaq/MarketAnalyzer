from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime

from app.models.user import User, Session, UserRank, Rank, RankPermission, Permission
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