from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LongTermMemoryItem:
    """
    Persistent-style memory representation.

    The current implementation stores data in memory.
    A database adapter can later persist these records.
    """

    id: str
    content: Any

    category: str = "general"
    source: str | None = None

    importance: float = 0.5
    confidence: float = 1.0

    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)

    access_count: int = 0

    metadata: dict[str, Any] = field(default_factory=dict)

    def access(self) -> None:
        self.access_count += 1
        self.last_accessed_at = time.time()

    def update(
        self,
        content: Any | None = None,
        *,
        importance: float | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if content is not None:
            self.content = content

        if importance is not None:
            self.importance = max(0.0, min(1.0, importance))

        if confidence is not None:
            self.confidence = max(0.0, min(1.0, confidence))

        if metadata is not None:
            self.metadata.update(metadata)

        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LongTermMemory:
    """
    Long-term memory manager.

    Provides CRUD, category filtering and simple relevance ranking.
    """

    def __init__(self) -> None:
        self._items: dict[str, LongTermMemoryItem] = {}
        self._lock = threading.RLock()

    def remember(
        self,
        content: Any,
        *,
        category: str = "general",
        source: str | None = None,
        importance: float = 0.5,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
        item_id: str | None = None,
    ) -> LongTermMemoryItem:
        item = LongTermMemoryItem(
            id=item_id or str(uuid.uuid4()),
            content=content,
            category=category,
            source=source,
            importance=max(0.0, min(1.0, importance)),
            confidence=max(0.0, min(1.0, confidence)),
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._items[item.id] = item

        return item

    def get(self, item_id: str) -> LongTermMemoryItem | None:
        with self._lock:
            item = self._items.get(item_id)

            if item is not None:
                item.access()

            return item

    def update(
        self,
        item_id: str,
        content: Any | None = None,
        *,
        importance: float | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LongTermMemoryItem | None:
        with self._lock:
            item = self._items.get(item_id)

            if item is None:
                return None

            item.update(
                content,
                importance=importance,
                confidence=confidence,
                metadata=metadata,
            )

            return item

    def forget(self, item_id: str) -> bool:
        with self._lock:
            return self._items.pop(item_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def by_category(
        self,
        category: str,
    ) -> list[LongTermMemoryItem]:
        with self._lock:
            return [
                item
                for item in self._items.values()
                if item.category == category
            ]

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[LongTermMemoryItem]:
        if not query.strip() or limit <= 0:
            return []

        query_terms = set(query.lower().split())

        scored: list[tuple[float, LongTermMemoryItem]] = []

        with self._lock:
            items = list(self._items.values())

        for item in items:
            if category is not None and item.category != category:
                continue

            text = str(item.content).lower()
            terms = set(text.split())

            overlap = len(query_terms.intersection(terms))

            if overlap == 0:
                continue

            score = (
                overlap * 2.0
                + item.importance
                + item.confidence
                + min(item.access_count / 100.0, 1.0)
            )

            scored.append((score, item))

        scored.sort(
            key=lambda value: value[0],
            reverse=True,
        )

        selected = [item for _, item in scored[:limit]]

        for item in selected:
            item.access()

        return selected

    def all(self) -> list[LongTermMemoryItem]:
        with self._lock:
            return list(self._items.values())

    def export(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                item.to_dict()
                for item in self._items.values()
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def __len__(self) -> int:
        return self.count()