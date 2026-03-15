from pydantic import BaseModel, ConfigDict


class SMetric(BaseModel):
    """Схема конкретной метрики (например, 'Качество материала')"""
    id: int
    name: str
    description: str
    weight: float
    is_custom: bool

    model_config = ConfigDict(from_attributes=True)


class SProductMetricBase(BaseModel):
    """Схема оценки товара по определённой метрике"""
    score: int
    explanation: str
    metric: SMetric


class SProductMetricCreate(SProductMetricBase):
    pass


class SProductMetric(SProductMetricBase):
    id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)
