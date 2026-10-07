"""
AIOS Task Manager.

Provides persistent task management backed by SQLite.

Responsibilities:
    - Create tasks
    - Read tasks
    - Update task status/state
    - Maintain task snapshots
    - Roll back task state
    - List tasks
    - Delete tasks

This module is intentionally independent from the API route layer.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from .db import execute, row, rows, now


# ============================================================================
# Constants
# ============================================================================

TASK_STATUSES = {
    "pending",
    "queued",
    "active",
    "running",
    "paused",
    "completed",
    "failed",
    "cancelled",
}


DEFAULT_STATUS = "active"


# ============================================================================
# Internal helpers
# ============================================================================

def _generate_task_id() -> str:
    """Generate a compact unique AIOS task ID."""

    return f"task_{uuid.uuid4().hex[:10]}"


def _serialize_state(
    state: Optional[dict[str, Any]],
) -> str:
    """
    Safely serialize task state.
    """

    if state is None:
        state = {}

    if not isinstance(state, dict):
        raise TypeError(
            "Task state must be a dictionary."
        )

    return json.dumps(
        state,
        ensure_ascii=False,
        default=str,
    )


def _deserialize_state(
    value: Any,
) -> dict[str, Any]:
    """
    Safely deserialize state JSON.
    """

    if isinstance(value, dict):
        return value

    if value is None:
        return {}

    try:
        parsed = json.loads(
            value
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return {}

    if isinstance(parsed, dict):
        return parsed

    return {}


def _normalize_task(
    task: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """
    Convert a database task row into the public task structure.
    """

    if task is None:
        return None

    result = dict(task)

    result["state_json"] = _deserialize_state(
        result.get("state_json")
    )

    # Provide a convenient state alias for newer callers.
    result["state"] = result["state_json"]

    return result


def _validate_status(
    status: Optional[str],
) -> Optional[str]:
    """
    Validate a task status.
    """

    if status is None:
        return None

    normalized = str(
        status
    ).strip().lower()

    if normalized not in TASK_STATUSES:
        raise ValueError(
            f"Invalid task status '{status}'. "
            f"Allowed values: {', '.join(sorted(TASK_STATUSES))}"
        )

    return normalized


# ============================================================================
# Create
# ============================================================================

def create_task(
    title: str,
    kind: str = "general",
    state: Optional[dict[str, Any]] = None,
    status: str = DEFAULT_STATUS,
) -> Optional[dict[str, Any]]:
    """
    Create a persistent task.

    Example:

        create_task(
            "Write project report",
            "writing",
            {"topic": "AIOS"}
        )
    """

    title = str(
        title or ""
    ).strip()

    if not title:
        raise ValueError(
            "Task title cannot be empty."
        )

    kind = str(
        kind or "general"
    ).strip() or "general"

    status = _validate_status(
        status
    ) or DEFAULT_STATUS

    state = (
        state
        if state is not None
        else {}
    )

    task_id = _generate_task_id()
    timestamp = now()
    state_json = _serialize_state(
        state
    )

    execute(
        """
        INSERT INTO tasks(
            id,
            title,
            kind,
            status,
            state_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            title,
            kind,
            status,
            state_json,
            timestamp,
            timestamp,
        ),
    )

    # Every task starts with a checkpoint.
    snapshot(
        task_id,
        state,
    )

    return get_task(
        task_id
    )


# ============================================================================
# Read
# ============================================================================

