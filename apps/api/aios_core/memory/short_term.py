from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass
class MemoryItem:
    """
    A single memory entry.
    """

    id: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    source: str | None = None
    memory_type: str = "general"
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def age_seconds(self) -> float:
        return max(0.0, time.time() - self.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ShortTermMemory:
    """
    Short-term conversational memory.

    Stores recent interactions/events using a bounded deque.
    """

    def __init__(self, max_items: int = 100) -> None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than zero.")

        self.max_items = max_items
        self._items: deque[MemoryItem] = deque(maxlen=max_items)
        self._lock = threading.RLock()

    def add(
        self,
        content: Any,
        *,
        source: str | None = None,
        memory_type: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
        item_id: str | None = None,
    ) -> MemoryItem:
        item = MemoryItem(
            id=item_id or str(uuid.uuid4()),
            content=content,
            source=source,
            memory_type=memory_type,
            importance=max(0.0, min(1.0, importance)),
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._items.append(item)

        return item

    def add_many(
        self,
        contents: Iterable[Any],
        **kwargs: Any,
    ) -> list[MemoryItem]:
        return [self.add(content, **kwargs) for content in contents]

    def latest(self, limit: int = 10) -> list[MemoryItem]:
        if limit <= 0:
            return []

        with self._lock:
            items = list(self._items)

        return items[-limit:][::-1]

    def get(self, item_id: str) -> MemoryItem | None:
        with self._lock:
            for item in self._items:
                if item.id == item_id:
                    return item

        return None

    def remove(self, item_id: str) -> bool:
        with self._lock:
            for index, item in enumerate(self._items):
                if item.id == item_id:
                    del self._items[index]
                    return True

        return False

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def search(self, query: str, limit: int = 10) -> list[MemoryItem]:
        if not query.strip() or limit <= 0:
            return []

        query_terms = set(query.lower().split())

        scored: list[tuple[float, MemoryItem]] = []

        with self._lock:
            items = list(self._items)

        for item in items:
            text = str(item.content).lower()
            terms = set(text.split())

            overlap = len(query_terms.intersection(terms))

            if overlap:
                score = overlap + item.importance
                scored.append((score, item))

        scored.sort(key=lambda value: value[0], reverse=True)

        return [item for _, item in scored[:limit]]

    def prune(self, max_age_seconds: float) -> int:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative.")

        removed = 0

        with self._lock:
            kept: deque[MemoryItem] = deque(maxlen=self.max_items)

            for item in self._items:
                if item.age_seconds() <= max_age_seconds:
                    kept.append(item)
                else:
                    removed += 1

            self._items = kept

        return removed

    def export(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item.to_dict() for item in self._items]

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def __len__(self) -> int:
        return self.count()