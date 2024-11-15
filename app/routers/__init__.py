from .commands import router as commands_router
from .auth import router as auth_router
from .index import router as index_router

__all__ = ["commands_router", "auth_router", "index_router"]
