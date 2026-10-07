from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .aios_core.db import init_db, now, rows, row, execute
from .aios_core.kernel import AIOSKernel
from .aios_core.memory import MemoryManager
from .aios_core.planner import plan

from .routes.kernel import router as kernel_router
from .routes.agents import router as agents_router
from .routes.environments import router as environments_router
from .routes.memory import router as memory_router
from .routes.tasks import router as tasks_router
from .routes.reminders import router as reminders_router
from .routes.voice import router as voice_router
from .routes.vision import router as vision_router
from .routes.rollback import router as rollback_router
from .routes.connectors import router as connectors_router


# ---------------------------------------------------------------------------
# Global AIOS services
# ---------------------------------------------------------------------------

kernel = AIOSKernel()
memory_manager = MemoryManager()


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    AIOS application lifecycle.

    Startup:
        - initialize database
        - prepare core services

    Shutdown:
        - stop background tasks cleanly
    """

    init_db()

    scheduler_task: asyncio.Task[Any] | None = None

    # Scheduler is optional at this stage.
    #
    # The dedicated scheduler module can be connected here once its
    # implementation is aligned with the new task/reminder architecture.
    try:
        from .aios_core.scheduler import scheduler_loop

        scheduler_task = asyncio.create_task(scheduler_loop())
    except (ImportError, AttributeError, TypeError):
        scheduler_task = None

    try:
        yield
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()

            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AIOS Runtime",
    description="Artificial Intelligence Operating System Runtime API",
    version="0.2.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Modular API routers
# ---------------------------------------------------------------------------
#
# All modular routers already define their own resource prefix:
#
#   /kernel
#   /agents
#   /environments
#   /memory
#   /tasks
#   /reminders
#   /voice
#   /vision
#   /rollback
#   /connectors
#
# Mounting them under /api keeps the frontend API contract consistent:
#
#   /api/kernel/...
#   /api/tasks/...
#   /api/memory/...
#

app.include_router(kernel_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(environments_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(vision_router, prefix="/api")
app.include_router(rollback_router, prefix="/api")
app.include_router(connectors_router, prefix="/api")


# ---------------------------------------------------------------------------
# Root / health endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "AIOS",
        "service": "AIOS Runtime",
        "version": "0.2.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "aios-api",
        "version": "0.2.0",
    }


@app.get("/api/health")
def api_health():
    return {
        "ok": True,
        "service": "aios-api",
        "version": "0.2.0",
    }


# ---------------------------------------------------------------------------
# Legacy / simplified command endpoint
# ---------------------------------------------------------------------------
#
# This endpoint is intentionally kept for compatibility with older clients.
#
# New frontend code should prefer:
#
#     POST /api/kernel/process
#
# This endpoint provides a lightweight command -> plan -> task flow.
#

@app.post("/api/command")
async def command(request: dict[str, Any]):
    text = str(
        request.get("text")
        or request.get("input")
        or ""
    ).strip()

    if not text:
        return {
            "success": False,
            "error": "Command text cannot be empty.",
        }

    planned = await plan(text)

    entities = planned.get("entities") or {}

    # Resolve a contact when the planner identifies a recipient.
    recipient_name = entities.get("recipient_name")

    if recipient_name:
        matches = rows(
            """
            SELECT *
            FROM contacts
            WHERE lower(name) = lower(?)
               OR lower(name) LIKE lower(?)
            LIMIT 1
            """,
            (
                recipient_name,
                f"{recipient_name}%",
            ),
        )

        if matches:
            entities["recipient_email"] = (
                matches[0].get("email") or ""
            )

            planned["entities"] = entities

    # Store recent context using the new memory manager.
    memory_candidates = planned.get("memory_candidates") or []

    for candidate in memory_candidates:
        if not isinstance(candidate, dict):
            continue

        content = str(candidate.get("content") or "").strip()

        if not content:
            continue

        category = str(
            candidate.get("category") or "context"
        )

        importance = int(
            candidate.get("importance") or 1
        )

        memory_manager.remember_recent(
            content=content,
            metadata={
                "category": category,
                "importance": importance,
                "source": "command",
            },
        )

    # Persist a lightweight task record when the legacy task table exists.
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    task_title = str(
        planned.get("title")
        or "AIOS Task"
    )

    task_type = str(
        planned.get("intent")
        or "general"
    )

    state = {
        "input": text,
        "plan": planned,
        "last_message": planned.get("response"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        execute(
            """
            INSERT INTO tasks(
                id,
                title,
                type,
                status,
                state_json,
                created_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                task_id,
                task_title,
                task_type,
                "pending",
                _json_dumps(state),
                now(),
            ),
        )
    except Exception:
        # The modular task system may use a different persistence layer.
        # The command endpoint should still return the generated plan.
        task_id = None

    actions = planned.get("actions") or []

    requires_confirmation = any(
        isinstance(action, dict)
        and action.get("risk") in {
            "high",
            "critical",
            "external",
        }
        for action in actions
    )

    return {
        "success": True,
        "task_id": task_id,
        "plan": planned,
        "requires_confirmation": requires_confirmation,
    }


