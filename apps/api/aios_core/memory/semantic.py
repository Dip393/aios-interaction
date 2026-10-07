from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from .embeddings import BaseEmbedder, EmbeddingStore, HashEmbedding


@dataclass
class SemanticMemoryItem:
    """
    Memory optimized for semantic retrieval.
    """

    id: str
    content: str

    category: str = "general"
    importance: float = 0.5

    metadata: dict[str, Any] = field(default_factory=dict)

    vector: list[float] | None = None


class SemanticMemory:
    """
    Semantic memory layer.

    Stores textual knowledge and their embeddings for similarity search.
    """

    def __init__(
        self,
        embedder: BaseEmbedder | None = None,
    ) -> None:
        self.embedder = embedder or HashEmbedding()
        self.store = EmbeddingStore(self.embedder)

        self._items: dict[str, SemanticMemoryItem] = {}
        self._lock = threading.RLock()

    def add(
        self,
        item_id: str,
        content: str,
        *,
        category: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> SemanticMemoryItem:
        if not content.strip():
            raise ValueError("Semantic memory content cannot be empty.")

        vector = self.embedder.embed(content)

        item = SemanticMemoryItem(
            id=item_id,
            content=content,
            category=category,
            importance=max(0.0, min(1.0, importance)),
            metadata=dict(metadata or {}),
            vector=vector,
        )

        with self._lock:
            self._items[item_id] = item
            self.store.add(item_id, content)

        return item

    def get(
        self,
        item_id: str,
    ) -> SemanticMemoryItem | None:
        with self._lock:
            return self._items.get(item_id)

    def remove(self, item_id: str) -> bool:
        with self._lock:
            removed = self._items.pop(item_id, None)

            if removed is None:
                return False

            self.store.remove(item_id)

            return True

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self.store.clear()

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        threshold: float = 0.0,
        category: str | None = None,
    ) -> list[tuple[SemanticMemoryItem, float]]:
        if not query.strip() or top_k <= 0:
            return []

        raw_results = self.store.search(
            query,
            top_k=max(top_k * 3, top_k),
            threshold=threshold,
        )

        results: list[tuple[SemanticMemoryItem, float]] = []

        with self._lock:
            for item_id, _, score in raw_results:
                item = self._items.get(item_id)

                if item is None:
                    continue

                if category is not None and item.category != category:
                    continue

                results.append((item, score))

        results.sort(
            key=lambda value: (
                value[1],
                value[0].importance,
            ),
            reverse=True,
        )

        return results[:top_k]

    def find_similar(
        self,
        content: str,
        *,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[tuple[SemanticMemoryItem, float]]:
        return self.search(
            content,
            top_k=top_k,
            threshold=threshold,
        )

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def export(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "id": item.id,
                    "content": item.content,
                    "category": item.category,
                    "importance": item.importance,
                    "metadata": dict(item.metadata),
                }
                for item in self._items.values()
            ]

    def __len__(self) -> int:
        return self.count()