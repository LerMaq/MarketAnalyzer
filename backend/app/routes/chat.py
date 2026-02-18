from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services import ChatService
from app.schemas import SMessageCreate, SChatResponse, SChatCreate, SChatShortResponse, SMessageResponse

router = APIRouter(prefix="/chat", tags=["AI Chat Stream"])

@router.post("/stream")
async def chat_stream(
        data: SMessageCreate,
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)

    return StreamingResponse(
        service.get_chat_history_stream(data.chat_id, data.message_text),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/create", response_model=SChatResponse)
async def create_chat(data: SChatCreate, db: AsyncSession = Depends(get_db)):
    # В будущем user_id нужно взять из Depends(get_current_user)
    current_user_id = 1
    service = ChatService(db)
    return await service.start_new_chat(current_user_id, data.product_id, data.title)

@router.get("/my-chats/{product_id}", response_model=List[SChatShortResponse])
async def get_my_chats(product_id: int, db: AsyncSession = Depends(get_db)):
    current_user_id = 1
    service = ChatService(db)
    return await service.get_chats_list(current_user_id, product_id)

@router.get("/{chat_id}/messages", response_model=List[SMessageResponse])
async def get_chat_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    current_user_id = 1
    service = ChatService(db)
    return await service.get_chat_messages(chat_id, current_user_id)

@router.delete("/{chat_id}")
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    current_user_id = 1
    service = ChatService(db)
    return await service.remove_chat(chat_id, current_user_id)