def get_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Retrieve one task by ID.
    """

    if not tid:
        return None

    result = row(
        """
        SELECT *
        FROM tasks
        WHERE id = ?
        LIMIT 1
        """,
        (tid,),
    )

    return _normalize_task(
        result
    )


# ============================================================================
# Update
# ============================================================================

def update_task(
    tid: str,
    status: Optional[str] = None,
    state: Optional[dict[str, Any]] = None,
    title: Optional[str] = None,
    kind: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Update an existing task.

    Only supplied fields are modified.

    A snapshot is automatically created whenever task state changes.
    """

    task = get_task(
        tid
    )

    if task is None:
        return None

    new_status = (
        _validate_status(status)
        or task["status"]
    )

    new_state = (
        state
        if state is not None
        else task["state_json"]
    )

    if not isinstance(
        new_state,
        dict,
    ):
        raise TypeError(
            "Task state must be a dictionary."
        )

    new_title = (
        str(title).strip()
        if title is not None
        else task["title"]
    )

    new_kind = (
        str(kind).strip()
        if kind is not None
        else task["kind"]
    )

    if not new_title:
        raise ValueError(
            "Task title cannot be empty."
        )

    if not new_kind:
        new_kind = "general"

    state_changed = (
        state is not None
    )

    execute(
        """
        UPDATE tasks
        SET
            title = ?,
            kind = ?,
            status = ?,
            state_json = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            new_title,
            new_kind,
            new_status,
            _serialize_state(
                new_state
            ),
            now(),
            tid,
        ),
    )

    if state_changed:
        snapshot(
            tid,
            new_state,
        )

    return get_task(
        tid
    )


# ============================================================================
# Snapshot
# ============================================================================

def snapshot(
    tid: str,
    state: dict[str, Any],
) -> Optional[int]:
    """
    Create a task state snapshot.

    Returns the database snapshot ID when available.
    """

    task = get_task(
        tid
    )

    if task is None:
        return None

    state_json = _serialize_state(
        state
    )

    result = execute(
        """
        INSERT INTO task_snapshots(
            task_id,
            state_json,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            tid,
            state_json,
            now(),
        ),
    )

    # db.execute may return either a row ID or a row-count depending on
    # the implementation. Keep the function safe for both cases.
    try:
        return int(result)
    except (
        TypeError,
        ValueError,
    ):
        return None


# ============================================================================
# Snapshot history
# ============================================================================

def list_snapshots(
    tid: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return task snapshots from newest to oldest.
    """

    limit = max(
        1,
        min(
            int(limit),
            500,
        ),
    )

    snapshots = rows(
        """
        SELECT *
        FROM task_snapshots
        WHERE task_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            tid,
            limit,
        ),
    )

    result: list[
        dict[str, Any]
    ] = []

    for item in snapshots:
        current = dict(
            item
        )

        current["state_json"] = _deserialize_state(
            current.get("state_json")
        )

        current["state"] = current[
            "state_json"
        ]

        result.append(
            current
        )

    return result


def get_snapshot(
    snapshot_id: int,
) -> Optional[dict[str, Any]]:
    """
    Retrieve a specific task snapshot.
    """

    result = row(
        """
        SELECT *
        FROM task_snapshots
        WHERE id = ?
        LIMIT 1
        """,
        (snapshot_id,),
    )

    if result is None:
        return None

    normalized = dict(
        result
    )

    normalized["state_json"] = _deserialize_state(
        normalized.get("state_json")
    )

    normalized["state"] = normalized[
        "state_json"
    ]

    return normalized


# ============================================================================
# Rollback
# ============================================================================

def rollback(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Roll the task back to its previous snapshot.

    The current snapshot is removed after a successful rollback.

    If there is only one snapshot, the current task is returned unchanged.
    """

    task = get_task(
        tid
    )

    if task is None:
        return None

    snapshots = rows(
        """
        SELECT *
        FROM task_snapshots
        WHERE task_id = ?
        ORDER BY id DESC
        LIMIT 2
        """,
        (tid,),
    )

    if len(snapshots) < 2:
        return task

    current_snapshot = snapshots[0]
    previous_snapshot = snapshots[1]

    previous_state = _deserialize_state(
        previous_snapshot.get(
            "state_json"
        )
    )

    # Remove the current snapshot.
    execute(
        """
        DELETE FROM task_snapshots
        WHERE id = ?
        """,
        (
            current_snapshot["id"],
        ),
    )

    # Update the task without creating another snapshot.
    execute(
        """
        UPDATE tasks
        SET
            state_json = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            _serialize_state(
                previous_state
            ),
            now(),
            tid,
        ),
    )

    return get_task(
        tid
    )


