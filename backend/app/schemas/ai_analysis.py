from pydantic import BaseModel, Field
from typing import List
from .ai_summary import SAiSummaryBase

class SAiMetricDefinition(BaseModel):
    """Описание самой метрики (справочник)"""
    name: str
    description: str
    weight_explanation: str
    weight: float = Field(ge=0.0, le=1.0)
    is_custom: bool

class SAiProductMetric(BaseModel):
    """Оценка товара по метрике"""
    metric: SAiMetricDefinition
    explanation: str
    score: int

class SAiAnalysisProduct(BaseModel):
    """Данные товара внутри анализа"""
    name: str
    description: str
    price: float
    ai_summary: SAiSummaryBase
    product_metrics: List[SAiProductMetric]

class SAiAnalysisResponse(BaseModel):
    """Корневой объект ответа ИИ"""
    product: SAiAnalysisProduct