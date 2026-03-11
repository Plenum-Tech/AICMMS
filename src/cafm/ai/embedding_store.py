"""Abstract vector/embedding storage interface.

Provides the contract for storing and searching embeddings for the
NLP chatbot and semantic search features. Concrete implementations
can use pgvector, ChromaDB, Pinecone, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingItem:
    """An item to store in the embedding store."""
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    source_type: str | None = None  # e.g., "asset", "work_order", "inspection"
    source_id: str | None = None


@dataclass
class SimilarityResult:
    """A result from a similarity search."""
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class EmbeddingStore(ABC):
    """Abstract interface for vector/embedding storage.

    Implementations:
      - InMemoryEmbeddingStore (for development/testing)
      - PgVectorEmbeddingStore (PostgreSQL + pgvector)
      - ChromaEmbeddingStore (ChromaDB)
      - Custom implementations via plugin
    """

    @abstractmethod
    async def store_embeddings(self, items: list[EmbeddingItem]) -> int:
        """Store embedding items. Returns count stored."""
        ...

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SimilarityResult]:
        """Search for similar items by embedding vector."""
        ...

    @abstractmethod
    async def delete_embeddings(self, ids: list[str]) -> int:
        """Delete embeddings by their IDs. Returns count deleted."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return total number of stored embeddings."""
        ...


class InMemoryEmbeddingStore(EmbeddingStore):
    """Simple in-memory embedding store for development and testing.

    Uses brute-force cosine similarity. Not suitable for production.
    """

    def __init__(self) -> None:
        self._store: dict[str, EmbeddingItem] = {}

    async def store_embeddings(self, items: list[EmbeddingItem]) -> int:
        for item in items:
            self._store[item.id] = item
        return len(items)

    async def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SimilarityResult]:
        results: list[tuple[float, EmbeddingItem]] = []

        for item in self._store.values():
            # Apply metadata filters
            if filters:
                if not all(item.metadata.get(k) == v for k, v in filters.items()):
                    continue

            score = self._cosine_similarity(query_embedding, item.embedding)
            results.append((score, item))

        results.sort(key=lambda x: x[0], reverse=True)

        return [
            SimilarityResult(
                id=item.id,
                text=item.text,
                score=score,
                metadata=item.metadata,
            )
            for score, item in results[:top_k]
        ]

    async def delete_embeddings(self, ids: list[str]) -> int:
        count = 0
        for id_ in ids:
            if id_ in self._store:
                del self._store[id_]
                count += 1
        return count

    async def count(self) -> int:
        return len(self._store)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
