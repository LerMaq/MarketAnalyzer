from datetime import datetime, timedelta
from fastapi import HTTPException, Response
from app.repositories.user_repository import UserRepository
from app.auth.security import hash_password, verify_password, generate_session_token, get_token_hash
from app.schemas.auth import SUserRegister, SUserLogin, SAuthResponse


class AuthService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    async def register(self, response: Response, data: SUserRegister, ua: str, ip: str) -> SAuthResponse:
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Пользователь уже существует")

        hashed_pw = hash_password(data.password)
        user = await self.repo.create_user({
            "email": data.email,
            "password": hashed_pw,
            "name": data.name
        })
        return await self._create_session_flow(response, user.id, ua, ip)

    async def login(self, response: Response, data: SUserLogin, ua: str, ip: str) -> SAuthResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")

        return await self._create_session_flow(response, user.id, ua, ip)

    async def logout(self, response: Response, token: str):
        await self.repo.deactivate_session(token)
        response.delete_cookie("session_token")
        return {"message": "Выход выполнен"}

    async def _create_session_flow(self, response: Response, user_id: int, ua: str, ip: str) -> SAuthResponse:
        token = generate_session_token()
        expires = datetime.utcnow() + timedelta(days=30)

        await self.repo.create_session({
            "user_id": user_id,
            "token_hash": get_token_hash(token),
            "expires_at": expires,
            "user_agent": ua,
            "ip_address": ip
        })

        # Установка куки
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=2592000
        )

        # Возвращаем схему, валидируя словарь данных
        return SAuthResponse.model_validate({
            "session_token": token,
            "message": "Успешно"
        })