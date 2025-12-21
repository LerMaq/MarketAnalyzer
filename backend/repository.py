from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import new_session, ProductOrm, ReviewOrm, ProductMetricOrm, AiSummaryOrm


class ProductRepository:
    @classmethod
    async def check_existence(cls, ozon_id: int):
        async with new_session() as session:
            query = select(ProductOrm).where(ProductOrm.ozon_id == ozon_id)
            result = await session.execute(query)
            product = result.scalar_one_or_none()
            if product:
                return {"exists": True, "date_added": product.date_added, "ozon_id": ozon_id}
            return {"exists": False, "date_added": None, "ozon_id": ozon_id}

    @classmethod
    async def get_full_report(cls, ozon_id: int):
        async with new_session() as session:
            query = (
                select(ProductOrm)
                .where(ProductOrm.ozon_id == ozon_id)
                .options(
                    selectinload(ProductOrm.reviews),
                    selectinload(ProductOrm.metrics),
                    selectinload(ProductOrm.summary)
                )
            )
            result = await session.execute(query)
            product = result.scalar_one_or_none()
            return product