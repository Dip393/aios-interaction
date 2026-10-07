from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


_tasks: dict[
    str,
    dict[str, Any],
] = {}

_lock = threading.RLock()


class CreateTaskRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
    )

    description: str = ""

    session_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None

    metadata: dict[str, Any] | None = None


@router.get("")
def list_tasks(
    status: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    with _lock:
        tasks = list(
            _tasks.values()
        )

    if status:
        tasks = [
            task
            for task in tasks
            if task["status"] == status
        ]

    if session_id:
        tasks = [
            task
            for task in tasks
            if task["session_id"]
            == session_id
        ]

    tasks.sort(
        key=lambda task: task["created_at"],
        reverse=True,
    )

    return {
        "success": True,
        "data": tasks,
    }


@router.post("")
def create_task(
    request: CreateTaskRequest,
) -> dict[str, Any]:
    task_id = (
        f"task-{uuid.uuid4().hex}"
    )

    task = {
        "task_id": task_id,
        "title": request.title,
        "description": request.description,
        "session_id": request.session_id,
        "status": "pending",
        "created_at": time.time(),
        "updated_at": time.time(),
        "metadata": dict(
            request.metadata
        ),
    }

    with _lock:
        _tasks[task_id] = task

    return {
        "success": True,
        "data": task,
    }


@router.get("/{task_id}")
def get_task(
    task_id: str,
) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return {
        "success": True,
        "data": task,
    }


@router.patch("/{task_id}")
def update_task(
    task_id: str,
    request: UpdateTaskRequest,
) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found.",
            )

        if request.title is not None:
            task["title"] = request.title

        if request.description is not None:
            task["description"] = (
                request.description
            )

        if request.status is not None:
            task["status"] = request.status

        if request.metadata is not None:
            task["metadata"] = dict(
                request.metadata
            )

        task["updated_at"] = time.time()

    return {
        "success": True,
        "data": task,
    }


@router.post("/{task_id}/complete")
def complete_task(
    task_id: str,
) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found.",
            )

        task["status"] = "completed"
        task["completed_at"] = time.time()
        task["updated_at"] = time.time()

    return {
        "success": True,
        "data": task,
    }


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: str,
) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found.",
            )

        task["status"] = "cancelled"
        task["updated_at"] = time.time()

    return {
        "success": True,
        "data": task,
    }


@router.delete("/{task_id}")
def delete_task(
    task_id: str,
) -> dict[str, Any]:
    with _lock:
        task = _tasks.pop(
            task_id,
            None,
        )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return {
        "success": True,
        "data": task,
    }