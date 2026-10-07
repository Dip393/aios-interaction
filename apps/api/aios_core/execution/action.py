"""
AIOS Executable Action Definitions.

An Action represents one concrete operation that the execution engine can run.

Examples:

    create_file
    write_file
    create_reminder
    send_email
    create_calendar_event
    run_code
"""

from __future__ import annotations

import inspect
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional


def utc_now() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class ActionStatus(str, Enum):
    """Lifecycle states of an executable action."""

    CREATED = "created"
    VALIDATED = "validated"
    WAITING_CONFIRMATION = "waiting_confirmation"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


@dataclass
class ActionDefinition:
    """
    Definition of an executable action.

    This describes what an action is allowed to do.
    """

    name: str

    description: str = ""

    handler: Optional[
        Callable[..., Any]
    ] = None

    rollback_handler: Optional[
        Callable[..., Any]
    ] = None

    risk_level: str = "low"

    reversible: bool = False

    requires_confirmation: bool = False

    external_side_effect: bool = False

    destructive: bool = False

    allowed_in_sandbox: bool = True

    timeout_seconds: float = 60.0

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def has_handler(self) -> bool:
        """Return whether an executable handler exists."""
        return callable(self.handler)

    def has_rollback(self) -> bool:
        """Return whether a rollback handler exists."""
        return callable(self.rollback_handler)


@dataclass
class Action:
    """
    Concrete action instance.

    ActionDefinition describes the capability.
    Action describes one specific execution request.
    """

    name: str

    args: Dict[str, Any] = field(
        default_factory=dict
    )

    kwargs: Dict[str, Any] = field(
        default_factory=dict
    )

    action_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    request_id: Optional[str] = None

    session_id: Optional[str] = None

    user_id: Optional[str] = None

    status: ActionStatus = ActionStatus.CREATED

    created_at: str = field(
        default_factory=utc_now
    )

    started_at: Optional[str] = None

    completed_at: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def mark_running(self) -> None:
        """Mark the action as running."""
        self.status = ActionStatus.RUNNING
        self.started_at = utc_now()

    def mark_success(self) -> None:
        """Mark the action as successfully completed."""
        self.status = ActionStatus.SUCCESS
        self.completed_at = utc_now()

    def mark_failed(self) -> None:
        """Mark the action as failed."""
        self.status = ActionStatus.FAILED
        self.completed_at = utc_now()

    def mark_cancelled(self) -> None:
        """Mark the action as cancelled."""
        self.status = ActionStatus.CANCELLED
        self.completed_at = utc_now()

    def mark_rolled_back(self) -> None:
        """Mark the action as rolled back."""
        self.status = ActionStatus.ROLLED_BACK
        self.completed_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert action into a JSON-friendly dictionary."""

        return {
            "action_id": self.action_id,
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


async def invoke_handler(
    handler: Callable[..., Any],
    action: Action,
    context: Any = None,
) -> Any:
    """
    Invoke an action handler.

    Supported handler styles include:

        handler(action)
        handler(action, context)
        async handler(action)
        async handler(action, context)

    The function inspects the handler signature so that action handlers
    remain flexible.
    """

    if not callable(handler):
        raise TypeError(
            "Action handler must be callable."
        )

    try:
        signature = inspect.signature(handler)
        parameters = list(
            signature.parameters.values()
        )

        positional = [
            parameter
            for parameter in parameters
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        if len(positional) >= 2:
            result = handler(
                action,
                context,
            )
        elif len(positional) == 1:
            result = handler(action)
        else:
            result = handler()

    except (TypeError, ValueError):
        result = handler(
            action,
            context,
        )

    if inspect.isawaitable(result):
        return await result

    return result