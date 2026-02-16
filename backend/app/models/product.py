from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text)
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    ozon_id: Mapped[int] = mapped_column() # Убрано unique=True
    date_added: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    price: Mapped[Optional[float]] = mapped_column()

    reviews: Mapped[List["Review"]] = relationship()
    product_metrics: Mapped[List["ProductMetric"]] = relationship()
    summary: Mapped["AiSummary"] = relationship(uselist=False)
    chat_messages: Mapped[List["ChatMessage"]] = relationship(back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', ozon_id={self.ozon_id}, date_added='{self.date_added}')>"

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int]
    author_name: Mapped[str]
    review_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"<Review(id={self.id}, product_id='{self.product_id}', rating='{self.rating}', author_name='{self.author_name}')>"

class AiSummary(Base):
    __tablename__ = "ai_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    text: Mapped[str] = mapped_column(Text)

    def __repr__(self):
        return f"<AiSummary(id={self.id}, product_id='{self.product_id}')>"

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[Optional[str]]
    weight: Mapped[float] = mapped_column(default=1.0)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<Metric(id={self.id}, name='{self.name}', weight={self.weight})>"

class ProductMetric(Base):
    __tablename__ = "product_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"))
    score: Mapped[int]
    explanation: Mapped[str]

    metric: Mapped["Metric"] = relationship(lazy="joined")

    def __repr__(self):
        return f"<ProductMetric(id={self.id}, product_id={self.product_id}, score={self.score})>"