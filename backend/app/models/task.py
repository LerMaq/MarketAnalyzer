from typing import Optional
from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Task(Base):
    """Стек для хранения задач на анализ товара"""
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    ozon_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    worker_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str]

    def __repr__(self):
        return f"<Task(id={self.id}, ozon_id={self.ozon_id}, status='{self.status}')>"