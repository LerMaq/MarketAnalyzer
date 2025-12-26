from pydantic import BaseModel
from typing import List
from app.schemas.review import SReview
from app.schemas.metric import SMetric

class SAnalyzeRequest(BaseModel):
    """Запрос на анализ, что прилетает с фронта: ссылка или ID"""
    url_or_id: str

class SFullReport(BaseModel):
    """Полный отчет, который фронт запрашивает для отрисовки страницы товара"""
    ozon_id: int
    name: str
    ai_summary: str
    metrics: List[SMetric]
    reviews: List[SReview]