import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import ProductService
from app.schemas import SProductFull, SProductVersionsList, SProductTopItem, SCheckProductRequest
from typing import List

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/top", response_model=List[SProductTopItem])
async def get_top_products(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_top_products()

@router.post("/check", response_model=SProductVersionsList)
async def check_versions(data: SCheckProductRequest, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)

    return await service.get_versions_list(data.url)

@router.get("/report/{product_id}", response_model=SProductFull)
async def get_full_report(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_full_report(product_id)
