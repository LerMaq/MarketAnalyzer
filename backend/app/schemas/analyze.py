from pydantic import BaseModel

class SAnalyzeRequest(BaseModel):
    """Запрос на анализ, что прилетает с фронта: ссылка или ID"""
    url_or_id: str