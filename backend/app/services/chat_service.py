from typing import AsyncGenerator

from fastapi import HTTPException

from app.repositories.chat_repository import ChatRepository
from app.services.ai_service import AIService
from app.models.chat import Chat


class ChatService:
    def __init__(self, db):
        self.db = db
        self.repo = ChatRepository(db)
        self.ai_service = AIService(db)

    async def start_new_chat(self, user_id: int, product_id: int, title: str):
        # Чат создаётся только после того, как пользователь нажал отправить сообщение
        # В качестве title можно передавать первые символы первого сообщения пользователя
        return await self.repo.create_chat(user_id, product_id, title)

    async def get_chat_messages(self, chat_id: int, user_id: int):
        messages = await self.repo.get_messages_by_chat_id(chat_id, user_id)
        if messages is None:
            raise HTTPException(status_code=403, detail="Доступ к чату запрещен или чат не существует")
        return messages

    async def get_chats_list(self, user_id: int, product_id: int):
        return await self.repo.get_user_chats_by_product(user_id, product_id)

    async def remove_chat(self, chat_id: int, user_id: int):
        success = await self.repo.delete_chat(chat_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Чат не найден или доступ запрещен")
        return {"status": "deleted"}

    async def get_chat_messages(self, chat_id: int, user_id: int):
        messages = await self.repo.get_messages_by_chat_id(chat_id, user_id)
        if messages is None:
            raise HTTPException(status_code=403, detail="Доступ к чату запрещен или чат не существует")
        return messages

    async def create_chat(self, user_id: int, product_id: int, title: str) -> Chat:
        return await self.repo.create_chat(user_id, product_id, title)

    async def get_chat_history_stream(self, chat_id: int, message_text: str) -> AsyncGenerator[str, None]:
        chat = await self.repo.get_chat_by_id(chat_id)
        if not chat:
            yield "data: Error: Chat not found\n\n"
            return

        await self.repo.save_message(chat_id, "user", message_text)

        history = await self.repo.get_chat_history(chat_id)

        # Тут можно изменить подход и использовать, например product_sservice.get_full_report,
        # хотя в текущей версии даже лучше, так как до отчёта о товаре многие данные (в т.ч. и отзывы) не дойдут
        product_context = await self.repo.get_product_context(chat.product_id)

        user_key = await self.repo.get_active_user_api_key(chat.user_id)
        if user_key:
            model_record = user_key
        else:
            model_record = await self.ai_service.repo.get_best_model_with_key()
        chat_config = await self.ai_service.repo.get_config_by_name("chat_config")

        messages = [
            {"role": "user", "content": f"Вот данные товара, по которому я буду задавать вопросы: {product_context}"},
            {"role": "assistant", "content": "Я изучил данные товара. Чем могу помочь?"}
        ]

        for m in history:
            messages.append({"role": m.role, "content": m.message_text})

        text_stream = await self.ai_service._execute(chat_config, messages, model_record)

        full_reply = []

        async for text_chunk in text_stream:
            full_reply.append(text_chunk)  # Сохранение для БД
            # Отправка фронтенду в формате SSE
            yield f"data: {text_chunk}\n\n"

        # Фраза для окончания потока (необходимо, чтобы фронтенд понял, что сообщение закончено)
        yield "data: [DONE]\n\n"

        if full_reply:
            await self.repo.save_message(chat_id, "assistant", "".join(full_reply))