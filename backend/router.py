from fastapi import APIRouter, HTTPException

from utils import extract_ozon_id
from schemas import SProductCheck, SAnalyzeRequest, SFullReport
from repository import ProductRepository

router = APIRouter(prefix="/products", tags=["Аналитика"])


@router.get("/check/{ozon_id}", response_model=SProductCheck)
async def check_product(ozon_id: int):
    # Проверяет наличие информации о товаре в БД
    result = await ProductRepository.check_existence(ozon_id)
    return result


@router.post("/analyze")
async def start_analysis(data: SAnalyzeRequest):
    try:
        ozon_id = extract_ozon_id(data.url_or_id)

        # 1. Проверяем, не анализируется ли он ПРЯМО СЕЙЧАС (опционально)

        # 2. Передаем задачу Воркеру (пока просто имитируем запуск)
        # В будущем тут будет вызов: await celery_app.send_task(ozon_id)
        # В будущем тут будет добавление запроса на анализ в очередь

        return {"status": "ok", "ozon_id": ozon_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/report/{ozon_id}", response_model=SFullReport)
async def get_report(ozon_id: int):
    product = await ProductRepository.get_full_report(ozon_id)
    if not product:
        raise HTTPException(status_code=404, detail="Отчет не найден")

    # Собираем данные в кучу для фронтенда
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