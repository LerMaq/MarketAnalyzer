from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SReviewBase(BaseModel):
    """Схема одного отзыва для отчета"""
    text: str
    rating: int
    author_name: str
    review_date: datetime


class SReviewCreate(SReviewBase):
    """Схема для добавления отзыва"""
    pass


class SReview(SReviewBase):
    """Схема запроса отзыва"""
    id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)
