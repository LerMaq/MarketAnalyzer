from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_tables, delete_tables
from app.routes import products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await delete_tables(); print("База удалена")
    await create_tables(); print("База создана")

    yield
    print("Выключение")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В разработке разрешаем всё, потом заменим на адрес фронта
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
