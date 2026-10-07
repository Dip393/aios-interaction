from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"],
)


_reminders: dict[
    str,
    dict[str, Any],
] = {}

_lock = threading.RLock()


class CreateReminderRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
    )

    remind_at: float

    session_id: str | None = None

    repeat: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


@router.get("")
def list_reminders(
    active_only: bool = True,
) -> dict[str, Any]:
    with _lock:
        reminders = list(
            _reminders.values()
        )

    if active_only:
        reminders = [
            item
            for item in reminders
            if item["active"]
        ]

    reminders.sort(
        key=lambda item: item["remind_at"]
    )

    return {
        "success": True,
        "data": reminders,
    }


@router.post("")
def create_reminder(
    request: CreateReminderRequest,
) -> dict[str, Any]:
    if request.remind_at <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid reminder time.",
        )

    reminder_id = (
        f"reminder-{uuid.uuid4().hex}"
    )

    reminder = {
        "reminder_id": reminder_id,
        "message": request.message,
        "remind_at": request.remind_at,
        "session_id": request.session_id,
        "repeat": request.repeat,
        "active": True,
        "created_at": time.time(),
        "metadata": dict(
            request.metadata
        ),
    }

    with _lock:
        _reminders[
            reminder_id
        ] = reminder

    return {
        "success": True,
        "data": reminder,
    }


@router.get("/{reminder_id}")
def get_reminder(
    reminder_id: str,
) -> dict[str, Any]:
    with _lock:
        reminder = _reminders.get(
            reminder_id
        )

    if reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found.",
        )

    return {
        "success": True,
        "data": reminder,
    }


@router.post("/{reminder_id}/cancel")
def cancel_reminder(
    reminder_id: str,
) -> dict[str, Any]:
    with _lock:
        reminder = _reminders.get(
            reminder_id
        )

        if reminder is None:
            raise HTTPException(
                status_code=404,
                detail="Reminder not found.",
            )

        reminder["active"] = False
        reminder["cancelled_at"] = (
            time.time()
        )

    return {
        "success": True,
        "data": reminder,
    }


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: str,
) -> dict[str, Any]:
    with _lock:
        reminder = _reminders.pop(
            reminder_id,
            None,
        )

    if reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found.",
        )

    return {
        "success": True,
        "data": reminder,
    }