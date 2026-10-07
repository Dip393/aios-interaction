from .kernel import router as kernel_router
from .agents import router as agents_router
from .environments import router as environments_router
from .memory import router as memory_router
from .tasks import router as tasks_router
from .reminders import router as reminders_router
from .voice import router as voice_router
from .vision import router as vision_router
from .rollback import router as rollback_router
from .connectors import router as connectors_router


__all__ = [
    "kernel_router",
    "agents_router",
    "environments_router",
    "memory_router",
    "tasks_router",
    "reminders_router",
    "voice_router",
    "vision_router",
    "rollback_router",
    "connectors_router",
]