# ============================================================================
# Rollback to a specific snapshot
# ============================================================================

def restore_snapshot(
    tid: str,
    snapshot_id: int,
) -> Optional[dict[str, Any]]:
    """
    Restore a task to a specific snapshot.

    The restored state itself becomes a new snapshot, preserving history.
    """

    task = get_task(
        tid
    )

    if task is None:
        return None

    selected = row(
        """
        SELECT *
        FROM task_snapshots
        WHERE id = ?
          AND task_id = ?
        LIMIT 1
        """,
        (
            snapshot_id,
            tid,
        ),
    )

    if selected is None:
        return None

    restored_state = _deserialize_state(
        selected.get(
            "state_json"
        )
    )

    return update_task(
        tid,
        state=restored_state,
    )


# ============================================================================
# Delete
# ============================================================================

def delete_task(
    tid: str,
) -> bool:
    """
    Delete a task and its snapshots.
    """

    task = get_task(
        tid
    )

    if task is None:
        return False

    # Explicitly delete snapshots so this works even if the SQLite
    # connection/table was created without relying on cascade behavior.
    execute(
        """
        DELETE FROM task_snapshots
        WHERE task_id = ?
        """,
        (tid,),
    )

    execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (tid,),
    )

    return True


# ============================================================================
# Task status helpers
# ============================================================================

def complete_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Mark a task as completed.
    """

    return update_task(
        tid,
        status="completed",
    )


def pause_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Pause a task.
    """

    return update_task(
        tid,
        status="paused",
    )


def cancel_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Cancel a task.
    """

    return update_task(
        tid,
        status="cancelled",
    )


def fail_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Mark a task as failed.
    """

    return update_task(
        tid,
        status="failed",
    )


def resume_task(
    tid: str,
) -> Optional[dict[str, Any]]:
    """
    Resume a paused task.
    """

    return update_task(
        tid,
        status="active",
    )


# ============================================================================
# Listing
# ============================================================================

def list_tasks(
    status: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List tasks.

    Optional filters:
        status
        kind
        limit
    """

    limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    status = _validate_status(
        status
    )

    query = """
        SELECT *
        FROM tasks
    """

    conditions: list[str] = []
    parameters: list[Any] = []

    if status is not None:
        conditions.append(
            "status = ?"
        )
        parameters.append(
            status
        )

    if kind is not None:
        conditions.append(
            "kind = ?"
        )
        parameters.append(
            str(kind).strip()
        )

    if conditions:
        query += (
            " WHERE "
            + " AND ".join(
                conditions
            )
        )

    query += """
        ORDER BY updated_at DESC, created_at DESC
        LIMIT ?
    """

    parameters.append(
        limit
    )

    task_rows = rows(
        query,
        tuple(parameters),
    )

    return [
        _normalize_task(task)
        for task in task_rows
    ]


# ============================================================================
# Task statistics
# ============================================================================

def task_stats() -> dict[str, Any]:
    """
    Return task counts grouped by status.
    """

    result = rows(
        """
        SELECT
            status,
            COUNT(*) AS count
        FROM tasks
        GROUP BY status
        ORDER BY status
        """
    )

    by_status = {
        item["status"]: int(
            item["count"]
        )
        for item in result
    }

    total = sum(
        by_status.values()
    )

    return {
        "total": total,
        "by_status": by_status,
    }


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "TASK_STATUSES",
    "DEFAULT_STATUS",
    "create_task",
    "get_task",
    "update_task",
    "snapshot",
    "list_snapshots",
    "get_snapshot",
    "rollback",
    "restore_snapshot",
    "delete_task",
    "complete_task",
    "pause_task",
    "cancel_task",
    "fail_task",
    "resume_task",
    "list_tasks",
    "task_stats",
]