import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.database import get_db
from app.services import ProductService
from app.schemas import SProductFull, SProductVersionsList, SProductCheck, SProductTopItem
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/top", response_model=List[SProductTopItem])
async def get_top_products(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_top_products()

@router.post("/check", response_model=SProductVersionsList)
async def check_versions(data: SProductCheck, db: AsyncSession = Depends(get_db)):
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
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Необходима авторизация"
        )
    
    if 'admin.panel' not in user.active_permissions:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для удаления товара"
        )
    
    service = ProductService(db)
    product = await service.product_repo.get_by_product_id_full(product_id)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Товар с ID {product_id} не найден"
        )
    
    # Сначала удаляем все задачи, связанные с этим товаром
    await db.execute(delete(Task).where(Task.product_id == product_id))
    
    # Удаляем товар (каскадное удаление удалит все связанные данные)
    await db.delete(product)
    await db.commit()
    
    return {"id": product_id, "deleted": True}