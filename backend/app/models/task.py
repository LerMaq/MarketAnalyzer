from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, Integer, DateTime, func, Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TaskStatus(str, Enum):
    pending = "pending"
    fetching = "fetching"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Task(Base):
    """Стек для хранения задач на анализ товара"""
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    ozon_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    worker_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLAEnum(TaskStatus, name="taskstatus", create_type=False),
        default=TaskStatus.pending,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now(), default=func.now()
    )

    def __repr__(self):
        return f"<Task(id={self.id}, ozon_id={self.ozon_id}, status='{self.status}')>"
