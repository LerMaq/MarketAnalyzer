import os
from datetime import datetime
from typing import Optional, List

from dotenv import load_dotenv
from sqlalchemy import ForeignKey, Text, Float, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)


class Model(AsyncAttrs, DeclarativeBase):
    pass


# --- Блок Пользователей и Доступов ---
class UserOrm(Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)

    ranks: Mapped[List["UserRankOrm"]] = relationship()


class RankOrm(Model):
    __tablename__ = "ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # free, premium, ultra
    level: Mapped[int]


class UserRankOrm(Model):
    __tablename__ = "user_ranks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"))
    expires_at: Mapped[datetime]


# --- Блок Товаров и Аналитики ---
class ProductOrm(Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    ozon_id: Mapped[int] = mapped_column(unique=True)
    date_added: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    reviews: Mapped[List["ReviewOrm"]] = relationship()
    metrics: Mapped[List["ProductMetricOrm"]] = relationship()
    summary: Mapped["AiSummaryOrm"] = relationship(uselist=False)


class ReviewOrm(Model):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int]
    author_name: Mapped[str]
    review_date: Mapped[str]


class AiSummaryOrm(Model):
    __tablename__ = "ai_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    text: Mapped[str] = mapped_column(Text)


class MetricOrm(Model):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    weight: Mapped[float]
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductMetricOrm(Model):
    __tablename__ = "product_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"))
    score: Mapped[int]
    explanation: Mapped[str]

    # Для легкого доступа к имени метрики
    metric_info: Mapped["MetricOrm"] = relationship(lazy="joined")



async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)


async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
