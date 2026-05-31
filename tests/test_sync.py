from unittest.mock import MagicMock, patch

import pytest

import sync


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "DSA").mkdir()
    (tmp_path / "DSA" / "Trees.md").write_text("# Trees\nA tree is a graph with no cycles.")
    (tmp_path / "DSA" / "Graphs.md").write_text("# Graphs\nNodes connected by edges.")
    (tmp_path / "ML").mkdir()
    (tmp_path / "ML" / "Regression.md").write_text("Linear regression fits a line to data.")
    return tmp_path


@pytest.fixture
def mock_store():
    with patch("sync.VectorStore") as mock_cls:
        instance = MagicMock()
        instance.upsert.return_value = 5
        instance.count.return_value = 5
        mock_cls.return_value = instance
        yield mock_cls, instance


# ── run() return values ───────────────────────────────────────────────────────

def test_run_returns_summary_dict(vault, mock_store):
    result = sync.run(str(vault))
    assert set(result.keys()) == {"notes", "chunks", "upserted"}


def test_run_notes_count(vault, mock_store):
    result = sync.run(str(vault))
    assert result["notes"] == 3


def test_run_chunks_positive(vault, mock_store):
    result = sync.run(str(vault))
    assert result["chunks"] > 0


def test_run_upserted_matches_store_return(vault, mock_store):
    _, instance = mock_store
    instance.upsert.return_value = 7
    result = sync.run(str(vault))
    assert result["upserted"] == 7


# ── VectorStore integration ───────────────────────────────────────────────────

def test_run_calls_upsert_once(vault, mock_store):
    _, instance = mock_store
    sync.run(str(vault))
    instance.upsert.assert_called_once()


def test_run_passes_all_chunks_to_upsert(vault, mock_store):
    _, instance = mock_store
    result = sync.run(str(vault))
    chunks_passed = instance.upsert.call_args[0][0]
    assert len(chunks_passed) == result["chunks"]


def test_run_uses_custom_db_path(vault, mock_store):
    mock_cls, _ = mock_store
    sync.run(str(vault), db_path="/tmp/custom_db")
    mock_cls.assert_called_once_with(db_path="/tmp/custom_db")


# ── error handling ────────────────────────────────────────────────────────────

def test_run_raises_on_missing_vault(mock_store):
    with pytest.raises(ValueError, match="Vault not found"):
        sync.run("/nonexistent/path")


def test_run_empty_vault_produces_zero_chunks(tmp_path, mock_store):
    _, instance = mock_store
    instance.upsert.return_value = 0
    result = sync.run(str(tmp_path))
    assert result["notes"] == 0
    assert result["chunks"] == 0
