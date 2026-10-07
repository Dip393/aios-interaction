from __future__ import annotations

import copy
import threading
import time
from collections import defaultdict
from typing import Any

from .restore import (
    RestoreEngine,
    RestoreHandlers,
    RestoreResult,
)
from .snapshot import Snapshot


class RollbackManager:
    """
    Central manager for AIOS checkpoints and rollback.

    Responsibilities:

    - Create snapshots
    - Store snapshots
    - Find snapshots
    - Create checkpoint chains
    - Restore snapshots
    - Delete snapshots
    - Maintain rollback history
    - Export/import snapshot state
    """

    def __init__(
        self,
        *,
        max_snapshots: int = 100,
        restore_handlers: RestoreHandlers | None = None,
    ) -> None:
        if max_snapshots <= 0:
            raise ValueError(
                "max_snapshots must be greater than zero."
            )

        self.max_snapshots = max_snapshots

        self._snapshots: dict[
            str,
            Snapshot,
        ] = {}

        self._session_index: dict[
            str,
            list[str],
        ] = defaultdict(list)

        self._task_index: dict[
            str,
            list[str],
        ] = defaultdict(list)

        self._environment_index: dict[
            str,
            list[str],
        ] = defaultdict(list)

        self._restore_engine = RestoreEngine(
            restore_handlers
        )

        self._lock = threading.RLock()

    @property
    def restore_engine(
        self,
    ) -> RestoreEngine:
        return self._restore_engine

    def configure_restore_handlers(
        self,
        handlers: RestoreHandlers,
    ) -> None:
        """
        Replace restore handlers.
        """

        with self._lock:
            self._restore_engine = RestoreEngine(
                handlers
            )

    def create_snapshot(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
        label: str = "",
        description: str = "",
        context_state: dict[str, Any] | None = None,
        environment_state: dict[str, Any] | None = None,
        memory_state: dict[str, Any] | None = None,
        execution_state: dict[str, Any] | None = None,
        custom_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        parent_snapshot_id: str | None = None,
    ) -> Snapshot:
        """
        Create and store a new snapshot.
        """

        if (
            parent_snapshot_id is not None
            and parent_snapshot_id
            not in self._snapshots
        ):
            raise ValueError(
                "Parent snapshot does not exist."
            )

        snapshot = Snapshot(
            snapshot_id=self._generate_snapshot_id(),
            created_at=time.time(),
            session_id=session_id,
            task_id=task_id,
            environment_id=environment_id,
            label=label,
            description=description,
            context_state=copy.deepcopy(
                context_state or {}
            ),
            environment_state=copy.deepcopy(
                environment_state or {}
            ),
            memory_state=copy.deepcopy(
                memory_state or {}
            ),
            execution_state=copy.deepcopy(
                execution_state or {}
            ),
            custom_state=copy.deepcopy(
                custom_state or {}
            ),
            metadata=copy.deepcopy(
                metadata or {}
            ),
            parent_snapshot_id=(
                parent_snapshot_id
            ),
        )

        with self._lock:
            self._snapshots[
                snapshot.snapshot_id
            ] = snapshot

            self._index_snapshot(
                snapshot
            )

            self._enforce_limit()

        return snapshot.clone()

    def checkpoint(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
        label: str = "checkpoint",
        description: str = "",
        context_state: dict[str, Any] | None = None,
        environment_state: dict[str, Any] | None = None,
        memory_state: dict[str, Any] | None = None,
        execution_state: dict[str, Any] | None = None,
        custom_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Snapshot:
        """
        Create a checkpoint automatically linked to the latest
        relevant snapshot.
        """

        parent = self.latest(
            session_id=session_id,
            task_id=task_id,
            environment_id=environment_id,
        )

        return self.create_snapshot(
            session_id=session_id,
            task_id=task_id,
            environment_id=environment_id,
            label=label,
            description=description,
            context_state=context_state,
            environment_state=environment_state,
            memory_state=memory_state,
            execution_state=execution_state,
            custom_state=custom_state,
            metadata=metadata,
            parent_snapshot_id=(
                parent.snapshot_id
                if parent is not None
                else None
            ),
        )

    def get(
        self,
        snapshot_id: str,
    ) -> Snapshot | None:
        with self._lock:
            snapshot = self._snapshots.get(
                snapshot_id
            )

            if snapshot is None:
                return None

            return snapshot.clone()

    def require(
        self,
        snapshot_id: str,
    ) -> Snapshot:
        snapshot = self.get(snapshot_id)

        if snapshot is None:
            raise KeyError(
                f"Snapshot not found: {snapshot_id}"
            )

        return snapshot

    def latest(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
    ) -> Snapshot | None:
        """
        Return the latest matching snapshot.
        """

        with self._lock:
            snapshots = list(
                self._snapshots.values()
            )

        matching = [
            snapshot
            for snapshot in snapshots
            if snapshot.matches(
                session_id=session_id,
                task_id=task_id,
                environment_id=environment_id,
            )
        ]

        if not matching:
            return None

        matching.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )

        return matching[0].clone()

    def list(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
        label: str | None = None,
        limit: int | None = None,
    ) -> list[Snapshot]:
        with self._lock:
            snapshots = list(
                self._snapshots.values()
            )

        result = []

        for snapshot in snapshots:
            if not snapshot.matches(
                session_id=session_id,
                task_id=task_id,
                environment_id=environment_id,
            ):
                continue

            if (
                label is not None
                and snapshot.label != label
            ):
                continue

            result.append(
                snapshot
            )

        result.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )

        if limit is not None:
            limit = max(0, limit)
            result = result[:limit]

        return [
            snapshot.clone()
            for snapshot in result
        ]

    def restore(
        self,
        snapshot_id: str,
        *,
        restore_context: bool = True,
        restore_environment: bool = True,
        restore_memory: bool = True,
        restore_execution: bool = True,
        restore_custom: bool = True,
    ) -> RestoreResult:
        """
        Restore a snapshot by ID.
        """

        snapshot = self.require(
            snapshot_id
        )

        return self._restore_engine.restore(
            snapshot,
            restore_context=restore_context,
            restore_environment=(
                restore_environment
            ),
            restore_memory=restore_memory,
            restore_execution=(
                restore_execution
            ),
            restore_custom=restore_custom,
        )

    def rollback(
        self,
        *,
        session_id: str | None = None,
        task_id: str | None = None,
        environment_id: str | None = None,
        steps: int = 1,
        restore_context: bool = True,
        restore_environment: bool = True,
        restore_memory: bool = True,
        restore_execution: bool = True,
        restore_custom: bool = True,
    ) -> RestoreResult:
        """
        Roll back N snapshots from the latest matching state.

        steps=1 means the immediately previous checkpoint.
        """

        if steps <= 0:
            raise ValueError(
                "steps must be greater than zero."
            )

        snapshots = self.list(
            session_id=session_id,
            task_id=task_id,
            environment_id=environment_id,
        )

        if len(snapshots) < steps:
            raise ValueError(
                "Not enough snapshots available "
                "for requested rollback."
            )

        target = snapshots[
            steps - 1
        ]

        return self.restore(
            target.snapshot_id,
            restore_context=restore_context,
            restore_environment=(
                restore_environment
            ),
            restore_memory=restore_memory,
            restore_execution=(
                restore_execution
            ),
            restore_custom=restore_custom,
        )

    def remove(
        self,
        snapshot_id: str,
    ) -> bool:
        """
        Delete a snapshot.
        """

        with self._lock:
            snapshot = self._snapshots.pop(
                snapshot_id,
                None,
            )

            if snapshot is None:
                return False

            self._remove_from_indexes(
                snapshot
            )

            return True

    def clear(
        self,
    ) -> None:
        """
        Delete all snapshots.
        """

        with self._lock:
            self._snapshots.clear()
            self._session_index.clear()
            self._task_index.clear()
            self._environment_index.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._snapshots)

    def export(
        self,
    ) -> list[dict[str, Any]]:
        """
        Export all snapshots.
        """

        with self._lock:
            snapshots = list(
                self._snapshots.values()
            )

        snapshots.sort(
            key=lambda item: item.created_at
        )

        return [
            snapshot.to_dict()
            for snapshot in snapshots
        ]

    def import_snapshots(
        self,
        data: list[
            dict[str, Any]
        ],
        *,
        replace: bool = False,
    ) -> int:
        """
        Import serialized snapshots.

        Returns the number of imported snapshots.
        """

        imported = 0

        with self._lock:
            if replace:
                self.clear()

            for item in data:
                snapshot = Snapshot.from_dict(
                    item
                )

                if (
                    snapshot.snapshot_id
                    in self._snapshots
                ):
                    continue

                self._snapshots[
                    snapshot.snapshot_id
                ] = snapshot

                self._index_snapshot(
                    snapshot
                )

                imported += 1

            self._enforce_limit()

        return imported

    def chain(
        self,
        snapshot_id: str,
    ) -> list[Snapshot]:
        """
        Return the parent chain ending at the supplied snapshot.
        """

        result: list[Snapshot] = []

        current = self.get(
            snapshot_id
        )

        visited: set[str] = set()

        while current is not None:
            if current.snapshot_id in visited:
                break

            visited.add(
                current.snapshot_id
            )

            result.append(
                current.clone()
            )

            if (
                current.parent_snapshot_id
                is None
            ):
                break

            current = self.get(
                current.parent_snapshot_id
            )

        return result

    def _generate_snapshot_id(
        self,
    ) -> str:
        import uuid

        return (
            f"snapshot-"
            f"{int(time.time() * 1000)}-"
            f"{uuid.uuid4().hex[:8]}"
        )

    def _index_snapshot(
        self,
        snapshot: Snapshot,
    ) -> None:
        if snapshot.session_id:
            self._session_index[
                snapshot.session_id
            ].append(
                snapshot.snapshot_id
            )

        if snapshot.task_id:
            self._task_index[
                snapshot.task_id
            ].append(
                snapshot.snapshot_id
            )

        if snapshot.environment_id:
            self._environment_index[
                snapshot.environment_id
            ].append(
                snapshot.snapshot_id
            )

    def _remove_from_indexes(
        self,
        snapshot: Snapshot,
    ) -> None:
        if snapshot.session_id:
            self._remove_id(
                self._session_index,
                snapshot.session_id,
                snapshot.snapshot_id,
            )

        if snapshot.task_id:
            self._remove_id(
                self._task_index,
                snapshot.task_id,
                snapshot.snapshot_id,
            )

        if snapshot.environment_id:
            self._remove_id(
                self._environment_index,
                snapshot.environment_id,
                snapshot.snapshot_id,
            )

    @staticmethod
    def _remove_id(
        index: dict[
            str,
            list[str],
        ],
        key: str,
        snapshot_id: str,
    ) -> None:
        values = index.get(key)

        if not values:
            return

        try:
            values.remove(
                snapshot_id
            )
        except ValueError:
            return

        if not values:
            index.pop(
                key,
                None,
            )

    def _enforce_limit(
        self,
    ) -> None:
        while (
            len(self._snapshots)
            > self.max_snapshots
        ):
            oldest = min(
                self._snapshots.values(),
                key=lambda item: item.created_at,
            )

            self._snapshots.pop(
                oldest.snapshot_id,
                None,
            )

            self._remove_from_indexes(
                oldest
            )

    def stats(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            return {
                "total_snapshots": len(
                    self._snapshots
                ),
                "max_snapshots": (
                    self.max_snapshots
                ),
                "sessions": len(
                    self._session_index
                ),
                "tasks": len(
                    self._task_index
                ),
                "environments": len(
                    self._environment_index
                ),
            }