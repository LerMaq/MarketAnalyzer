from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import AIService
from app.schemas.ai_config import SSystemAiKeyCreate

router = APIRouter(prefix="/ai-setup", tags=["AI Setup"])

@router.post("/keys")
async def setup_ai_key(data: SSystemAiKeyCreate, db: AsyncSession = Depends(get_db)):
    service = AIService(db)
    new_key = await service.add_key_with_preset(data)
    return {
        "status": "success",
        "key_id": new_key.id,
        "models_created": len(service.PRESET_TEMPLATES.get(data.preset.value, {}).get("models", []))
    }