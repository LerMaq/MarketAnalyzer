from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    ozon_id: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str]

    def __repr__(self):
        return f"<Task(id={self.id}, ozon_id={self.ozon_id}, status='{self.status}')>"