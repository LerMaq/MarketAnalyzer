from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.task import STask, STaskAdd, STaskAddedResponse, STaskWorkerTake, STaskWorkerData
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Задачи"])

@router.post("/add", response_model=STaskAddedResponse)
async def add_task(data: STaskAdd, db: AsyncSession = Depends(get_db)):
    service = TaskService(db)
    return await service.add_new_task(data.url_or_id)

@router.get("/status/{task_id}", response_model=STask)
async def get_status(task_id: int, db: AsyncSession = Depends(get_db)):
    service = TaskService(db)
    return await service.get_task_info(task_id)

@router.get("/take", response_model=Optional[STaskWorkerTake])
async def worker_take(db: AsyncSession = Depends(get_db)):
    service = TaskService(db)
    return await service.take_task_for_worker()


@router.post("/complete/{task_id}")
async def worker_complete(
        task_id: int,
        data: STaskWorkerData,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    await service.task_repo.update_status(task_id, status="processing")
    background_tasks.add_task(service.run_ai_analysis_and_finalize, task_id, data)
    # Анализ выполняется в фоне, воркеру сразу сообщается об успехе.
    return {"status": "processing", "message": "Данные приняты, анализ запущен в фоне"}