# ---------------------------------------------------------------------------
# Legacy contacts endpoint
# ---------------------------------------------------------------------------
#
# Contacts are currently a lightweight persistence feature.
# A dedicated Contacts module can replace this later.
#

@app.get("/api/contacts")
def contacts():
    try:
        return {
            "contacts": rows(
                "SELECT * FROM contacts ORDER BY name"
            )
        }
    except Exception:
        return {
            "contacts": []
        }


@app.post("/api/contacts")
def create_contact(request: dict[str, Any]):
    name = str(request.get("name") or "").strip()
    email = str(request.get("email") or "").strip()
    phone = str(request.get("phone") or "").strip()

    if not name:
        return {
            "success": False,
            "error": "Contact name is required.",
        }

    contact_id = execute(
        """
        INSERT INTO contacts(name,email,phone)
        VALUES(?,?,?)
        """,
        (
            name,
            email,
            phone,
        ),
    )

    return row(
        "SELECT * FROM contacts WHERE id=?",
        (contact_id,),
    )


# ---------------------------------------------------------------------------
# Legacy events endpoint
# ---------------------------------------------------------------------------

@app.get("/api/events")
def events():
    try:
        return {
            "events": rows(
                """
                SELECT *
                FROM events
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
        }
    except Exception:
        return {
            "events": []
        }


# ---------------------------------------------------------------------------
# Legacy reminders endpoint
# ---------------------------------------------------------------------------
#
# The main reminder API is now provided by routes/reminders.py.
# This GET endpoint remains for compatibility with older clients.
#

@app.get("/api/legacy/reminders")
def legacy_reminders():
    try:
        return {
            "reminders": rows(
                """
                SELECT *
                FROM reminders
                ORDER BY due_at ASC
                """
            )
        }
    except Exception:
        return {
            "reminders": []
        }


# ---------------------------------------------------------------------------
# Legacy workspace endpoint
# ---------------------------------------------------------------------------
#
# New environment API:
#
#     /api/environments
#
# This endpoint is kept only as a compatibility bridge for older clients.
#

@app.post("/api/workspaces")
def create_workspace(request: dict[str, Any]):
    title = str(
        request.get("title")
        or "AIOS Workspace"
    ).strip()

    kind = str(
        request.get("kind")
        or "generic"
    ).strip()

    state = request.get("state")

    if not isinstance(state, dict):
        state = {}

    environment = {
        "environment": kind,
        "state": state,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "success": True,
        "title": title,
        "kind": kind,
        "environment": environment,
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _json_dumps(value: Any) -> str:
    """
    JSON serialization helper.

    Keeps serialization in one place so the API does not depend on
    Pydantic models for internal persistence.
    """

    import json

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )