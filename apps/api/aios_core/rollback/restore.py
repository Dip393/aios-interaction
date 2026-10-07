from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .snapshot import Snapshot


class RestoreError(Exception):
    """
    Base exception for restore failures.
    """


class RestoreValidationError(RestoreError):
    """
    Raised when a snapshot cannot safely be restored.
    """


@dataclass
class RestoreResult:
    """
    Result of a restore operation.
    """

    success: bool

    snapshot_id: str

    restored_at: float = field(
        default_factory=time.time
    )

    message: str = ""

    restored_context: bool = False

    restored_environment: bool = False

    restored_memory: bool = False

    restored_execution: bool = False

    restored_custom: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "snapshot_id": self.snapshot_id,
            "restored_at": self.restored_at,
            "message": self.message,
            "restored_context": (
                self.restored_context
            ),
            "restored_environment": (
                self.restored_environment
            ),
            "restored_memory": (
                self.restored_memory
            ),
            "restored_execution": (
                self.restored_execution
            ),
            "restored_custom": (
                self.restored_custom
            ),
            "metadata": copy.deepcopy(
                self.metadata
            ),
        }


@dataclass
class RestoreHandlers:
    """
    Optional callbacks used by RestoreEngine.

    Each callback receives the corresponding snapshot state.

    Example:

        handlers = RestoreHandlers(
            context=restore_context,
            environment=restore_environment,
        )
    """

    context: Callable[
        [dict[str, Any]],
        Any,
    ] | None = None

    environment: Callable[
        [dict[str, Any]],
        Any,
    ] | None = None

    memory: Callable[
        [dict[str, Any]],
        Any,
    ] | None = None

    execution: Callable[
        [dict[str, Any]],
        Any,
    ] | None = None

    custom: Callable[
        [dict[str, Any]],
        Any,
    ] | None = None


class RestoreEngine:
    """
    Responsible for validating and restoring snapshots.

    The engine itself does not know how Context, Environment,
    Memory or Execution objects are implemented.

    It delegates restoration to registered handlers.
    """

    def __init__(
        self,
        handlers: RestoreHandlers | None = None,
    ) -> None:
        self.handlers = (
            handlers
            if handlers is not None
            else RestoreHandlers()
        )

    @staticmethod
    def validate(
        snapshot: Snapshot,
    ) -> None:
        if not snapshot.snapshot_id:
            raise RestoreValidationError(
                "Snapshot ID is missing."
            )

        if snapshot.created_at <= 0:
            raise RestoreValidationError(
                "Snapshot timestamp is invalid."
            )

        if not isinstance(
            snapshot.context_state,
            dict,
        ):
            raise RestoreValidationError(
                "Invalid context state."
            )

        if not isinstance(
            snapshot.environment_state,
            dict,
        ):
            raise RestoreValidationError(
                "Invalid environment state."
            )

        if not isinstance(
            snapshot.memory_state,
            dict,
        ):
            raise RestoreValidationError(
                "Invalid memory state."
            )

        if not isinstance(
            snapshot.execution_state,
            dict,
        ):
            raise RestoreValidationError(
                "Invalid execution state."
            )

        if not isinstance(
            snapshot.custom_state,
            dict,
        ):
            raise RestoreValidationError(
                "Invalid custom state."
            )

    def restore(
        self,
        snapshot: Snapshot,
        *,
        restore_context: bool = True,
        restore_environment: bool = True,
        restore_memory: bool = True,
        restore_execution: bool = True,
        restore_custom: bool = True,
    ) -> RestoreResult:
        """
        Restore selected portions of a snapshot.

        A missing handler means that the corresponding state is
        considered restored into the result's local runtime state,
        but no external object is modified.

        This makes the engine safe to use before all AIOS services
        are fully wired together.
        """

        self.validate(snapshot)

        restored_context = False
        restored_environment = False
        restored_memory = False
        restored_execution = False
        restored_custom = False

        if restore_context:
            if self.handlers.context is not None:
                self.handlers.context(
                    copy.deepcopy(
                        snapshot.context_state
                    )
                )

            restored_context = True

        if restore_environment:
            if self.handlers.environment is not None:
                self.handlers.environment(
                    copy.deepcopy(
                        snapshot.environment_state
                    )
                )

            restored_environment = True

        if restore_memory:
            if self.handlers.memory is not None:
                self.handlers.memory(
                    copy.deepcopy(
                        snapshot.memory_state
                    )
                )

            restored_memory = True

        if restore_execution:
            if self.handlers.execution is not None:
                self.handlers.execution(
                    copy.deepcopy(
                        snapshot.execution_state
                    )
                )

            restored_execution = True

        if restore_custom:
            if self.handlers.custom is not None:
                self.handlers.custom(
                    copy.deepcopy(
                        snapshot.custom_state
                    )
                )

            restored_custom = True

        return RestoreResult(
            success=True,
            snapshot_id=snapshot.snapshot_id,
            message=(
                "Snapshot restored successfully."
            ),
            restored_context=restored_context,
            restored_environment=(
                restored_environment
            ),
            restored_memory=restored_memory,
            restored_execution=(
                restored_execution
            ),
            restored_custom=restored_custom,
        )