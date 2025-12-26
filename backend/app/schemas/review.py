from pydantic import BaseModel

class SReview(BaseModel):
    """Схема одного отзыва для отчета"""
    text: str
    rating: int
    author_name: str
    review_date: str