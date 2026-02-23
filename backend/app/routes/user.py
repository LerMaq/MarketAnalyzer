from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.user_service import UserService
from app.auth.dependencies import get_current_user
from app.schemas.user import SUserFullProfile

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me", response_model=SUserFullProfile)
async def get_me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.get_my_profile(user)