from pydantic import BaseModel

class SMetric(BaseModel):
    """Схема конкретной метрики (например, 'Качество материала')"""
    name: str
    score: int
    explanation: str