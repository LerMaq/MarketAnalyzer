import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories import ProductRepository
from app.schemas import SProductCheck, SProductFull, STaskWorkerData
from app.models import Product, AiSummary, ProductMetric



class ProductService:
    def __init__(self, db: AsyncSession):
        self.product_repo = ProductRepository(db)

    async def check_existence(self, ozon_id: int) -> SProductCheck:
        product = await self.product_repo.get_by_ozon_id_light(ozon_id)
        if not product:
            return SProductCheck(exists=False, ozon_id=ozon_id)

        return SProductCheck(exists=True, ozon_id=ozon_id,
                             id=product.id, name=product.name, date_added=product.date_added)

    async def get_full_report(self, product_id: int) -> SProductFull:
        product = await self.product_repo.get_by_product_id_full(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {product_id} не найден в базе"
            )
        if not product.product_metrics:
            score = 0.0
        else:
            total_weight = sum(pm.metric.weight for pm in product.product_metrics)
            if total_weight > 0:
                score = sum(pm.score * pm.metric.weight for pm in product.product_metrics) / total_weight
            else:
                score = 0.0
        product.score = score
        return SProductFull.model_validate(product)

    async def process_worker_data(self, task_id: int, worker_data: STaskWorkerData):
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return None

        # Получаем данные от ИИ (пока заглушка)
        ai_data = await self._get_ai_analysis(worker_data.raw_content)
        product = ai_data["product"]

        new_product = Product(
            name=product["name"],
            description=product["description"],
            ozon_id=task.ozon_id,
            raw_content=worker_data.raw_content,
            price=product["price"],
            summary=AiSummary(text=product["ai_summary"]["text"])
        )

        for product_metric in product["product_metrics"]:
            metric = product_metric["metric"]

            # Логика сопоставления по названию
            new_metric = await self.product_repo.get_or_create_metric(
                name=metric["name"],
                defaults={
                    "description": metric.get("description", f"Анализ параметра {metric['name']}"),
                    "weight": metric.get("weight", 1.0),
                    "is_custom": metric.get("is_custom", False)
                }
            )

            # Создаем связь между продуктом и метрикой
            pm_entry = ProductMetric(
                score=int(product_metric["score"]),  # Нужно изменить в бд на float
                explanation=str(product_metric["explanation"]),
                metric=new_metric  # SQLAlchemy сама подставит metric_id после сохранения
            )
            new_product.product_metrics.append(pm_entry)

        # 3. Сохраняем все объекты
        saved_product = await self.product_repo.save_all(new_product)

        # 4. Закрываем задачу
        await self.task_repo.update_status(
            task_id=task.id,
            status="completed",
            product_id=saved_product.id
        )

        return saved_product

    async def _get_ai_analysis(self, text: str):
        """Проработанная заглушка с твоим форматом данных"""
        await asyncio.sleep(1)
        return {
            "product": {
                "name": "SIM-карта Билайн...",
                "description": "SIM-карта Билайн с эксклюзивным тарифом...",
                "price": 43.0,
                "ai_summary": {"text": "Товар представляет собой..."},
                "product_metrics": [
                    {
                        "metric": {"name": "Соответствие описанию"},
                        "explanation": "Описание тарифа в целом соответствует...",
                        "score": 4
                    },
                    {
                        "metric": {
                            "name": "Сложность управления личным кабинетом",
                            "description": "Оценка удобства...",
                            "weight": 0.45,
                            "is_custom": True
                        },
                        "explanation": "Упоминается, что работает...",
                        "score": 3
                    }
                ]
            }
        }

    async def get_versions_list(self, ozon_id):
        pass