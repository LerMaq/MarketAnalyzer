from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List

from app.repositories import ProductRepository
from app.schemas import SProductCheck, SProductFull, SProductVersionsList, SProductVersion, SAiAnalysisResponse, SProductTopItem
from app.models import Product, AiSummary, ProductMetric
from app.utils import extract_ozon_id


class ProductService:
    def __init__(self, db: AsyncSession):
        self.product_repo = ProductRepository(db)

    async def check_existence(self, ozon_id: int) -> SProductCheck:
        product = await self.product_repo.get_by_ozon_id_light(ozon_id)
        if not product:
            return SProductCheck(exists=False, ozon_id=ozon_id)

        return SProductCheck(exists=True, ozon_id=ozon_id,
                             id=product.id, name=product.name, date_added=product.date_added)

    async def get_versions_list(self, url: str) -> SProductVersionsList:
        """
        Получает список всех версий товара.
        Если версий нет — возвращает пустой список.
        """
        ozon_id = extract_ozon_id(url)
        products = await self.product_repo.get_all_versions(ozon_id)

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

    async def get_top_products(self, limit: int = 10) -> List[SProductTopItem]:
        """
        Топ товаров: уникальные по ozon_id (самый свежий),
        отсортированные по средневзвешенной оценке.
        """
        all_products = await self.product_repo.get_all_products_with_metrics()

        # Дедупликация: оставляем продукт с наибольшим id для каждого ozon_id
        latest_by_ozon: dict[int, Product] = {}
        for p in all_products:
            if p.ozon_id not in latest_by_ozon or p.id > latest_by_ozon[p.ozon_id].id:
                latest_by_ozon[p.ozon_id] = p

        # Рассчитываем score для каждого уникального продукта
        scored = []
        for product in latest_by_ozon.values():
            if not product.product_metrics:
                score = 0.0
            else:
                total_weight = sum(pm.metric.weight for pm in product.product_metrics)
                if total_weight > 0:
                    score = sum(pm.score * pm.metric.weight for pm in product.product_metrics) / total_weight
                else:
                    score = 0.0
            scored.append(SProductTopItem(
                id=product.id,
                ozon_id=product.ozon_id,
                name=product.name,
                score=round(score, 2),
                date_added=product.date_added,
            ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:limit]

    async def create_full_product(self, ozon_id: int, raw_content: str, ai_result: SAiAnalysisResponse) -> Product:
        ai_data = ai_result.product

        product = Product(
            ozon_id=ozon_id,
            name=ai_data.name,
            description=ai_data.description,
            price=ai_data.price,
            raw_content=raw_content
        )
        product.summary = AiSummary(text=ai_data.ai_summary.text)

        for pm in ai_data.product_metrics_standard:
            try:
                metric_obj = await self.product_repo.get_metric_by_name(pm.metric.name)

                # Привязываем только если это реально стандартная метрика
                if metric_obj and not metric_obj.is_custom:
                    product.product_metrics.append(ProductMetric(
                        metric=metric_obj,
                        score=pm.score,
                        explanation=pm.explanation
                    ))
            except Exception as e:
                print(f"Ошибка связи со стандартной метрикой {pm.metric.name}: {e}")

        for pm in ai_data.product_metrics_custom:
            try:
                m_info = pm.metric

                # Собираем дефолты, фильтруя None, чтобы сработали значения из get_or_create_metric
                metric_defaults = {}
                if m_info.description:
                    metric_defaults["description"] = m_info.description
                if m_info.weight is not None:
                    metric_defaults["weight"] = m_info.weight

                metric_obj = await self.product_repo.get_or_create_metric(
                    name=m_info.name,
                    defaults=metric_defaults
                )

                if metric_obj and metric_obj.is_custom:
                    product.product_metrics.append(ProductMetric(
                        metric=metric_obj,
                        score=pm.score,
                        explanation=pm.explanation
                    ))
            except Exception as e:
                print(f"Ошибка кастомной метрики {pm.metric.name}: {e}")

        return await self.product_repo.save_all(product)