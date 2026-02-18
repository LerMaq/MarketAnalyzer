from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SMessageCreate(BaseModel):
    chat_id: int
    message_text: str

class SMessageResponse(BaseModel):
    id: int
    role: str
    message_text: str
    created_at: datetime

    class Config:
        from_attributes = True





class SChatCreate(BaseModel):
    product_id: int
    title: Optional[str] = "Новый диалог"

class SChatResponse(BaseModel):
    id: int
    product_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class SChatShortResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    last_message_preview: Optional[str] = None # Для красоты в списке истории