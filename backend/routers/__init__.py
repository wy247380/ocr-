from .upload import router as upload_router
from .tasks import router as tasks_router
from .admin import router as admin_router

__all__ = ["upload_router", "tasks_router", "admin_router"]
