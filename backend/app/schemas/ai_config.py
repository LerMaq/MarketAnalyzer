from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ApiProviderPreset(str, Enum):
    google = "google"
    openai = "openai"
    yandex = "yandex"
    gigachat = "gigachat"
    deepseek = "deepseek"
    custom = "custom"


class SModelPreset(BaseModel):
    model_name: str
    priority: int = 1

class SSystemAiKeyCreate(BaseModel):
    key: str
    provider_url: Optional[str] = None
    preset: ApiProviderPreset