from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.services.user_service import UserService
from app.auth.dependencies import get_current_user
from app.schemas.user import SUserFullProfile, SUserUpdate, SUserPasswordChange, SSimpleMessage

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me", response_model=SUserFullProfile)
async def get_me(
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    return await service.get_my_profile(user)


@router.put("/me", response_model=SUserFullProfile)
async def update_me(
        payload: SUserUpdate,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
        service = UserService(db)
        return await service.update_my_profile(user, payload.model_dump())


@router.put("/me/password", response_model=SSimpleMessage)
async def change_password(
        payload: SUserPasswordChange,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
        service = UserService(db)
        return await service.change_my_password(user, payload.model_dump())