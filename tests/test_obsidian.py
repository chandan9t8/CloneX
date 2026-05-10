import textwrap
from pathlib import Path

import pytest

from ingest.obsidian import _clean_markdown, _strip_frontmatter, load_vault


# ── _strip_frontmatter ────────────────────────────────────────────────────────

def test_strip_frontmatter_present():
    raw = "---\ntitle: Test\ntags: [a, b]\n---\nBody text here."
    fm, body = _strip_frontmatter(raw)
    assert fm == {"title": "Test", "tags": ["a", "b"]}
    assert body == "Body text here."


def test_strip_frontmatter_absent():
    raw = "No frontmatter here.\nJust content."
    fm, body = _strip_frontmatter(raw)
    assert fm == {}
    assert body == raw


def test_strip_frontmatter_malformed_yaml():
    raw = "---\n: bad: yaml:\n---\nBody."
    fm, body = _strip_frontmatter(raw)
    assert fm == {}
    assert body == "Body."


def test_strip_frontmatter_unclosed():
    raw = "---\ntitle: Oops\nno closing fence"
    fm, body = _strip_frontmatter(raw)
    assert fm == {}
    assert body == raw


# ── _clean_markdown ───────────────────────────────────────────────────────────

def test_clean_image_embeds_removed():
    text = "Before\n![[screenshot.png]]\nAfter"
    assert "![[" not in _clean_markdown(text)
    assert "Before" in _clean_markdown(text)
    assert "After" in _clean_markdown(text)


def test_clean_wikilink_simple():
    assert _clean_markdown("See [[Graph Theory]]") == "See Graph Theory"


def test_clean_wikilink_with_alias():
    assert _clean_markdown("Read [[Graph Theory|this note]]") == "Read this note"


def test_clean_multiple_blank_lines_collapsed():
    text = "A\n\n\n\nB"
    result = _clean_markdown(text)
    assert "\n\n\n" not in result


# ── load_vault ────────────────────────────────────────────────────────────────

def test_load_vault_basic(tmp_path):
    (tmp_path / "Notes").mkdir()
    (tmp_path / "Notes" / "Hello.md").write_text("# Hello\nSome content.")

    docs = load_vault(str(tmp_path))
    assert len(docs) == 1
    assert docs[0].title == "Hello"
    assert docs[0].folder == "Notes"
    assert "Some content" in docs[0].text


def test_load_vault_skips_obsidian_dir(tmp_path):
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "config.md").write_text("internal")
    (tmp_path / "Note.md").write_text("Real note.")

    docs = load_vault(str(tmp_path))
    assert len(docs) == 1
    assert docs[0].title == "Note"


def test_load_vault_skips_empty_notes(tmp_path):
    (tmp_path / "Empty.md").write_text("![[image.png]]")  # becomes empty after cleaning
    (tmp_path / "Real.md").write_text("Actual content.")

    docs = load_vault(str(tmp_path))
    titles = [d.title for d in docs]
    assert "Real" in titles
    assert "Empty" not in titles


def test_load_vault_strips_frontmatter(tmp_path):
    (tmp_path / "Note.md").write_text("---\ntags: [ml]\n---\nBody text.")
    docs = load_vault(str(tmp_path))
    assert docs[0].frontmatter == {"tags": ["ml"]}
    assert "tags" not in docs[0].text
    assert "Body text" in docs[0].text


def test_load_vault_nested_folders(tmp_path):
    (tmp_path / "A" / "B").mkdir(parents=True)
    (tmp_path / "A" / "B" / "Deep.md").write_text("Deep content.")

    docs = load_vault(str(tmp_path))
    assert docs[0].folder == "A/B"
