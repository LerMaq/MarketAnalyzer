from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils import extract_ozon_id
from app.schemas import SProductCheck, SAnalyzeRequest, SProductFull
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Аналитика"])

@router.get("/check/{ozon_id}", response_model=SProductCheck)
async def check_product(ozon_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.check_existence(ozon_id)

@router.get("/report/{ozon_id}", response_model=SProductFull)
async def get_report(ozon_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_full_report(ozon_id)

@router.post("/analyze")
async def start_analysis(data: SAnalyzeRequest):
    try:
        ozon_id = extract_ozon_id(data.url_or_id)
        # Здесь будет логика воркера
        return {"status": "ok", "ozon_id": ozon_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))