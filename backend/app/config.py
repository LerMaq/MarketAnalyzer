from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union

class Settings(BaseSettings):
    app_name: str = "MarketAnalyzer API"
    debug: bool = True
    DATABASE_URL: str
    SECRET_KEY: str
    cors_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    static_dir: str = "static"
    images_dir: str = "static/images"

    model_config = SettingsConfigDict(env_file=".env") # Путь относительно папки backend

settings = Settings()