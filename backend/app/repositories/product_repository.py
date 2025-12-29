from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import Product
from typing import Optional

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ozon_id_light(self, ozon_id: int) -> Optional[Product]:
        """Только данные самого товара без связей (быстрый запрос)"""
        query = select(Product).where(Product.ozon_id == ozon_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ozon_id_full(self, ozon_id: int) -> Optional[Product]:
        """Товар со всеми связями для полного отчета"""
        query = (
            select(Product)
            .where(Product.ozon_id == ozon_id)
            .options(
                selectinload(Product.reviews),
                selectinload(Product.product_metrics),
                selectinload(Product.summary)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()