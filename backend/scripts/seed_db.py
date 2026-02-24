import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.config import settings
from app.models.user import Rank, Permission, RankPermission

PERMISSIONS = [
    ("task.analysis", "Анализ товара"),
    ("chat.ask", "Уточняющие вопросы в чате"),
    ("ai_api_key.use", "Использование собственных API ключей для нейросетей"),
    ("ai.manage_keys", "Управление системными API ключами ИИ"),
    ("admin.panel", "Доступ к админ-панели"),
    ("task.worker", "Функционал воркера"),
    ("top.moderate", "Редактирование подборок"),
    ("user.manage", "Управление пользователями"),
]

RANKS = [
    {"name": "free", "level": 10, "analysis": 3, "chat": 10, "perms": ["task.analysis", "chat.ask", "ai_api_key.use"]},
    {"name": "premium", "level": 20, "analysis": 10, "chat": 100,
     "perms": ["task.analysis", "chat.ask", "ai_api_key.use"]},
    {"name": "worker", "level": 30, "analysis": None, "chat": 50, "perms": ["task.worker", "chat.ask"]},
    {"name": "moderator", "level": 40, "analysis": None, "chat": None,
     "perms": ["top.moderate", "user.manage", "chat.ask"]},
    {"name": "admin", "level": 100, "analysis": 99999, "chat": 99999, "perms": "ALL"},
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        perm_map = {}
        for name, desc in PERMISSIONS:
            p = Permission(name=name, description=desc)
            session.add(p)
            perm_map[name] = p
        await session.flush()

        for r_data in RANKS:
            rank = Rank(
                name=r_data["name"],
                level=r_data["level"],
                daily_analysis_limit=r_data["analysis"],
                daily_chat_limit=r_data["chat"]
            )
            session.add(rank)
            await session.flush()

            target_perms = perm_map.values() if r_data["perms"] == "ALL" else [perm_map[n] for n in r_data["perms"]]
            for p in target_perms:
                session.add(RankPermission(rank_id=rank.id, permission_id=p.id))

        await session.commit()
        print("База успешно наполнена данными!")


if __name__ == "__main__":
    asyncio.run(seed())