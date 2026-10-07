"""
AIOS Environment State.

Stores runtime state separately from the environment definition itself.
"""

from __future__ import annotations

import copy
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EnvironmentState:
    """
    Runtime state of an environment.

    The state can contain:
    - current document
    - selected files
    - current task
    - UI state
    - temporary variables
    - agent results
    """

    environment_id: str

    values: Dict[str, Any] = field(
        default_factory=dict
    )

    history: List[Dict[str, Any]] = field(
        default_factory=list
    )

    active_task_id: Optional[str] = None

    current_view: Optional[str] = None

    focused_element: Optional[str] = None

    created_at: str = field(
        default_factory=utc_now
    )

    updated_at: str = field(
        default_factory=utc_now
    )

    version: int = 1

    def set(
        self,
        key: str,
        value: Any,
        *,
        record_history: bool = True,
    ) -> None:
        """Set runtime state value."""

        previous = self.values.get(
            key
        )

        self.values[key] = value

        if record_history:
            self.history.append(
                {
                    "id": str(
                        uuid.uuid4()
                    ),
                    "operation": "set",
                    "key": key,
                    "previous": previous,
                    "value": value,
                    "timestamp": utc_now(),
                }
            )

        self.version += 1
        self.updated_at = utc_now()

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get state value."""

        return self.values.get(
            key,
            default,
        )

    def delete(
        self,
        key: str,
    ) -> Any:
        """Delete state value."""

        previous = self.values.pop(
            key,
            None,
        )

        self.history.append(
            {
                "id": str(
                    uuid.uuid4()
                ),
                "operation": "delete",
                "key": key,
                "previous": previous,
                "timestamp": utc_now(),
            }
        )

        self.version += 1
        self.updated_at = utc_now()

        return previous

    def set_active_task(
        self,
        task_id: Optional[str],
    ) -> None:
        """Set current active task."""

        self.active_task_id = task_id
        self.updated_at = utc_now()
        self.version += 1

    def set_view(
        self,
        view: Optional[str],
    ) -> None:
        """Set current UI view."""

        self.current_view = view
        self.updated_at = utc_now()
        self.version += 1

    def set_focus(
        self,
        element: Optional[str],
    ) -> None:
        """Set currently focused UI element."""

        self.focused_element = element
        self.updated_at = utc_now()
        self.version += 1

    def snapshot(self) -> Dict[str, Any]:
        """Create a deep state snapshot."""

        return {
            "environment_id": self.environment_id,
            "values": copy.deepcopy(
                self.values
            ),
            "history": copy.deepcopy(
                self.history
            ),
            "active_task_id": (
                self.active_task_id
            ),
            "current_view": (
                self.current_view
            ),
            "focused_element": (
                self.focused_element
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    def restore(
        self,
        snapshot: Dict[str, Any],
    ) -> None:
        """Restore state from a snapshot."""

        self.values = copy.deepcopy(
            snapshot.get(
                "values",
                {},
            )
        )

        self.history = copy.deepcopy(
            snapshot.get(
                "history",
                [],
            )
        )

        self.active_task_id = (
            snapshot.get(
                "active_task_id"
            )
        )

        self.current_view = (
            snapshot.get(
                "current_view"
            )
        )

        self.focused_element = (
            snapshot.get(
                "focused_element"
            )
        )

        self.version = int(
            snapshot.get(
                "version",
                self.version,
            )
        )

        self.updated_at = utc_now()


class EnvironmentStateStore:
    """
    Thread-safe in-memory state store.

    A database-backed implementation can replace this later without changing
    the EnvironmentManager interface.
    """

    def __init__(self) -> None:

        self._states: Dict[
            str,
            EnvironmentState,
        ] = {}

        self._lock = threading.RLock()

    def create(
        self,
        environment_id: str,
    ) -> EnvironmentState:
        """Create state for an environment."""

        with self._lock:

            if environment_id in self._states:
                return self._states[
                    environment_id
                ]

            state = EnvironmentState(
                environment_id=environment_id
            )

            self._states[
                environment_id
            ] = state

            return state

    def get(
        self,
        environment_id: str,
    ) -> Optional[
        EnvironmentState
    ]:
        """Get environment state."""

        with self._lock:
            return self._states.get(
                environment_id
            )

    def require(
        self,
        environment_id: str,
    ) -> EnvironmentState:
        """Get state or create it."""

        with self._lock:

            state = self._states.get(
                environment_id
            )

            if state is None:
                state = self.create(
                    environment_id
                )

            return state

    def delete(
        self,
        environment_id: str,
    ) -> bool:
        """Delete environment state."""

        with self._lock:
            return (
                self._states.pop(
                    environment_id,
                    None,
                )
                is not None
            )

    def snapshot(
        self,
        environment_id: str,
    ) -> Optional[
        Dict[str, Any]
    ]:
        """Get a state snapshot."""

        state = self.get(
            environment_id
        )

        if state is None:
            return None

        return state.snapshot()

    def restore(
        self,
        environment_id: str,
        snapshot: Dict[str, Any],
    ) -> EnvironmentState:
        """Restore state from a snapshot."""

        state = self.require(
            environment_id
        )

        state.restore(
            snapshot
        )

        return state

    def list_states(self) -> List[
        EnvironmentState
    ]:
        """List all environment states."""

        with self._lock:
            return list(
                self._states.values()
            )

    def clear(self) -> None:
        """Clear all states."""

        with self._lock:
            self._states.clear()