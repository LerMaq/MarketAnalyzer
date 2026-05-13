from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Any, Optional


class Settings(BaseSettings):
    app_name: str = "MarketAnalyzer API"
    debug: bool = True
    DATABASE_URL: str
    HTTP_PROXY: Optional[str] = None
    EMBEDDING_API_KEY: str
    EMBEDDING_API_BASE_URL: str = "https://openrouter.ai/api/v1"
    EMBEDDING_MODEL: str = "qwen/qwen3-embedding-8b"
    EMBEDDING_DIMENSION: int = 4096

    # Меняем тип на Any, чтобы Pydantic не паниковал при получении строки
    CORS_ORIGINS: Any = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # Если это строка через запятую
            if not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            # Если это строка, которая выглядит как JSON-массив
            import json
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix=""  # Гарантируем, что префиксы не мешают
    )


settings = Settings()
