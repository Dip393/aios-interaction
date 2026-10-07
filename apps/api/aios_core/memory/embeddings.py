from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Iterable, Sequence


class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""


class BaseEmbedder:
    """
    Base interface for embedding providers.

    External embedding providers can later implement this interface.
    The default AIOS implementation is completely local.
    """

    dimension: int = 0

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def similarity(
        self,
        first: Sequence[float],
        second: Sequence[float],
    ) -> float:
        if len(first) != len(second):
            raise EmbeddingError("Embedding dimensions do not match.")

        if not first or not second:
            return 0.0

        dot = sum(a * b for a, b in zip(first, second))
        norm_a = math.sqrt(sum(a * a for a in first))
        norm_b = math.sqrt(sum(b * b for b in second))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot / (norm_a * norm_b)


class HashEmbedding(BaseEmbedder):
    """
    Lightweight deterministic local embedding.

    This is NOT intended to compete with transformer embeddings.
    It provides a dependency-free semantic-ish representation that is
    useful for local development, testing and basic similarity search.

    The same text always produces the same vector.
    """

    def __init__(self, dimension: int = 256) -> None:
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive.")

        self.dimension = dimension

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"\b[\w'-]+\b", text.lower())

    def embed(self, text: str) -> list[float]:
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        vector = [0.0] * self.dimension
        tokens = self._tokens(text)

        if not tokens:
            return vector

        counts = Counter(tokens)

        for token, frequency in counts.items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()

            index = int.from_bytes(digest[:4], "big") % self.dimension

            sign = 1.0 if digest[4] % 2 == 0 else -1.0

            weight = 1.0 + math.log1p(frequency)

            vector[index] += sign * weight

        # Add a small character-level signal.
        normalized = re.sub(r"\s+", " ", text.lower()).strip()

        for index in range(max(0, len(normalized) - 2)):
            trigram = normalized[index:index + 3]

            digest = hashlib.md5(trigram.encode("utf-8")).digest()

            bucket = int.from_bytes(digest[:4], "big") % self.dimension

            sign = 1.0 if digest[4] % 2 == 0 else -1.0

            vector[bucket] += sign * 0.1

        norm = math.sqrt(sum(value * value for value in vector))

        if norm > 0:
            vector = [value / norm for value in vector]

        return vector


class EmbeddingStore:
    """
    Small in-memory embedding store.

    Used by SemanticMemory for local semantic retrieval.
    """

    def __init__(self, embedder: BaseEmbedder | None = None) -> None:
        self.embedder = embedder or HashEmbedding()
        self._items: dict[str, tuple[str, list[float]]] = {}

    def add(self, item_id: str, text: str) -> list[float]:
        vector = self.embedder.embed(text)
        self._items[item_id] = (text, vector)
        return vector

    def remove(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def get(self, item_id: str) -> tuple[str, list[float]] | None:
        return self._items.get(item_id)

    def clear(self) -> None:
        self._items.clear()

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        threshold: float = -1.0,
    ) -> list[tuple[str, str, float]]:
        if top_k <= 0:
            return []

        query_vector = self.embedder.embed(query)

        results: list[tuple[str, str, float]] = []

        for item_id, (text, vector) in self._items.items():
            score = self.embedder.similarity(query_vector, vector)

            if score >= threshold:
                results.append((item_id, text, score))

        results.sort(key=lambda item: item[2], reverse=True)

        return results[:top_k]

    def __len__(self) -> int:
        return len(self._items)