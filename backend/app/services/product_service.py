from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories import ProductRepository
from app.schemas import SProductCheck, SProductFull, SProductVersionsList, SProductVersion, SAiAnalysisResponse
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

    async def get_versions_list(self, ozon_id: int) -> SProductVersionsList:
        """
        Получает список всех версий товара.
        Если версий нет — выбрасывает 404, чтобы роутер вернул ошибку.
        """
        products = await self.product_repo.get_all_versions(ozon_id)

        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ozon_id {ozon_id} еще не проходил анализ"
            )

        versions = [
            SProductVersion(id=p.id, date_added=p.date_added)
            for p in products
        ]

        return SProductVersionsList(ozon_id=ozon_id, versions=versions)

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

    async def create_full_product(self, ozon_id: int, raw_content: str, ai_result: SAiAnalysisResponse) -> Product:
        ai_data = ai_result.product

        product = Product(
            ozon_id=ozon_id,
            name=ai_data.name,
            description=ai_data.description,
            price=ai_data.price,
            raw_content=raw_content  # данные воркера
        )

        product.summary = AiSummary(text=ai_data.ai_summary.text)

        # Обработка стандартных метрик
        if hasattr(ai_data, 'product_metrics_not_custom'):
            for pm in ai_data.product_metrics_not_custom:
                try:
                    # Ищем метрику в БД. Если её нет — пропускаем.
                    metric_obj = await self.product_repo.get_metric_by_name(pm.name)

                    if metric_obj and not metric_obj.is_custom:
                        product.product_metrics.append(ProductMetric(
                            metric=metric_obj,
                            score=pm.score,
                            explanation=pm.explanation
                        ))
                except Exception:
                    continue

        # Обработка кастомных метрик
        if hasattr(ai_data, 'product_metrics_custom'):
            for pm in ai_data.product_metrics_custom:
                try:
                    m_info = pm.metric
                    metric_obj = await self.product_repo.get_or_create_metric(
                        name=m_info.name,
                        defaults={
                            "description": m_info.description,
                            "weight": m_info.weight,
                            "is_custom": True
                        }
                    )

                    # Если метрика нашлась, но она НЕ кастомная — пропускаем
                    if metric_obj and metric_obj.is_custom:
                        product.product_metrics.append(ProductMetric(
                            metric=metric_obj,
                            score=pm.score,
                            explanation=pm.explanation
                        ))
                except Exception:
                    continue

        return await self.product_repo.save_all(product)