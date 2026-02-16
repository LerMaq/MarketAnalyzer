from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import Product, Metric
from typing import Optional, List


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ozon_id_light(self, ozon_id: int) -> Optional[Product]:
        """Только данные самого товара без связей (быстрый запрос)"""
        query = select(Product).where(Product.ozon_id == ozon_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_product_id_full(self, product_id: int) -> Optional[Product]:
        """Товар со всеми связями для полного отчета"""
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.reviews),
                selectinload(Product.product_metrics),
                selectinload(Product.summary)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_versions(self, ozon_id: int) -> list[Product]:
        """Возвращает все найденные версии товара по его внешнему ozon_id"""
        query = (
            select(Product)
            .where(Product.ozon_id == ozon_id)
            .order_by(Product.date_added.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_full_by_id(self, product_id: int) -> Optional[Product]:
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.reviews),
                selectinload(Product.product_metrics),
                selectinload(Product.summary)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_metric(self, name: str, defaults: dict) -> Metric:
        """Находит метрику по имени или создает новую с дефолтными значениями"""
        query = select(Metric).where(Metric.name == name)
        result = await self.db.execute(query)
        metric = result.scalar_one_or_none()

        if not metric:
            metric = Metric(
                name=name,
                description=defaults.get("description", "Автоматически созданная метрика"),
                weight=defaults.get("weight", 1.0),
                is_custom=defaults.get("is_custom", False)
            )
            self.db.add(metric)
            # Мы не делаем commit здесь, чтобы сохранить атомарность всей транзакции
        return metric

    async def save_all(self, product: Product):
        """Сохраняет продукт и все связанные с ним объекты (summary, metrics, etc.)"""
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_standard_metrics(self) -> List[Metric]:
        """Все метрики с is_custom=False"""
        query = select(Metric).where(Metric.is_custom == False)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_random_custom_metrics(self, limit: int = 30) -> List[Metric]:
        """Случайные метрики с is_custom=True"""
        query = (
            select(Metric)
            .where(Metric.is_custom == True)
            .order_by(func.random())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

