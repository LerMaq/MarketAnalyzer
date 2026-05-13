import asyncio
from typing import List
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.repositories.product_repository import ProductRepository

class EmbeddingService:
    """Сервис для генерации эмбеддингов"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.EMBEDDING_API_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY
        )
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    async def generate_embedding(self, text: str) -> List[float]:
        """Генерирует векторное представление для текста"""
        if not text or not text.strip():
            raise ValueError("Текст не может быть пустым")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding

            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Неожиданная размерность эмбеддинга: {len(embedding)}, ожидалось {self.dimension}"
                )
            
            return embedding
        except Exception as e:
            raise ValueError(f"Ошибка генерации эмбеддинга: {str(e)}")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Генерирует векторные представления для списка текстов"""
        if not texts:
            return []

        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("Все тексты пустые")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                encoding_format="float"
            )
            
            embeddings = [item.embedding for item in response.data]

            for embedding in embeddings:
                if len(embedding) != self.dimension:
                    raise ValueError(
                        f"Неожиданная размерность эмбеддинга: {len(embedding)}, ожидалось {self.dimension}"
                    )
            
            return embeddings
        except Exception as e:
            raise ValueError(f"Ошибка генерации эмбеддингов: {str(e)}")

    def prepare_metric_text(self, name: str, description: str = None) -> str:
        """Подготавливает текст метрики для векторизации"""
        if description:
            return f"{name}: {description}"
        return name

    async def process_metrics_without_embeddings(self, db: AsyncSession, batch_size: int = 5) -> int:
        """Обрабатывает метрики без эмбеддингов одним батч-запросом"""
        repo = ProductRepository(db)

        metrics = await repo.get_metrics_without_embeddings(limit=batch_size)

        if not metrics:
            return 0

        try:
            # Подготавливаем тексты для всех метрик
            texts = [self.prepare_metric_text(m.name, m.description) for m in metrics]

            # Генерируем эмбеддинги одним батч-запросом
            embeddings = await self.generate_embeddings_batch(texts)

            # Сохраняем эмбеддинги для всех метрик
            for metric, embedding in zip(metrics, embeddings):
                await repo.update_metric_embedding(metric.id, embedding)

            print(f"✓ Эмбеддинги созданы для {len(metrics)} метрик: {', '.join([m.name for m in metrics])}")
            return len(metrics)

        except Exception as e:
            print(f"✗ Ошибка батч-генерации эмбеддингов: {e}")
            print(f"  Пробую обработать метрики по одной...")

            # Fallback: обрабатываем по одной при ошибке батч-запроса
            processed = 0
            for metric in metrics:
                try:
                    text = self.prepare_metric_text(metric.name, metric.description)
                    embedding = await self.generate_embedding(text)
                    await repo.update_metric_embedding(metric.id, embedding)
                    processed += 1
                    print(f"  ✓ {metric.name}")
                except Exception as e:
                    print(f"  ✗ {metric.name}: {e}")
                    continue

            return processed
