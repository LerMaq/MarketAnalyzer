import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.routes import products_router, tasks_router, ai_router, chat_router, auth_router, user_router
from app.services.task_watcher import run_task_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await delete_tables(); print("База удалена")
    await create_tables(); print("База создана")

    watcher_task = asyncio.create_task(run_task_watcher())

    yield

    watcher_task.cancel()
    try:
        await watcher_task
    except asyncio.CancelledError:
        pass
    print("Выключение")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(products_router)
app.include_router(tasks_router)
app.include_router(ai_router)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(user_router)
