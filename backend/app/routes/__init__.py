from .products import router as products_router
from .tasks import router as tasks_router
from .ai import router as ai_router
from .chat import router as chat_router

__all__ = [
    "products_router",
    "tasks_router",
    "ai_router",
    "chat_router"
]