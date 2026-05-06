from pydantic import BaseModel, ConfigDict, field_validator
from typing import Literal, Optional
from datetime import datetime


ALLOWED_REVIEW_COUNTS = (50, 100, 150, 200)


class STask(BaseModel):
    id: int
    ozon_id: int
    status: str
    product_id: Optional[int] = None
    user_id: int
    retry_count: int = 0
    review_count: int = 50

    model_config = ConfigDict(from_attributes=True)

class STaskAdd(BaseModel):
    """То, что прилетает с фронта (ссылка или ID)"""
    url_or_id: str
    review_count: Literal[50, 100, 150, 200] = 50

class STaskWorkerTake(BaseModel):
    """То, что забирает воркер"""
    task_id: int
    ozon_id: int
    review_count: int = 50

class STaskWorkerData(BaseModel):
    """То, что воркер присылает обратно"""
    raw_content: str
    price: Optional[float] = None
    name: str

class STaskAddedResponse(BaseModel):
    """Ответ пользователю после создания задачи"""
    status: str
    task_id: int