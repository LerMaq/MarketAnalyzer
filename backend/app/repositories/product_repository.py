from sqlalchemy import select, func, delete, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import Product, Metric
from app.models.task import Task
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

    async def get_latest_task_review_counts(self, product_ids: list[int]) -> dict[int, int]:
        if not product_ids:
            return {}

        query = (
            select(Task.product_id, Task.review_count)
            .where(Task.product_id.in_(product_ids))
            .order_by(Task.product_id, Task.created_at.desc())
        )
        result = await self.db.execute(query)

        counts: dict[int, int] = {}
        for product_id, review_count in result:
            if product_id not in counts:
                counts[product_id] = review_count
        return counts

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
        metric = result.scalars().first()

        if not metric:
            metric = Metric(
                name=name,
                description=defaults.get("description", "Автоматически созданная метрика"),
                weight=defaults.get("weight", 0.4),
                is_custom=defaults.get("is_custom", True)
            )
            self.db.add(metric)
            # Мы не делаем commit здесь, чтобы сохранить атомарность всей транзакции
        return metric

    async def get_metric_by_name(self, name: str):
        query = select(Metric).where(Metric.name == name)
        result = await self.db.execute(query)
        return result.scalars().first()

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

    async def get_all_products_with_metrics(self) -> List[Product]:
        """Все продукты с метриками для расчёта топа"""
        query = (
            select(Product)
            .options(
                selectinload(Product.product_metrics),
                selectinload(Product.summary)
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    async def delete_tasks_by_product_id(self, product_id: int) -> None:
        """Удалить все задачи, связанные с товаром."""
        await self.db.execute(delete(Task).where(Task.product_id == product_id))

    async def delete_product(self, product: Product) -> None:
        """Удалить товар и сохранить изменения."""
        await self.db.delete(product)
        await self.db.commit()

    async def update_metric_embedding(self, metric_id: int, embedding: List[float]) -> None:
        """Обновить векторное представление метрики"""
        query = select(Metric).where(Metric.id == metric_id)
        result = await self.db.execute(query)
        metric = result.scalar_one_or_none()

        if metric:
            metric.embedding = embedding
            await self.db.commit()
            await self.db.refresh(metric)

    async def get_metrics_with_similarity(self, query_vector: List[float], limit: int = 40) -> List[dict]:
        """
        Векторный поиск кастомных метрик с вычислением similarity score.
        Возвращает список словарей с метрикой и её оценкой схожести.
        """
        query_vector_param = bindparam("query_vector", query_vector, type_=Metric.embedding.type)
        distance_expr = Metric.embedding.cosine_distance(query_vector_param)
        similarity_expr = (1 - distance_expr)

        query = (
            select(
                Metric.id,
                Metric.name,
                Metric.description,
                Metric.weight,
                Metric.is_custom,
                similarity_expr.label("similarity")
            )
            .where(Metric.is_custom == True, Metric.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        metrics_with_scores = []
        for row in rows:
            metric = Metric(
                id=row.id,
                name=row.name,
                description=row.description,
                weight=row.weight,
                is_custom=row.is_custom
            )
            metrics_with_scores.append({
                "metric": metric,
                "score": float(row.similarity)
            })

        return metrics_with_scores

    async def get_metrics_without_embeddings(self, limit: int = 100) -> List[Metric]:
        """Получить метрики без векторных представлений для генерации эмбеддингов"""
        query = (
            select(Metric)
            .where(Metric.embedding.is_(None))
            .limit(limit)
            .order_by(Metric.id.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


