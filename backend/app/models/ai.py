from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class SystemAiApiKey(Base):
    __tablename__ = "system_ai_api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_url: Mapped[str]
    key: Mapped[str]

    models: Mapped[list["SystemAiModel"]] = relationship(back_populates="api_key")

class SystemAiModel(Base):
    __tablename__ = "system_ai_models"
    id: Mapped[int] = mapped_column(primary_key=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("system_ai_api_keys.id"))
    model_name: Mapped[str]
    works: Mapped[bool] = mapped_column(default=True)
    priority: Mapped[int] = mapped_column(default=1)

    api_key: Mapped["SystemAiApiKey"] = relationship(back_populates="models")

class AiConfig(Base):
    __tablename__ = "ai_configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    system_instruction: Mapped[str] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(default=0.7)