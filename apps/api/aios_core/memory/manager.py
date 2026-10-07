from __future__ import annotations

import threading
from typing import Any

from .long_term import LongTermMemory, LongTermMemoryItem
from .semantic import SemanticMemory, SemanticMemoryItem
from .short_term import MemoryItem, ShortTermMemory
from .working import WorkingMemory, WorkingMemoryStore


class MemoryManager:
    """
    Unified AIOS memory manager.

    Coordinates:

        Short-Term Memory
              ↓
        Working Memory
              ↓
        Long-Term Memory
              ↓
        Semantic Memory

    The manager provides a single interface to the Kernel/Context layer.
    """

    def __init__(
        self,
        *,
        short_term_limit: int = 100,
    ) -> None:
        self.short_term = ShortTermMemory(
            max_items=short_term_limit,
        )

        self.working = WorkingMemoryStore()
        self.long_term = LongTermMemory()
        self.semantic = SemanticMemory()

        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # SHORT-TERM MEMORY
    # ------------------------------------------------------------------

    def remember_recent(
        self,
        content: Any,
        *,
        source: str | None = None,
        memory_type: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem:
        return self.short_term.add(
            content,
            source=source,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata,
        )

    def recent(
        self,
        limit: int = 10,
    ) -> list[MemoryItem]:
        return self.short_term.latest(limit)

    # ------------------------------------------------------------------
    # WORKING MEMORY
    # ------------------------------------------------------------------

    def create_task_memory(
        self,
        task_id: str,
        goal: str | None = None,
    ) -> WorkingMemory:
        return self.working.create(
            task_id,
            goal,
        )

    def get_task_memory(
        self,
        task_id: str,
    ) -> WorkingMemory:
        return self.working.get_or_create(task_id)

    def clear_task_memory(
        self,
        task_id: str,
    ) -> bool:
        return self.working.delete(task_id)

    # ------------------------------------------------------------------
    # LONG-TERM MEMORY
    # ------------------------------------------------------------------

    def remember(
        self,
        content: Any,
        *,
        category: str = "general",
        source: str | None = None,
        importance: float = 0.5,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> LongTermMemoryItem:
        return self.long_term.remember(
            content,
            category=category,
            source=source,
            importance=importance,
            confidence=confidence,
            metadata=metadata,
        )

    def recall(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[LongTermMemoryItem]:
        return self.long_term.search(
            query,
            category=category,
            limit=limit,
        )

    def forget(
        self,
        memory_id: str,
    ) -> bool:
        semantic_removed = self.semantic.remove(memory_id)
        long_term_removed = self.long_term.forget(memory_id)

        return semantic_removed or long_term_removed

    # ------------------------------------------------------------------
    # SEMANTIC MEMORY
    # ------------------------------------------------------------------

    def remember_semantically(
        self,
        memory_id: str,
        content: str,
        *,
        category: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> SemanticMemoryItem:
        return self.semantic.add(
            memory_id,
            content,
            category=category,
            importance=importance,
            metadata=metadata,
        )

    def semantic_search(
        self,
        query: str,
        *,
        top_k: int = 5,
        threshold: float = 0.0,
        category: str | None = None,
    ) -> list[tuple[SemanticMemoryItem, float]]:
        return self.semantic.search(
            query,
            top_k=top_k,
            threshold=threshold,
            category=category,
        )

    # ------------------------------------------------------------------
    # UNIFIED RECALL
    # ------------------------------------------------------------------

    def recall_all(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search across all memory layers.

        Returns a structured dictionary so the Kernel can decide
        which memories should be included in the current context.
        """

        short_term = self.short_term.search(
            query,
            limit=limit,
        )

        long_term = self.long_term.search(
            query,
            limit=limit,
        )

        semantic = self.semantic.search(
            query,
            top_k=limit,
        )

        return {
            "short_term": short_term,
            "long_term": long_term,
            "semantic": semantic,
        }

    # ------------------------------------------------------------------
    # CONSOLIDATION
    # ------------------------------------------------------------------

    def consolidate_recent(
        self,
        *,
        limit: int = 10,
        category: str = "conversation",
    ) -> list[LongTermMemoryItem]:
        """
        Promote recent short-term memories into long-term memory.

        This is intentionally explicit rather than automatic so that
        a future AI policy layer can decide what deserves persistence.
        """

        recent_items = self.short_term.latest(limit)

        promoted: list[LongTermMemoryItem] = []

        for item in recent_items:
            memory = self.long_term.remember(
                item.content,
                category=category,
                source=item.source,
                importance=item.importance,
                metadata={
                    **item.metadata,
                    "short_term_memory_id": item.id,
                },
            )

            promoted.append(memory)

        return promoted

    # ------------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------------

    def snapshot_task(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        return self.working.snapshot(task_id)

    def restore_task(
        self,
        task_id: str,
        snapshot: dict[str, Any],
    ) -> WorkingMemory:
        return self.working.restore(
            task_id,
            snapshot,
        )

    # ------------------------------------------------------------------
    # EXPORT / IMPORT STYLE DATA
    # ------------------------------------------------------------------

    def export(self) -> dict[str, Any]:
        with self._lock:
            return {
                "short_term": self.short_term.export(),
                "long_term": self.long_term.export(),
                "semantic": self.semantic.export(),
            }

    def clear_all(self) -> None:
        with self._lock:
            self.short_term.clear()
            self.working.clear()
            self.long_term.clear()
            self.semantic.clear()

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, int]:
        return {
            "short_term": self.short_term.count(),
            "working": self.working.count(),
            "long_term": self.long_term.count(),
            "semantic": self.semantic.count(),
        }