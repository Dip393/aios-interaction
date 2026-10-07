from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Snapshot:
    """
    Immutable-style checkpoint of AIOS runtime state.

    A snapshot contains enough information to restore a previous
    state of a task/session/environment.
    """

    snapshot_id: str

    created_at: float

    session_id: str | None = None

    task_id: str | None = None

    environment_id: str | None = None

    label: str = ""

    description: str = ""

    context_state: dict[str, Any] = field(
        default_factory=dict
    )

    environment_state: dict[str, Any] = field(
        default_factory=dict
    )

    memory_state: dict[str, Any] = field(
        default_factory=dict
    )

    execution_state: dict[str, Any] = field(
        default_factory=dict
    )

    custom_state: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    parent_snapshot_id: str | None = None

    def clone(self) -> "Snapshot":
        """
        Return a deep copy of this snapshot.
        """

        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the snapshot into a dictionary.
        """

        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "environment_id": self.environment_id,
            "label": self.label,
            "description": self.description,
            "context_state": copy.deepcopy(
                self.context_state
            ),
            "environment_state": copy.deepcopy(
                self.environment_state
            ),
            "memory_state": copy.deepcopy(
                self.memory_state
            ),
            "execution_state": copy.deepcopy(
                self.execution_state
            ),
            "custom_state": copy.deepcopy(
                self.custom_state
            ),
            "metadata": copy.deepcopy(
                self.metadata
            ),
            "parent_snapshot_id": (
                self.parent_snapshot_id
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Snapshot":
        """
        Reconstruct a Snapshot from serialized data.
        """

        return cls(
            snapshot_id=str(
                data.get(
                    "snapshot_id",
                    str(uuid.uuid4()),
                )
            ),
            created_at=float(
                data.get(
                    "created_at",
                    time.time(),
                )
            ),
            session_id=data.get(
                "session_id"
            ),
            task_id=data.get(
                "task_id"
            ),
            environment_id=data.get(
                "environment_id"
            ),
            label=str(
                data.get(
                    "label",
                    "",
                )
            ),
            description=str(
                data.get(
                    "description",
                    "",
                )
            ),
            context_state=copy.deepcopy(
                data.get(
                    "context_state",
                    {},
                )
            ),
            environment_state=copy.deepcopy(
                data.get(
                    "environment_state",
                    {},
                )
            ),
            memory_state=copy.deepcopy(
                data.get(
                    "memory_state",
                    {},
                )
            ),
            execution_state=copy.deepcopy(
                data.get(
                    "execution_state",
                    {},
                )
            ),
            custom_state=copy.deepcopy(
                data.get(
                    "custom_state",
                    {},
                )
            ),
            metadata=copy.deepcopy(
                data.get(
                    "metadata",
                    {},
                )
            ),
            parent_snapshot_id=data.get(
                "parent_snapshot_id"
            ),
        )

    def matches(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
    ) -> bool:
        """
        Check whether this snapshot belongs to the supplied
        runtime identifiers.

        None means "do not filter by this field".
        """

        if (
            session_id is not None
            and self.session_id != session_id
        ):
            return False

        if (
            task_id is not None
            and self.task_id != task_id
        ):
            return False

        if (
            environment_id is not None
            and self.environment_id
            != environment_id
        ):
            return False

        return True