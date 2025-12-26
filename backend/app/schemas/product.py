from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SProductCheck(BaseModel):
    """Схема для быстрой проверки: есть товар в БД или нет"""
    exists: bool
    date_added: Optional[datetime] = None
    ozon_id: int