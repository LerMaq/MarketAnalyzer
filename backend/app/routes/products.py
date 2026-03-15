import re
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import ProductService
from app.schemas import SProductFull, SProductVersionsList, SCheckProductRequest, SProductTopItem
from app.auth.dependencies import get_current_user
from app.models.user import User

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

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить товар и все связанные данные (только для администраторов)"""
    service = ProductService(db)
    return await service.delete_product(product_id, user)
