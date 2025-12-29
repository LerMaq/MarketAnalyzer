from datetime import datetime
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    ozon_id: Mapped[int] = mapped_column(unique=True)
    date_added: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    reviews: Mapped[List["Review"]] = relationship()
    product_metrics: Mapped[List["ProductMetric"]] = relationship()
    summary: Mapped["AiSummary"] = relationship(uselist=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', ozon_id={self.ozon_id}, date_added='{self.date_added}')>"