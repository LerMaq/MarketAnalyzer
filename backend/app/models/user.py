from datetime import datetime
from sqlalchemy import ForeignKey, Text
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

    ranks: Mapped[List["UserRank"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"

class AiApiKey(Base):
    """Пользовательский API ключ от нейросети"""
    __tablename__ = "ai_api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider_url: Mapped[str]
    key: Mapped[str]
    model_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)

class Rank(Base):
    """Роль пользователя в системе"""
    __tablename__ = "ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] # free, premium, ultra, worker, admin
    level: Mapped[int]

    permissions: Mapped[List["RankPermission"]] = relationship(back_populates="rank")
    users: Mapped[List["UserRank"]] = relationship(back_populates="rank")

    def __repr__(self):
        return f"<Rank(id={self.id}, name='{self.name}', level={self.level})>"

class UserRank(Base):
    """Закрепление ролей за пользователями"""
    __tablename__ = "user_ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="ranks")
    rank: Mapped["Rank"] = relationship(back_populates="users")

    def __repr__(self):
        return f"<UserRank(user_id={self.user_id}, rank_id={self.rank_id})>"

class Permission(Base):
    """Конкретные права на действия"""
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(Text)

    ranks: Mapped[List["RankPermission"]] = relationship(back_populates="permission")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class RankPermission(Base):
    """Права, закреплённые за ролью"""
    __tablename__ = "rank_permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))

    rank: Mapped["Rank"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="ranks")

    def __repr__(self):
        return f"<RankPermission(rank_id={self.rank_id}, perm_id={self.permission_id})>"