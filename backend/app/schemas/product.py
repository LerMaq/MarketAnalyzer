from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.schemas.ai_summary import SAiSummary
from app.schemas.metric import SProductMetricCreate, SProductMetric
from app.schemas.review import SReviewCreate, SReview


class SProductBase(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    ozon_id: int
    date_added: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SProductFull(SProductBase):
    """Полные данные о товаре для чтения"""
    summary: SAiSummary
    product_metrics: List[SProductMetric]
    reviews: List[SReview]
    score: float



class SProductCheck(SProductBase):
    """Быстрая проверка: есть ли товар"""
    exists: bool


class SProductCreate(BaseModel):
    """Что присылает скрапер при создании/обновлении товара"""
    name: str
    ozon_id: int
    ai_summary: str
    product_metrics: List[SProductMetricCreate]
    reviews: List[SReviewCreate]


class SProductVersion(BaseModel):
    """Краткая информация о версии товара"""
    id: int
    date_added: datetime

    model_config = ConfigDict(from_attributes=True)


class SProductVersionsList(BaseModel):
    ozon_id: int
    versions: list[SProductVersion]


class SProductTopItem(BaseModel):
    """Краткая информация о товаре для топа"""
    id: int
    ozon_id: int
    name: str
    score: float
    date_added: datetime

    model_config = ConfigDict(from_attributes=True)