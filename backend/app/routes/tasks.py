from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import STask, STaskAdd, STaskAddedResponse, STaskWorkerTake, STaskWorkerData
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/add", response_model=STaskAddedResponse)
async def add_task(
    data: STaskAdd, 
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    service = TaskService(db)
    # Передаем юзера в сервис для проверки лимитов task.analysis
    return await service.add_new_task(data.url_or_id, user)

@router.get("/status/{task_id}", response_model=STask)
async def get_status(task_id: int, db: AsyncSession = Depends(get_db)):
    # Статус задачи обычно публичен (или можно добавить проверку владельца)
    service = TaskService(db)
    return await service.get_task_info(task_id)

@router.get("/take", response_model=Optional[STaskWorkerTake])
async def worker_take(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    service = TaskService(db)
    # Внутри сервиса проверим право task.worker
    return await service.take_task_for_worker(user)

@router.post("/complete/{task_id}")
async def worker_complete(
    task_id: int,
    data: STaskWorkerData,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    service = TaskService(db)
    # Проверяем права воркера перед запуском анализа
    await service.verify_worker_access(user)
    
    await service.task_repo.update_status(task_id, status="processing")
    background_tasks.add_task(service.run_ai_analysis_and_finalize, task_id, data)
    return {"status": "processing", "message": "Данные приняты, анализ запущен в фоне"}