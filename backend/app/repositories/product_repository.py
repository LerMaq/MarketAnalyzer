from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import new_session
from app.models.product import Product


class ProductRepository:
    @classmethod
    async def check_existence(cls, ozon_id: int):
        async with new_session() as session:
            query = select(Product).where(Product.ozon_id == ozon_id)
            result = await session.execute(query)
            product = result.scalar_one_or_none()
            if product:
                return {"exists": True, "date_added": product.date_added, "ozon_id": ozon_id}
            return {"exists": False, "date_added": None, "ozon_id": ozon_id}

    @classmethod
    async def get_full_report(cls, ozon_id: int):
        async with new_session() as session:
            query = (
                select(Product)
                .where(Product.ozon_id == ozon_id)
                .options(
                    selectinload(Product.reviews),
                    selectinload(Product.metrics),
                    selectinload(Product.summary)
                )
            )
            result = await session.execute(query)
            product = result.scalar_one_or_none()
            return product