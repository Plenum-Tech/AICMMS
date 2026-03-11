"""Tests for the in-memory embedding store."""

import pytest
from cafm.ai.embedding_store import EmbeddingItem, InMemoryEmbeddingStore


@pytest.mark.asyncio
async def test_store_and_search():
    store = InMemoryEmbeddingStore()

    items = [
        EmbeddingItem(id="1", text="HVAC maintenance", embedding=[1.0, 0.0, 0.0]),
        EmbeddingItem(id="2", text="Plumbing repair", embedding=[0.0, 1.0, 0.0]),
        EmbeddingItem(id="3", text="AC unit service", embedding=[0.9, 0.1, 0.0]),
    ]
    await store.store_embeddings(items)

    assert await store.count() == 3

    # Search for something similar to HVAC
    results = await store.search_similar([1.0, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].id == "1"  # Exact match
    assert results[0].score > 0.9


@pytest.mark.asyncio
async def test_delete_embeddings():
    store = InMemoryEmbeddingStore()
    await store.store_embeddings([
        EmbeddingItem(id="1", text="test", embedding=[1.0]),
    ])
    deleted = await store.delete_embeddings(["1"])
    assert deleted == 1
    assert await store.count() == 0


@pytest.mark.asyncio
async def test_search_with_filters():
    store = InMemoryEmbeddingStore()
    await store.store_embeddings([
        EmbeddingItem(id="1", text="a", embedding=[1.0, 0.0], metadata={"type": "asset"}),
        EmbeddingItem(id="2", text="b", embedding=[0.9, 0.1], metadata={"type": "wo"}),
    ])
    results = await store.search_similar([1.0, 0.0], top_k=10, filters={"type": "asset"})
    assert len(results) == 1
    assert results[0].id == "1"
