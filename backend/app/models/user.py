from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    ranks: Mapped[List["UserRank"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"

class AiApiKey(Base):
    __tablename__ = "ai_api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider_url: Mapped[str]
    key: Mapped[str]
    model_name: Mapped[str]

    def __repr__(self):
        return f"<AiApiKey(id={self.id}, user_id={self.user_id}, model='{self.model_name}')>"