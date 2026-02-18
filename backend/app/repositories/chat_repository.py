from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload

from app.models import Product, AiSummary, Chat, ChatMessage


class ChatRepository:
    def __init__(self, db):
        self.db = db

    async def get_chat_history(self, chat_id: int):
        """Получить сообщения без верификации пользователя"""
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at)
        )
        return result.scalars().all()

    async def get_messages_by_chat_id(self, chat_id: int, user_id: int):
        """Получить сообщения с верификацией пользователя"""
        chat_check = await self.db.execute(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if not chat_check.scalar_one_or_none():
            return None

        query = (
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.asc())  # От старых к новым
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_product_context(self, product_id: int) -> str:
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.summary))
        )
        result = await self.db.execute(query)
        p = result.scalar_one_or_none()

        if not p:
            return "Данные о товаре отсутствуют"

        summary_text = p.summary.text if p.summary else "Анализ еще не проведен"
        context = (
            f"Название: {p.name}\n"
            f"Описание: {p.description}\n"
            f"Анализ отзывов: {summary_text}"
            f"Сырая информация: {p.raw_content}"
        )
        return context

    async def save_message(self, chat_id: int, role: str, text: str):
        msg = ChatMessage(chat_id=chat_id, role=role, message_text=text)
        self.db.add(msg)
        await self.db.commit()

    async def get_chat_by_id(self, chat_id: int):
        return await self.db.get(Chat, chat_id)

    async def create_chat(self, user_id: int, product_id: int, title: str) -> Chat:
        new_chat = Chat(user_id=user_id, product_id=product_id, title=title)
        self.db.add(new_chat)
        await self.db.commit()
        await self.db.refresh(new_chat)
        return new_chat

    async def get_user_chats_by_product(self, user_id: int, product_id: int):
        query = (
            select(Chat)
            .where(Chat.user_id == user_id, Chat.product_id == product_id)
            .order_by(desc(Chat.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_chat(self, chat_id: int, user_id: int) -> bool:
        query = delete(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0