from pydantic import BaseModel, Field
from typing import List, Optional
from .ai_summary import SAiSummaryBase

class SAiMetricDefinition(BaseModel):
    """Универсальная схема для имени и описания метрики"""
    name: str
    # Поля опциональны, чтобы ИИ мог их пропускать для существующих метрик
    description: Optional[str] = None
    weight_explanation: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)

class SAiProductMetricLink(BaseModel):
    """Универсальная схема оценки товара по метрике"""
    metric: SAiMetricDefinition
    explanation: str
    score: int

class SAiAnalysisProduct(BaseModel):
    """Корневая схема анализа"""
    name: str
    description: str
    price: float
    thinking: str = Field(..., description="Анализ предоставленных кастомных метрик: почему выбраны одни и отброшены другие")
    ai_summary: SAiSummaryBase
    product_metrics_standard: List[SAiProductMetricLink] = []
    product_metrics_custom: List[SAiProductMetricLink] = []

class SAiAnalysisResponse(BaseModel):
    product: SAiAnalysisProduct