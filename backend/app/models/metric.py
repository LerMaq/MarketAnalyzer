from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    weight: Mapped[float]
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Metric(id={self.id}, name='{self.name}', weight={self.weight}, is_custom={self.is_custom}')>"