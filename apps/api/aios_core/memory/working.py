from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkingMemory:
    """
    Temporary memory associated with the currently active task.

    Unlike short-term memory, working memory is task-oriented.
    """

    task_id: str | None = None
    goal: str | None = None

    variables: dict[str, Any] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    decisions: list[str] = field(default_factory=list)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    completed_actions: list[dict[str, Any]] = field(default_factory=list)

    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.updated_at = time.time()

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value
        self.touch()

    def get_variable(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.variables.get(key, default)

    def remove_variable(self, key: str) -> bool:
        if key not in self.variables:
            return False

        del self.variables[key]
        self.touch()
        return True

    def add_fact(self, key: str, value: Any) -> None:
        self.facts[key] = value
        self.touch()

    def get_fact(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.facts.get(key, default)

    def add_decision(self, decision: str) -> None:
        self.decisions.append(decision)
        self.touch()

    def add_pending_action(self, action: dict[str, Any]) -> None:
        self.pending_actions.append(dict(action))
        self.touch()

    def complete_action(
        self,
        action: dict[str, Any],
    ) -> None:
        action_copy = dict(action)

        self.completed_actions.append(action_copy)

        action_id = action_copy.get("id")

        if action_id is not None:
            self.pending_actions = [
                pending
                for pending in self.pending_actions
                if pending.get("id") != action_id
            ]

        self.touch()

    def clear(self) -> None:
        self.variables.clear()
        self.facts.clear()
        self.decisions.clear()
        self.pending_actions.clear()
        self.completed_actions.clear()

        self.touch()

    def snapshot(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "variables": dict(self.variables),
            "facts": dict(self.facts),
            "decisions": list(self.decisions),
            "pending_actions": [
                dict(action)
                for action in self.pending_actions
            ],
            "completed_actions": [
                dict(action)
                for action in self.completed_actions
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict[str, Any],
    ) -> "WorkingMemory":
        return cls(
            task_id=snapshot.get("task_id"),
            goal=snapshot.get("goal"),
            variables=dict(snapshot.get("variables", {})),
            facts=dict(snapshot.get("facts", {})),
            decisions=list(snapshot.get("decisions", [])),
            pending_actions=[
                dict(action)
                for action in snapshot.get("pending_actions", [])
            ],
            completed_actions=[
                dict(action)
                for action in snapshot.get("completed_actions", [])
            ],
            created_at=snapshot.get("created_at", time.time()),
            updated_at=snapshot.get("updated_at", time.time()),
        )


class WorkingMemoryStore:
    """
    Thread-safe store for task-specific working memories.
    """

    def __init__(self) -> None:
        self._memories: dict[str, WorkingMemory] = {}
        self._lock = threading.RLock()

    def create(
        self,
        task_id: str,
        goal: str | None = None,
    ) -> WorkingMemory:
        memory = WorkingMemory(
            task_id=task_id,
            goal=goal,
        )

        with self._lock:
            self._memories[task_id] = memory

        return memory

    def get(self, task_id: str) -> WorkingMemory | None:
        with self._lock:
            return self._memories.get(task_id)

    def get_or_create(
        self,
        task_id: str,
        goal: str | None = None,
    ) -> WorkingMemory:
        with self._lock:
            existing = self._memories.get(task_id)

            if existing is not None:
                return existing

            return self.create(task_id, goal)

    def delete(self, task_id: str) -> bool:
        with self._lock:
            return self._memories.pop(task_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._memories.clear()

    def snapshot(self, task_id: str) -> dict[str, Any] | None:
        memory = self.get(task_id)

        if memory is None:
            return None

        return memory.snapshot()

    def restore(
        self,
        task_id: str,
        snapshot: dict[str, Any],
    ) -> WorkingMemory:
        memory = WorkingMemory.from_snapshot(snapshot)

        memory.task_id = task_id

        with self._lock:
            self._memories[task_id] = memory

        return memory

    def count(self) -> int:
        with self._lock:
            return len(self._memories)

    def __len__(self) -> int:
        return self.count()