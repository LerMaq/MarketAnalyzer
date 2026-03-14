"""Фоновый watcher для сброса застрявших fetching-задач."""
import asyncio
from app.database import new_session
from app.services.task_service import TaskService


async def run_task_watcher() -> None:
    """Каждые 10 секунд проверяет задачи в fetching; при updated_at > 80 сек сбрасывает или помечает failed."""
    while True:
        try:
            await asyncio.sleep(10)
            async with new_session() as db:
                service = TaskService(db)
                await service.process_stale_fetching_tasks()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Task watcher error: {e}")
