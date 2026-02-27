from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import SUserRegister, SUserLogin, SAuthResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=SAuthResponse)
async def register(data: SUserRegister, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(response, data, request.headers.get("user-agent"), request.client.host)

@router.post("/login", response_model=SAuthResponse)
async def login(data: SUserLogin, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(response, data, request.headers.get("user-agent"), request.client.host)

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    # Извлекаем токен вручную для логаута
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    service = AuthService(db)
    return await service.logout(response, token)