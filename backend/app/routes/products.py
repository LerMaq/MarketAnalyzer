from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import ProductService
from app.schemas import SProductFull, SProductVersionsList

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/check/{ozon_id}", response_model=SProductVersionsList)
async def check_versions(ozon_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_versions_list(ozon_id)

@router.get("/report/{product_id}", response_model=SProductFull)
async def get_full_report(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_full_report(product_id)