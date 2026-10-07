"""
AIOS Legacy Memory Compatibility Layer.

This module preserves the original memory.py API while the main AIOS
memory system lives in:

    aios_core/memory/

The functions here provide a small database-backed compatibility API for
older routes and services.

Primary memory architecture:

    Short-Term Memory
            │
    Working Memory
            │
    Long-Term Memory
            │
    Semantic Memory
            │
      MemoryManager

This file should NOT contain the complete memory architecture.
It exists mainly for backward compatibility.
"""

from __future__ import annotations

from typing import Any, Optional

from .db import (
    execute,
    json_dumps,
    json_load,
    now,
    row,
    rows,
)


# ============================================================================
# Memory creation
# ============================================================================

def add_memory(
    category: str,
    content: str,
    importance: int = 1,
    metadata: Optional[dict[str, Any]] = None,
) -> int:
    """
    Store a memory in the legacy database-backed memory table.

    This function remains compatible with the original:

        add_memory(category, content, importance)

    Additional metadata is optional.
    """

    category = str(category or "general").strip()
    content = str(content or "").strip()

    if not content:
        raise ValueError(
            "Memory content cannot be empty."
        )

    importance = max(
        0,
        min(
            int(importance),
            10,
        ),
    )

    metadata = metadata or {}

    return execute(
        """
        INSERT INTO memories(
            category,
            content,
            importance,
            created_at,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            category,
            content,
            importance,
            now(),
            json_dumps(metadata),
        ),
    )


# ============================================================================
# Memory retrieval
# ============================================================================

def list_memories(
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return recent memories.

    Newest memories are returned first.
    """

    limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    data = rows(
        """
        SELECT
            id,
            category,
            content,
            importance,
            created_at,
            metadata_json
        FROM memories
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )

    return [
        _normalize_memory(memory)
        for memory in data
    ]


def get_memory(
    memory_id: int,
) -> Optional[dict[str, Any]]:
    """
    Retrieve a single memory by database ID.
    """

    memory = row(
        """
        SELECT
            id,
            category,
            content,
            importance,
            created_at,
            metadata_json
        FROM memories
        WHERE id = ?
        LIMIT 1
        """,
        (memory_id,),
    )

    if memory is None:
        return None

    return _normalize_memory(memory)


# ============================================================================
# Memory search
# ============================================================================

def search_memory(
    q: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search legacy memories using lightweight token matching.

    This intentionally does not require an embedding model.

    The newer semantic memory system is available through:

        MemoryManager.semantic_search(...)
    """

    query = str(q or "").strip()

    if not query:
        return list_memories(limit)

    limit = max(
        1,
        min(
            int(limit),
            100,
        ),
    )

    # Ignore very short tokens because they create noisy matches.
    tokens = [
        token.lower()
        for token in _tokenize(query)
        if len(token) > 2
    ]

    if not tokens:
        return list_memories(limit)

    # Retrieve a bounded candidate set.
    data = list_memories(500)

    scored: list[
        tuple[
            float,
            dict[str, Any],
        ]
    ] = []

    for memory in data:
        content = str(
            memory.get(
                "content",
                "",
            )
        ).lower()

        category = str(
            memory.get(
                "category",
                "",
            )
        ).lower()

        combined = (
            f"{content} {category}"
        )

        score = 0.0

        for token in tokens:
            if token in content:
                score += 2.0
            elif token in category:
                score += 1.0

        # Small bonus when the query contains multiple matching terms.
        matched = sum(
            1
            for token in tokens
            if token in combined
        )

        if matched > 1:
            score += 0.5 * (
                matched - 1
            )

        # Importance slightly influences ranking.
        importance = float(
            memory.get(
                "importance",
                1,
            )
        )

        score += min(
            importance,
            10,
        ) * 0.05

        if score > 0:
            scored.append(
                (
                    score,
                    memory,
                )
            )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].get(
                "created_at",
                "",
            ),
        ),
        reverse=True,
    )

    return [
        memory
        for _, memory in scored[:limit]
    ]


# ============================================================================
# Memory update
# ============================================================================

def update_memory(
    memory_id: int,
    *,
    category: Optional[str] = None,
    content: Optional[str] = None,
    importance: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    """
    Update an existing memory.

    Only supplied fields are changed.
    """

    existing = get_memory(
        memory_id
    )

    if existing is None:
        return None

    fields: list[str] = []
    values: list[Any] = []

    if category is not None:
        category = str(
            category
        ).strip()

        if not category:
            raise ValueError(
                "Memory category cannot be empty."
            )

        fields.append(
            "category = ?"
        )
        values.append(category)

    if content is not None:
        content = str(
            content
        ).strip()

        if not content:
            raise ValueError(
                "Memory content cannot be empty."
            )

        fields.append(
            "content = ?"
        )
        values.append(content)

    if importance is not None:
        importance = max(
            0,
            min(
                int(importance),
                10,
            ),
        )

        fields.append(
            "importance = ?"
        )
        values.append(importance)

    if metadata is not None:
        fields.append(
            "metadata_json = ?"
        )
        values.append(
            json_dumps(metadata)
        )

    if not fields:
        return existing

    values.append(
        memory_id
    )

    execute(
        f"""
        UPDATE memories
        SET {", ".join(fields)}
        WHERE id = ?
        """,
        tuple(values),
    )

    return get_memory(
        memory_id
    )


# ============================================================================
# Memory deletion
# ============================================================================

def delete_memory(
    memory_id: int,
) -> bool:
    """
    Delete one legacy memory.
    """

    existing = get_memory(
        memory_id
    )

    if existing is None:
        return False

    with_memory = execute(
        """
        DELETE FROM memories
        WHERE id = ?
        """,
        (memory_id,),
    )

    return with_memory >= 0


def clear_memories() -> int:
    """
    Delete all legacy memories.

    Returns the number of deleted rows when SQLite provides it.
    """

    existing = rows(
        "SELECT id FROM memories"
    )

    execute(
        "DELETE FROM memories"
    )

    return len(existing)


# ============================================================================
# Search helpers
# ============================================================================

def _tokenize(
    text: str,
) -> list[str]:
    """
    Lightweight tokenizer for local keyword search.
    """

    normalized = (
        text.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("!", " ")
        .replace("?", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("[", " ")
        .replace("]", " ")
        .replace("{", " ")
        .replace("}", " ")
        .replace("/", " ")
        .replace("\\", " ")
        .replace("-", " ")
        .replace("_", " ")
    )

    return [
        token
        for token in normalized.split()
        if token
    ]


def _normalize_memory(
    memory: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a database memory row.

    This keeps the old response shape while exposing metadata.
    """

    result = dict(
        memory
    )

    result["metadata"] = json_load(
        result.pop(
            "metadata_json",
            "{}",
        ),
        default={},
    )

    return result


# ============================================================================
# Compatibility aliases
# ============================================================================

remember = add_memory
recall = search_memory
forget = delete_memory


__all__ = [
    "add_memory",
    "list_memories",
    "get_memory",
    "search_memory",
    "update_memory",
    "delete_memory",
    "clear_memories",
    "remember",
    "recall",
    "forget",
]