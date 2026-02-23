from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Text, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from app.database import Base

class User(Base):
    """Пользователь системы"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    user_ranks: Mapped[List["UserRank"]] = relationship(back_populates="user")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class UserRank(Base):
    """Закрепление ролей за пользователями"""
    __tablename__ = "user_ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="user_ranks")
    rank: Mapped["Rank"] = relationship(back_populates="user_ranks")

    def __repr__(self):
        return f"<UserRank(user_id={self.user_id}, rank_id={self.rank_id})>"


class Rank(Base):
    """Роль пользователя в системе"""
    __tablename__ = "ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] # free, premium, ultra, worker, admin
    level: Mapped[int]

    rank_permissions: Mapped[List["RankPermission"]] = relationship(back_populates="rank")
    user_ranks: Mapped[List["UserRank"]] = relationship(back_populates="rank")

    def __repr__(self):
        return f"<Rank(id={self.id}, name='{self.name}', level={self.level})>"


class RankPermission(Base):
    """Права, закреплённые за ролью"""
    __tablename__ = "rank_permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))

    rank: Mapped["Rank"] = relationship(back_populates="rank_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="rank_permissions")

    def __repr__(self):
        return f"<RankPermission(rank_id={self.rank_id}, perm_id={self.permission_id})>"


class Permission(Base):
    """Конкретные права на действия"""
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(Text)

    rank_permissions: Mapped[List["RankPermission"]] = relationship(back_populates="permission")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"


class AiApiKey(Base):
    """Пользовательский API ключ от нейросети"""
    __tablename__ = "ai_api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider_url: Mapped[str]
    key: Mapped[str]
    model_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(default=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))

    user: Mapped["User"] = relationship(back_populates="sessions")