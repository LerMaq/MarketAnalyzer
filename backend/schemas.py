from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Для проверки наличия
class SProductCheck(BaseModel):
    exists: bool
    date_added: Optional[datetime] = None
    ozon_id: int

# Для запроса на анализ
class SAnalyzeRequest(BaseModel):
    url_or_id: str

# Для отчета (то, что друг будет выводить на экран)
class SReviewSchema(BaseModel):
    text: str
    rating: int
    author_name: str
    review_date: str

class SMetricSchema(BaseModel):
    name: str
    score: int
    explanation: str

class SFullReport(BaseModel):
    ozon_id: int
    name: str
    ai_summary: str
    metrics: List[SMetricSchema]
    reviews: List[SReviewSchema]