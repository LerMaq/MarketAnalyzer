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

    reviews: Mapped[List["Review"]] = relationship(cascade="all, delete-orphan", back_populates="product")
    product_metrics: Mapped[List["ProductMetric"]] = relationship(cascade="all, delete-orphan", back_populates="product")
    summary: Mapped["AiSummary"] = relationship(uselist=False, cascade="all, delete-orphan", back_populates="product")
    chats: Mapped[List["Chat"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', ozon_id={self.ozon_id}, date_added='{self.date_added}')>"

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int]
    author_name: Mapped[str]
    review_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, product_id='{self.product_id}', rating='{self.rating}', author_name='{self.author_name}')>"

class AiSummary(Base):
    __tablename__ = "ai_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)

    product: Mapped["Product"] = relationship(back_populates="summary")

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
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"))
    score: Mapped[int]
    explanation: Mapped[str]

    metric: Mapped["Metric"] = relationship(lazy="joined")
    product: Mapped["Product"] = relationship(back_populates="product_metrics")

    def __repr__(self):
        return f"<ProductMetric(id={self.id}, product_id={self.product_id}, score={self.score})>"