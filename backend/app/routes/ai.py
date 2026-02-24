from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.services import AIService
from app.schemas.ai_config import SSystemAiKeyCreate

router = APIRouter(prefix="/ai-setup", tags=["AI Setup"])

@router.post("/keys")
async def setup_ai_key(
    data: SSystemAiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    service = AIService(db)
    return await service.add_key_with_preset(data, user)