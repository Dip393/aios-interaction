from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.rollback import (
    RollbackManager,
)


router = APIRouter(
    prefix="/rollback",
    tags=["Rollback"],
)


_rollback = RollbackManager()


class SnapshotRequest(BaseModel):
    session_id: str | None = None
    task_id: str | None = None
    environment_id: str | None = None

    label: str = "checkpoint"

    description: str = ""

    context_state: dict[str, Any] = Field(
        default_factory=dict
    )

    environment_state: dict[str, Any] = Field(
        default_factory=dict
    )

    memory_state: dict[str, Any] = Field(
        default_factory=dict
    )

    execution_state: dict[str, Any] = Field(
        default_factory=dict
    )

    custom_state: dict[str, Any] = Field(
        default_factory=dict
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


@router.get("/stats")
def stats() -> dict[str, Any]:
    return {
        "success": True,
        "data": _rollback.stats(),
    }


@router.post("/snapshot")
def create_snapshot(
    request: SnapshotRequest,
) -> dict[str, Any]:
    try:
        snapshot = _rollback.create_snapshot(
            session_id=request.session_id,
            task_id=request.task_id,
            environment_id=request.environment_id,
            label=request.label,
            description=request.description,
            context_state=request.context_state,
            environment_state=(
                request.environment_state
            ),
            memory_state=request.memory_state,
            execution_state=(
                request.execution_state
            ),
            custom_state=request.custom_state,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": snapshot.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/checkpoint")
def checkpoint(
    request: SnapshotRequest,
) -> dict[str, Any]:
    try:
        snapshot = _rollback.checkpoint(
            session_id=request.session_id,
            task_id=request.task_id,
            environment_id=request.environment_id,
            label=request.label,
            description=request.description,
            context_state=request.context_state,
            environment_state=(
                request.environment_state
            ),
            memory_state=request.memory_state,
            execution_state=(
                request.execution_state
            ),
            custom_state=request.custom_state,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": snapshot.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/snapshots")
def list_snapshots(
    session_id: str | None = None,
    task_id: str | None = None,
    environment_id: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    snapshots = _rollback.list(
        session_id=session_id,
        task_id=task_id,
        environment_id=environment_id,
        limit=limit,
    )

    return {
        "success": True,
        "data": [
            snapshot.to_dict()
            for snapshot in snapshots
        ],
    }


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(
    snapshot_id: str,
) -> dict[str, Any]:
    snapshot = _rollback.get(
        snapshot_id
    )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Snapshot not found.",
        )

    return {
        "success": True,
        "data": snapshot.to_dict(),
    }


@router.post(
    "/snapshots/{snapshot_id}/restore"
)
def restore_snapshot(
    snapshot_id: str,
) -> dict[str, Any]:
    try:
        result = _rollback.restore(
            snapshot_id
        )

        return {
            "success": result.success,
            "data": result.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/rollback")
def rollback(
    session_id: str | None = None,
    task_id: str | None = None,
    environment_id: str | None = None,
    steps: int = 1,
) -> dict[str, Any]:
    try:
        result = _rollback.rollback(
            session_id=session_id,
            task_id=task_id,
            environment_id=environment_id,
            steps=steps,
        )

        return {
            "success": result.success,
            "data": result.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/snapshots/{snapshot_id}/chain"
)
def snapshot_chain(
    snapshot_id: str,
) -> dict[str, Any]:
    try:
        chain = _rollback.chain(
            snapshot_id
        )

        return {
            "success": True,
            "data": [
                snapshot.to_dict()
                for snapshot in chain
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.delete(
    "/snapshots/{snapshot_id}"
)
def delete_snapshot(
    snapshot_id: str,
) -> dict[str, Any]:
    removed = _rollback.remove(
        snapshot_id
    )

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Snapshot not found.",
        )

    return {
        "success": True,
        "deleted": True,
        "snapshot_id": snapshot_id,
    }