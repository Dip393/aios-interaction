from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.memory import MemoryManager


router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


_memory = MemoryManager()


class RememberRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
    )

    source: str = "api"

    category: str = "general"

    importance: float = 0.5

    confidence: float = 1.0

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class TaskMemoryRequest(BaseModel):
    task_id: str
    goal: str = ""


class SemanticRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
    )

    category: str = "general"

    importance: float = 0.5

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


@router.get("/stats")
def stats() -> dict[str, Any]:
    return {
        "success": True,
        "data": _memory.stats(),
    }


@router.post("/recent")
def remember_recent(
    request: RememberRequest,
) -> dict[str, Any]:
    try:
        item = _memory.remember_recent(
            content=request.content,
            source=request.source,
            importance=request.importance,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": (
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/recent")
def recent(
    limit: int = 20,
) -> dict[str, Any]:
    try:
        result = _memory.recent(
            limit=limit
        )

        return {
            "success": True,
            "data": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in result
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/long-term")
def remember(
    request: RememberRequest,
) -> dict[str, Any]:
    try:
        item = _memory.remember(
            content=request.content,
            category=request.category,
            source=request.source,
            importance=request.importance,
            confidence=request.confidence,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": (
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/recall")
def recall(
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    try:
        result = _memory.recall(
            query,
            limit=limit,
        )

        return {
            "success": True,
            "data": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in result
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/semantic")
def remember_semantically(
    request: SemanticRequest,
) -> dict[str, Any]:
    try:
        item = _memory.remember_semantically(
            content=request.content,
            category=request.category,
            importance=request.importance,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": (
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/semantic/search")
def semantic_search(
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    try:
        result = _memory.semantic_search(
            query,
            limit=limit,
        )

        return {
            "success": True,
            "data": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in result
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/tasks")
def create_task_memory(
    request: TaskMemoryRequest,
) -> dict[str, Any]:
    try:
        memory = _memory.create_task_memory(
            task_id=request.task_id,
            goal=request.goal,
        )

        return {
            "success": True,
            "data": (
                memory.to_dict()
                if hasattr(
                    memory,
                    "to_dict",
                )
                else memory
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/tasks/{task_id}")
def get_task_memory(
    task_id: str,
) -> dict[str, Any]:
    memory = _memory.get_task_memory(
        task_id
    )

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Task memory not found.",
        )

    return {
        "success": True,
        "data": (
            memory.to_dict()
            if hasattr(
                memory,
                "to_dict",
            )
            else memory
        ),
    }


@router.delete("/tasks/{task_id}")
def clear_task_memory(
    task_id: str,
) -> dict[str, Any]:
    result = _memory.clear_task_memory(
        task_id
    )

    return {
        "success": True,
        "cleared": bool(result)
        if result is not None
        else True,
    }


@router.post("/consolidate")
def consolidate_recent(
    limit: int = 20,
) -> dict[str, Any]:
    try:
        result = _memory.consolidate_recent(
            limit=limit
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc