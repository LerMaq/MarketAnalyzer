import asyncio
from typing import AsyncGenerator, Optional
from fastapi import HTTPException, status, Request

from app.models import User
from app.repositories import ChatRepository, UserRepository
from app.services.ai_service import AIService
from app.database import new_session # Импортируем твой сессионмейкер
from app.models.chat import Chat


class ChatService:
    def __init__(self, db):
        self.db = db
        self.repo = ChatRepository(db)
        self.user_repo = UserRepository(db)
        self.ai_service = AIService(db)

    async def start_new_chat(self, user: Optional[User], product_id: int, title: str):
        # Чат создаётся только после того, как пользователь нажал отправить сообщение
        # В качестве title можно передавать первые символы первого сообщения пользователя
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "chat.ask" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав для использования чата")
        
        return await self.repo.create_chat(user.id, product_id, title)

    async def get_chat_messages(self, chat_id: int, user: Optional[User]):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "chat.ask" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав для использования чата")

        messages = await self.repo.get_messages_by_chat_id(chat_id, user.id)
        if messages is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к чату запрещен или чат не существует")
        return messages

    async def get_chats_list(self, user: Optional[User], product_id: int):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "chat.ask" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав для использования чата")

        return await self.repo.get_user_chats_by_product(user.id, product_id)

    async def remove_chat(self, chat_id: int, user: Optional[User]):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")
        if "chat.ask" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав для использования чата")

        success = await self.repo.delete_chat(chat_id, user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден или доступ запрещен")
        return {"status": "deleted"}

    async def get_chat_history_stream(self, user, chat_id, message_text, request, background_tasks):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходима авторизация")

        if "chat.ask" not in user.active_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав для использования чата")

        # Проверка лимитов (если не используется свой ключ)
        user_key = await self.repo.get_active_user_api_key(user.id)
        is_using_system_key = user_key is None

        if is_using_system_key:
            usage = await self.user_repo.get_or_create_today_usage(user.id)
            max_chat_limit = user.daily_limits.get("chat", 0)

            if usage.chat_count >= max_chat_limit:
                yield f"data: Error: Дневной лимит вопросов ({max_chat_limit}) исчерпан. Добавьте свой API ключ.\\n\\n"
                yield "data: [DONE]\\n\\n"
                return

        chat = await self.repo.get_chat_by_id(chat_id)
        if not chat:
            yield "data: Error: Chat not found\\n\\n"
            return

        await self.repo.save_message(chat_id, "user", message_text)
        history = await self.repo.get_chat_history(chat_id)
        # Тут можно использовать соответствующий метод product_service.get_full_report из ProductService
        product_context = await self.repo.get_product_context(chat.product_id)

        if user_key:
            model_record = user_key
        else:
            model_record = await self.ai_service.repo.get_best_model_with_key()
        chat_config = await self.ai_service.repo.get_config_by_name("chat_config")

        messages = [
            {"role": "user", "content": f"Данные товара: {product_context}"},
            {"role": "assistant", "content": "Я изучил данные товара. Чем могу помочь?"}
        ]
        for m in history:
            messages.append({"role": m.role, "content": m.message_text})

        text_stream = await self.ai_service.execute(chat_config, messages, model_record)
        full_reply = []

        try:
            async for text_chunk in text_stream:
                if await request.is_disconnected():
                    break
                full_reply.append(text_chunk)
                yield f"data: {text_chunk}\n\n"
        finally:
            # Когда стрим окончен (сам или по кнопке Стоп)
            if full_reply:
                reply_text = "".join(full_reply)
                # Добавляем задачу в фон, чтобы FastAPI выполнил её после закрытия коннекта
                background_tasks.add_task(self._bg_save_message, chat_id, reply_text)

    async def _bg_save_message(self, chat_id: int, text: str):
        """Фоновое сохранение через новую независимую сессию"""
        async with new_session() as db:
            repo = ChatRepository(db)  # Создаем репозиторий с новой сессией
            await repo.save_message(chat_id, "assistant", text)