from unittest.mock import MagicMock, patch

import pytest

from ingest.chunker import Chunk
from store.vector_store import VectorStore, _chunk_id


def _chunk(source: str, idx: int, text: str = "some text") -> Chunk:
    return Chunk(
        text=text,
        source=source,
        title="Note",
        folder="DSA",
        heading="Intro",
        chunk_index=idx,
    )


def _fake_embed(texts: list[str]) -> list[list[float]]:
    """Return deterministic unit vectors so we don't need a real API key."""
    return [[float(i % 10) / 10] * 1536 for i, _ in enumerate(texts)]


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("store.vector_store.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        def fake_create(model, input):
            response = MagicMock()
            response.data = [
                MagicMock(embedding=vec) for vec in _fake_embed(input)
            ]
            return response

        mock_client.embeddings.create.side_effect = fake_create
        vs = VectorStore(db_path=str(tmp_path / "db"))
        yield vs


# ── upsert ────────────────────────────────────────────────────────────────────

def test_upsert_returns_count(store):
    chunks = [_chunk("/vault/A.md", i) for i in range(3)]
    assert store.upsert(chunks) == 3


def test_upsert_empty_is_noop(store):
    assert store.upsert([]) == 0
    assert store.count() == 0


def test_upsert_idempotent(store):
    chunks = [_chunk("/vault/A.md", 0, "hello")]
    store.upsert(chunks)
    store.upsert(chunks)   # same ID — should upsert, not duplicate
    assert store.count() == 1


def test_upsert_multiple_chunks_stored(store):
    chunks = [_chunk("/vault/A.md", i) for i in range(5)]
    store.upsert(chunks)
    assert store.count() == 5


# ── search ────────────────────────────────────────────────────────────────────

def test_search_returns_results(store):
    chunks = [_chunk("/vault/A.md", i, f"content {i}") for i in range(5)]
    store.upsert(chunks)
    results = store.search("content", top_k=3)
    assert len(results) == 3


def test_search_result_has_expected_keys(store):
    store.upsert([_chunk("/vault/A.md", 0, "hello world")])
    result = store.search("hello", top_k=1)[0]
    for key in ("text", "score", "title", "folder", "source", "heading", "chunk_index"):
        assert key in result


def test_search_top_k_respected(store):
    chunks = [_chunk("/vault/A.md", i) for i in range(10)]
    store.upsert(chunks)
    assert len(store.search("query", top_k=4)) == 4


# ── chunk ID stability ────────────────────────────────────────────────────────

def test_chunk_id_deterministic():
    c = _chunk("/vault/A.md", 0)
    assert _chunk_id(c) == _chunk_id(c)


def test_chunk_id_unique_per_position():
    c0 = _chunk("/vault/A.md", 0)
    c1 = _chunk("/vault/A.md", 1)
    assert _chunk_id(c0) != _chunk_id(c1)


def test_chunk_id_unique_per_source():
    c0 = _chunk("/vault/A.md", 0)
    c1 = _chunk("/vault/B.md", 0)
    assert _chunk_id(c0) != _chunk_id(c1)
