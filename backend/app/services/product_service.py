from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.product_repository import ProductRepository
from app.schemas import SProductCheck, SProductFull


class ProductService:
    def __init__(self, db: AsyncSession):
        self.product_repo = ProductRepository(db)

    async def check_existence(self, ozon_id: int) -> SProductCheck:
        product = await self.product_repo.get_by_ozon_id_light(ozon_id)
        if not product:
            return SProductCheck(exists=False, ozon_id=ozon_id)

        return SProductCheck(exists=True, ozon_id=ozon_id,
                             id=product.id, name=product.name, date_added=product.date_added)

    async def get_full_report(self, ozon_id: int) -> SProductFull:
        product = await self.product_repo.get_by_ozon_id_full(ozon_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {ozon_id} не найден в базе"
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