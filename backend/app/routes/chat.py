from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.services import ChatService
from app.schemas import (
    SMessageCreate,
    SChatResponse,
    SChatCreate,
    SChatShortResponse,
    SMessageResponse,
    SAiKeyResponse,
    SAiKeyCreate,
    SAiKeyActivate
)

router = APIRouter(prefix="/chat", tags=["AI Chat Stream"])


@router.post("/stream")
async def chat_stream(
    data: SMessageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return StreamingResponse(
        service.get_chat_history_stream(user, data.chat_id, data.message_text, request, background_tasks),
        media_type="text/event-stream"
    )


@router.post("/create", response_model=SChatResponse)
async def create_chat(
        data: SChatCreate, db: AsyncSession = Depends(get_db),
        user: Optional[User] = Depends(get_current_user)
):
    service = ChatService(db)
    return await service.start_new_chat(user, data.product_id, data.title)


@router.get("/my-chats/{product_id}", response_model=List[SChatShortResponse])
async def get_my_chats(
        product_id: int,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.get_chats_list(user, product_id)


@router.get("/{chat_id}/messages", response_model=List[SMessageResponse])
async def get_chat_messages(
        chat_id: int,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.get_chat_messages(chat_id, user)


@router.delete("/{chat_id}")
async def delete_chat(
        chat_id: int,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.remove_chat(chat_id, user)


# ----------------- управление пользовательскими API-ключами ---------------------------
@router.get("/keys", response_model=List[SAiKeyResponse])
async def list_user_ai_keys(
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.get_user_ai_keys(user)


@router.post("/keys", response_model=SAiKeyResponse)
async def create_user_ai_key(
        data: SAiKeyCreate,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.add_user_ai_key(user, data.provider_url, data.key, data.model_name)


@router.post("/keys/activate")
async def activate_user_ai_key(
        data: SAiKeyActivate,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.activate_user_ai_key(user, data.key_id)


@router.delete("/keys/{key_id}")
async def delete_user_ai_key(
        key_id: int,
        user: Optional[User] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    return await service.delete_user_ai_key(user, key_id)

