from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_tables, delete_tables
from router import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("База создана")
    yield
    print("Выключение")


app = FastAPI(lifespan=lifespan)
app.include_router(products_router)
