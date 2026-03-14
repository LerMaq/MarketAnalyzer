from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class STask(BaseModel):
    id: int
    ozon_id: int
    status: str
    product_id: Optional[int] = None
    user_id: int
    retry_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class STaskAdd(BaseModel):
    """То, что прилетает с фронта (ссылка или ID)"""
    url_or_id: str

class STaskWorkerTake(BaseModel):
    """То, что забирает воркер"""
    task_id: int
    ozon_id: int

class STaskWorkerData(BaseModel):
    """То, что воркер присылает обратно"""
    raw_content: str
    price: Optional[float] = None
    name: str

class STaskAddedResponse(BaseModel):
    """Ответ пользователю после создания задачи"""
    status: str
    task_id: int