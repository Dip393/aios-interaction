"""
AIOS Execution Results.

All execution operations return ExecutionResult so that the kernel,
planner, UI and future observability system can consume a consistent format.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class ExecutionStatus(str, Enum):
    """Execution result states."""

    SUCCESS = "success"
    FAILED = "failed"
    VALIDATION_FAILED = "validation_failed"
    DENIED = "denied"
    NEEDS_CONFIRMATION = "needs_confirmation"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    SANDBOX_VIOLATION = "sandbox_violation"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionResult:
    """Standard result returned by the execution engine."""

    success: bool

    status: ExecutionStatus

    action_name: str

    action_id: Optional[str] = None

    message: str = ""

    data: Any = None

    error: Optional[str] = None

    request_id: Optional[str] = None

    rollback_available: bool = False

    rollback_token: Optional[str] = None

    requires_confirmation: bool = False

    confirmation_reason: Optional[str] = None

    duration_ms: Optional[float] = None

    logs: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_now
    )

    result_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    def add_log(
        self,
        message: str,
    ) -> None:
        """Append an execution log."""
        self.logs.append(
            str(message)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a JSON-friendly dictionary."""

        return {
            "result_id": self.result_id,
            "success": self.success,
            "status": self.status.value,
            "action_name": self.action_name,
            "action_id": self.action_id,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "request_id": self.request_id,
            "rollback_available": self.rollback_available,
            "rollback_token": self.rollback_token,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_reason": self.confirmation_reason,
            "duration_ms": self.duration_ms,
            "logs": self.logs,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def success_result(
        cls,
        action_name: str,
        message: str = "",
        data: Any = None,
        **kwargs: Any,
    ) -> "ExecutionResult":
        """Create a successful result."""

        return cls(
            success=True,
            status=ExecutionStatus.SUCCESS,
            action_name=action_name,
            message=message,
            data=data,
            **kwargs,
        )

    @classmethod
    def failure_result(
        cls,
        action_name: str,
        message: str = "",
        error: Optional[str] = None,
        **kwargs: Any,
    ) -> "ExecutionResult":
        """Create a failed result."""

        return cls(
            success=False,
            status=ExecutionStatus.FAILED,
            action_name=action_name,
            message=message,
            error=error,
            **kwargs,
        )

    @classmethod
    def confirmation_required(
        cls,
        action_name: str,
        reason: str,
        data: Any = None,
        **kwargs: Any,
    ) -> "ExecutionResult":
        """Create a confirmation-required result."""

        return cls(
            success=False,
            status=ExecutionStatus.NEEDS_CONFIRMATION,
            action_name=action_name,
            message="Explicit confirmation is required.",
            data=data,
            requires_confirmation=True,
            confirmation_reason=reason,
            **kwargs,
        )