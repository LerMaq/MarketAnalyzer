"""Фоновый watcher для генерации эмбеддингов метрик."""
import asyncio
from app.database import new_session
from app.services.embedding_service import EmbeddingService

async def run_embedding_watcher() -> None:
    """
    Фоновый процесс для генерации эмбеддингов метрик.
    
    Каждые 30 секунд проверяет наличие метрик без эмбеддингов
    и генерирует для них векторные представления.
    Приоритет отдается новым метрикам.
    """
    embedding_service = EmbeddingService()
    
    while True:
        try:
            await asyncio.sleep(30)
            
            async with new_session() as db:
                processed = await embedding_service.process_metrics_without_embeddings(
                    db=db,
                    batch_size=100
                )
                
                if processed > 0:
                    print(f"Embedding watcher: обработано {processed} метрик")
                    
        except asyncio.CancelledError:
            print("Embedding watcher остановлен")
            break
        except Exception as e:
            print(f"Embedding watcher error: {e}")
            # Продолжаем работу даже при ошибках