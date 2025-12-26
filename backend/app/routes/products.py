from fastapi import APIRouter, HTTPException
from app.utils import extract_ozon_id
from app.schemas import SProductCheck, SAnalyzeRequest, SFullReport
from app.repositories.product_repository import ProductRepository

router = APIRouter(prefix="/products", tags=["Аналитика"])

@router.get("/check/{ozon_id}", response_model=SProductCheck)
async def check_product(ozon_id: int):
    result = await ProductRepository.check_existence(ozon_id)
    return result

@router.post("/analyze")
async def start_analysis(data: SAnalyzeRequest):
    try:
        ozon_id = extract_ozon_id(data.url_or_id)
        # Здесь будет логика воркера
        return {"status": "ok", "ozon_id": ozon_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/report/{ozon_id}", response_model=SFullReport)
async def get_report(ozon_id: int):
    product = await ProductRepository.get_full_report(ozon_id)
    if not product:
        raise HTTPException(status_code=404, detail="Отчет не найден")

    return {
        "ozon_id": product.ozon_id,
        "name": product.name,
        "ai_summary": product.summary.text if product.summary else "Еще не готово",
        "metrics": [
            {"name": m.metric_info.name, "score": m.score, "explanation": m.explanation}
            for m in product.metrics
        ],
        "reviews": product.reviews
    }