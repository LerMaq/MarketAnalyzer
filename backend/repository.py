from sqlalchemy import select

from database import new_session, ProductOrm
from schemas import SProductAdd, SProduct


class ProductRepository:
    @classmethod
    async def add_one(cls, data: SProductAdd) -> int:
        async with new_session() as session:
            product_dict = data.model_dump()

            product = ProductOrm(**product_dict)
            session.add(product)

            await session.flush()
            await session.commit()
            return product.id


    @classmethod
    async def find_all(cls) -> list[SProduct]:
        async with new_session() as session:
            query = select(ProductOrm)
            result = await session.execute(query)
            product_models = result.scalars().all()
            product_schemas = [SProduct.model_validate(product_model) for product_model in product_models]
            return product_schemas