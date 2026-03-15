from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload, joinedload
from app.database import get_db
from app.models.user import User, UserRank, Rank
from app.models.product import Metric, ProductMetric
from app.models.ai import AiConfig, SystemAiApiKey, SystemAiModel
from app.auth.dependencies import get_current_user
from app.schemas.metric import SMetric, SProductMetric
from app.schemas.ai_config import SSystemAiKeyCreate
from app.services.ai_service import AIService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin_permission(user: Optional[User]):
    """Проверка прав администратора"""
    if user is None or "admin.panel" not in user.active_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )


# ========== METRICS ==========

@router.get("/metrics", response_model=List[SMetric])
async def get_metrics(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все метрики"""
    require_admin_permission(user)
    
    result = await db.execute(select(Metric))
    metrics = result.scalars().all()
    return metrics


@router.patch("/metrics/{metric_id}", response_model=SMetric)
async def update_metric(
    metric_id: int,
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить метрику (name, weight)"""
    require_admin_permission(user)
    
    # Проверяем существование метрики
    metric = await db.get(Metric, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Метрика не найдена")
    
    # Разрешенные поля (включая описание)
    allowed_fields = {"name", "description", "weight"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    
    await db.execute(
        update(Metric).where(Metric.id == metric_id).values(**update_data)
    )
    await db.commit()
    
    # Возвращаем обновленную метрику
    result = await db.execute(select(Metric).where(Metric.id == metric_id))
    metric = result.scalar_one()
    return metric


@router.delete("/metrics/{metric_id}", response_model=SMetric)
async def delete_metric(
    metric_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить метрику"""
    require_admin_permission(user)
    
    metric = await db.get(Metric, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Метрика не найдена")
    
    await db.delete(metric)
    await db.commit()
    
    return metric


# ========== PRODUCT METRICS ==========

@router.get("/product-metrics", response_model=List[SProductMetric])
async def get_product_metrics(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все оценки товаров по метрикам"""
    require_admin_permission(user)
    
    result = await db.execute(
        select(ProductMetric).options(
            # Загружаем связанную метрику
            selectinload(ProductMetric.metric)
        )
    )
    product_metrics = result.scalars().all()
    return product_metrics


@router.patch("/product-metrics/{pm_id}", response_model=SProductMetric)
async def update_product_metric(
    pm_id: int,
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить оценку товара (score, explanation)"""
    require_admin_permission(user)
    
    pm = await db.get(ProductMetric, pm_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    
    allowed_fields = {"score", "explanation"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    
    await db.execute(
        update(ProductMetric).where(ProductMetric.id == pm_id).values(**update_data)
    )
    await db.commit()
    
    result = await db.execute(
        select(ProductMetric).where(ProductMetric.id == pm_id)
    )
    pm = result.scalar_one()
    return pm


@router.delete("/product-metrics/{pm_id}", response_model=SProductMetric)
async def delete_product_metric(
    pm_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить оценку товара"""
    require_admin_permission(user)
    
    pm = await db.get(ProductMetric, pm_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    
    await db.delete(pm)
    await db.commit()
    
    return pm


# ========== USERS ==========

@router.get("/users", response_model=List[dict])
async def get_users(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить всех пользователей (базовая информация)"""
    require_admin_permission(user)
    
    result = await db.execute(
        select(User).options(
            selectinload(User.user_ranks).selectinload(UserRank.rank)
        )
    )
    users = result.scalars().all()
    
    # Формируем упрощенный ответ
    users_data = []
    for u in users:
        ranks = []
        for ur in u.user_ranks:
            rank_name = ur.rank.name if ur.rank else None
            ranks.append({
                "rank": rank_name,
                "expires_at": ur.expires_at
            })
        
        users_data.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "ranks": ranks
        })
    
    return users_data


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить пользователя"""
    require_admin_permission(user)
    
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя удалить самого себя
    if target_user.id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    # Удаляем связанные данные
    await db.delete(target_user)
    await db.commit()
    
    return {"id": user_id, "deleted": True}


@router.get("/users/search")
async def search_users(
    email: str,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск пользователей по email"""
    require_admin_permission(user)
    
    repo = UserRepository(db)
    users = await repo.search_users_by_email(email)
    
    result = []
    for u in users:
        # Получаем ранги пользователя
        user_with_ranks = await repo.get_user_with_ranks(u.id)
        ranks = []
        for ur in user_with_ranks.user_ranks:
            rank_name = ur.rank.name if ur.rank else None
            ranks.append({
                "rank": rank_name,
                "expires_at": ur.expires_at
            })
        
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "ranks": ranks
        })
    
    return result


@router.get("/users/{user_id}/usage")
async def get_user_usage(
    user_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику использования пользователя за сегодня"""
    require_admin_permission(user)
    
    repo = UserRepository(db)
    usage = await repo.get_user_usage_stats(user_id)
    return usage


@router.get("/ranks")
async def get_all_ranks(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все доступные ранги"""
    require_admin_permission(user)
    
    repo = UserRepository(db)
    ranks = await repo.get_all_ranks()
    return [{"id": r.id, "name": r.name, "level": r.level} for r in ranks]


@router.post("/users/{user_id}/ranks/{rank_name}")
async def assign_rank_to_user(
    user_id: int,
    rank_name: str,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Назначить пользователю ранг"""
    require_admin_permission(user)
    
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    repo = UserRepository(db)
    try:
        user_rank = await repo.assign_rank(user_id, rank_name)
        return {"user_id": user_id, "rank": rank_name, "assigned": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}/ranks/{rank_name}")
async def remove_rank_from_user(
    user_id: int,
    rank_name: str,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить ранг у пользователя"""
    require_admin_permission(user)
    
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    repo = UserRepository(db)
    success = await repo.remove_rank(user_id, rank_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Ранг не найден у пользователя")
    
    return {"user_id": user_id, "rank": rank_name, "removed": True}


@router.post("/users/worker")
async def create_worker(
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать нового пользователя с ролью worker.

    Ожидает JSON тело: { "email": "...", "password": "...", "name": "..." }.
    """
    require_admin_permission(user)

    email = payload.get("email")
    password = payload.get("password")
    name = payload.get("name")

    if not email or not password or not name:
        raise HTTPException(
            status_code=400,
            detail="Поля email, password и name обязательны"
        )
    
    from app.services.user_service import UserService
    from app.auth.security import hash_password

    service = UserService(db)
    
    # Проверяем, не существует ли уже пользователь с таким email
    existing = await service.repo.get_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Создаем пользователя
    hashed_password = hash_password(password)
    new_user = await service.repo.create_user({
        "email": email,
        "name": name,
        "password": hashed_password
    })
    
    # Назначаем ранг worker
    await service.repo.assign_rank(new_user.id, "worker")
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "role": "worker"
    }


# ========== AI CONFIGS ==========

@router.get("/ai-configs")
async def get_ai_configs(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все конфигурации ИИ"""
    require_admin_permission(user)
    
    result = await db.execute(select(AiConfig))
    configs = result.scalars().all()
    
    return [{
        "id": c.id,
        "name": c.name,
        "system_instruction": c.system_instruction,
        "temperature": c.temperature,
        "is_stream": c.is_stream,
        "is_json": c.is_json
    } for c in configs]


@router.post("/ai-configs")
async def create_ai_config(
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новую конфигурацию ИИ"""
    require_admin_permission(user)
    
    # Проверяем обязательные поля
    required = {"name", "system_instruction"}
    if not all(k in payload for k in required):
        raise HTTPException(status_code=400, detail=f"Обязательные поля: {required}")
    
    # Проверяем уникальность имени
    existing = await db.execute(select(AiConfig).where(AiConfig.name == payload["name"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Конфигурация с таким именем уже существует")
    
    config = AiConfig(
        name=payload["name"],
        system_instruction=payload["system_instruction"],
        temperature=payload.get("temperature", 0.7),
        is_stream=payload.get("is_stream", False),
        is_json=payload.get("is_json", True)
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return {
        "id": config.id,
        "name": config.name,
        "system_instruction": config.system_instruction,
        "temperature": config.temperature,
        "is_stream": config.is_stream,
        "is_json": config.is_json
    }


@router.put("/ai-configs/{config_id}")
async def update_ai_config(
    config_id: int,
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить конфигурацию ИИ"""
    require_admin_permission(user)
    
    config = await db.get(AiConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    
    # Разрешенные поля для обновления
    allowed = {"system_instruction", "temperature", "is_stream", "is_json"}
    update_data = {k: v for k, v in payload.items() if k in allowed}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    
    # Если меняется имя, проверяем уникальность
    if "name" in payload:
        existing = await db.execute(
            select(AiConfig).where(AiConfig.name == payload["name"], AiConfig.id != config_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Конфигурация с таким именем уже существует")
        update_data["name"] = payload["name"]
    
    await db.execute(
        update(AiConfig).where(AiConfig.id == config_id).values(**update_data)
    )
    await db.commit()
    
    result = await db.execute(select(AiConfig).where(AiConfig.id == config_id))
    config = result.scalar_one()
    
    return {
        "id": config.id,
        "name": config.name,
        "system_instruction": config.system_instruction,
        "temperature": config.temperature,
        "is_stream": config.is_stream,
        "is_json": config.is_json
    }


@router.delete("/ai-configs/{config_id}")
async def delete_ai_config(
    config_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить конфигурацию ИИ"""
    require_admin_permission(user)
    
    config = await db.get(AiConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    
    await db.delete(config)
    await db.commit()
    
    return {"id": config_id, "deleted": True}


# ========== AI KEYS & MODELS ==========

@router.get("/ai-keys")
async def get_ai_keys(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все системные API ключи с моделями"""
    require_admin_permission(user)
    
    result = await db.execute(
        select(SystemAiApiKey).options(
            selectinload(SystemAiApiKey.models)
        )
    )
    keys = result.scalars().all()
    
    return [{
        "id": k.id,
        "provider_url": k.provider_url,
        "key": k.key[:10] + "..." if k.key else "",  # Показываем только начало ключа
        "models": [{
            "id": m.id,
            "model_name": m.model_name,
            "works": m.works,
            "priority": m.priority
        } for m in k.models]
    } for k in keys]


@router.post("/ai-keys")
async def create_ai_key(
    data: SSystemAiKeyCreate,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новый API ключ с пресетом моделей"""
    require_admin_permission(user)
    
    service = AIService(db)
    result = await service.add_key_with_preset(data, user)
    return result


@router.post("/ai-keys/{key_id}/models")
async def add_model_to_ai_key(
    key_id: int,
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить новую модель к существующему системному API ключу.
    
    Ожидает JSON тело:
    {
        "model_name": "gpt-4o",
        "priority": 5   # необязательное поле, по умолчанию 1
    }
    """
    require_admin_permission(user)

    key = await db.get(SystemAiApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    model_name = payload.get("model_name")
    priority = payload.get("priority", 1)

    if not model_name:
        raise HTTPException(status_code=400, detail="Поле model_name обязательно")

    # Проверяем, нет ли уже модели с таким именем для данного ключа
    result = await db.execute(
        select(SystemAiModel).where(
            SystemAiModel.api_key_id == key_id,
            SystemAiModel.model_name == model_name
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Модель с таким именем уже привязана к этому ключу")

    new_model = SystemAiModel(
        api_key_id=key_id,
        model_name=model_name,
        priority=priority,
        works=True
    )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)

    return {
        "id": new_model.id,
        "api_key_id": key_id,
        "model_name": new_model.model_name,
        "priority": new_model.priority,
        "works": new_model.works
    }


@router.delete("/ai-keys/{key_id}")
async def delete_ai_key(
    key_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить API ключ (каскадно удалит модели)"""
    require_admin_permission(user)
    
    key = await db.get(SystemAiApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    
    await db.delete(key)
    await db.commit()
    
    return {"id": key_id, "deleted": True}


@router.patch("/ai-models/{model_id}/toggle")
async def toggle_ai_model(
    model_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Переключить флаг works модели"""
    require_admin_permission(user)
    
    model = await db.get(SystemAiModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    model.works = not model.works
    await db.commit()
    
    return {"id": model_id, "works": model.works}


@router.patch("/ai-models/{model_id}")
async def update_ai_model(
    model_id: int,
    payload: dict,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить системную модель (название и/или приоритет).
    
    Допустимые поля:
    - model_name: str
    - priority: int
    """
    require_admin_permission(user)

    model = await db.get(SystemAiModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")

    allowed_fields = {"model_name", "priority"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    # Если меняем имя модели, проверим, что для данного ключа нет дубликата
    new_name = update_data.get("model_name")
    if new_name and new_name != model.model_name:
        result = await db.execute(
            select(SystemAiModel).where(
                SystemAiModel.api_key_id == model.api_key_id,
                SystemAiModel.model_name == new_name
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Модель с таким именем уже существует для этого ключа")

    await db.execute(
        update(SystemAiModel).where(SystemAiModel.id == model_id).values(**update_data)
    )
    await db.commit()

    refreshed = await db.get(SystemAiModel, model_id)
    return {
        "id": refreshed.id,
        "api_key_id": refreshed.api_key_id,
        "model_name": refreshed.model_name,
        "priority": refreshed.priority,
        "works": refreshed.works,
    }


@router.delete("/ai-models/{model_id}")
async def delete_ai_model(
    model_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить системную модель из ключа"""
    require_admin_permission(user)

    model = await db.get(SystemAiModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")

    await db.delete(model)
    await db.commit()

    return {"id": model_id, "deleted": True}