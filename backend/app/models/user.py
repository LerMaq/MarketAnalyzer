from datetime import date, datetime, timezone
from sqlalchemy import ForeignKey, Text, String, DateTime, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
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

    @hybrid_property
    def active_permissions(self) -> set[str]:
        """Возвращает набор активных прав пользователя."""
        active_perms = set()
        # expires_at хранится как naive (TIMESTAMP WITHOUT TIME ZONE)
        now = datetime.now()

        for ur in self.user_ranks:
            if ur.expires_at is None or ur.expires_at > now:
                for rp in ur.rank.rank_permissions:
                    active_perms.add(rp.permission.name)
        return active_perms

    @property
    def daily_limits(self) -> dict:
        """Находит максимальные лимиты среди всех ролей пользователя."""
        limits = {"analysis": 0, "chat": 0}
        # expires_at хранится как naive (TIMESTAMP WITHOUT TIME ZONE)
        now = datetime.now()

        for ur in self.user_ranks:
            if ur.expires_at is None or ur.expires_at > now:
                rank = ur.rank
                if rank.daily_analysis_limit is not None:
                    limits["analysis"] = max(limits["analysis"], rank.daily_analysis_limit)
                if rank.daily_chat_limit is not None:
                    limits["chat"] = max(limits["chat"], rank.daily_chat_limit)
        return limits

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
    name: Mapped[str] # free, premium, worker, moderator, admin
    level: Mapped[int]

    # Лимиты (могут быть null для ролей типа worker или moderator)
    daily_analysis_limit: Mapped[Optional[int]] = mapped_column(nullable=True)
    daily_chat_limit: Mapped[Optional[int]] = mapped_column(nullable=True)

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


class UserUsage(Base):
    """Статистика использования ресурсов по дням"""
    __tablename__ = "user_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    usage_date: Mapped[date] = mapped_column(default=lambda: datetime.now(timezone.utc).date())

    analysis_count: Mapped[int] = mapped_column(default=0)
    chat_count: Mapped[int] = mapped_column(default=0)

    # Индекс для быстрого поиска связки юзер + дата
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="idx_user_usage_date"),)