from ingest.chunker import MAX_CHARS, OVERLAP_CHARS, chunk_document
from ingest.obsidian import Document


def _doc(text: str, title: str = "Note", folder: str = "root") -> Document:
    return Document(text=text, source=f"/vault/{title}.md", title=title, folder=folder)


# ── heading-based splitting ───────────────────────────────────────────────────

def test_single_section_no_heading():
    doc = _doc("Just some plain text with no headings.")
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].heading == ""
    assert chunks[0].chunk_index == 0


def test_multiple_headings_produce_separate_chunks():
    doc = _doc("## Alpha\nContent A.\n\n## Beta\nContent B.")
    chunks = chunk_document(doc)
    headings = [c.heading for c in chunks]
    assert "Alpha" in headings
    assert "Beta" in headings


def test_heading_assigned_to_following_body():
    doc = _doc("## My Section\nThis is the body.")
    chunks = chunk_document(doc)
    assert chunks[0].heading == "My Section"
    assert "body" in chunks[0].text


def test_preamble_before_first_heading_gets_empty_heading():
    doc = _doc("Intro text.\n\n## Section\nBody.")
    chunks = chunk_document(doc)
    assert chunks[0].heading == ""
    assert "Intro" in chunks[0].text


def test_chunk_indices_are_sequential():
    doc = _doc("## A\nText A.\n\n## B\nText B.\n\n## C\nText C.")
    chunks = chunk_document(doc)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


# ── oversized section splitting ───────────────────────────────────────────────

def test_large_section_is_split():
    big_para = "word " * 400       # ~2000 chars — over MAX_CHARS
    doc = _doc(f"## Big\n{big_para}")
    chunks = chunk_document(doc)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= MAX_CHARS + OVERLAP_CHARS


def test_overlap_carries_tail_of_previous_chunk():
    # build a section with two clearly distinct paragraphs, each near MAX_CHARS
    para_a = "A " * (MAX_CHARS // 2)
    para_b = "B " * (MAX_CHARS // 2)
    doc = _doc(f"## Sec\n{para_a}\n\n{para_b}")
    chunks = chunk_document(doc)
    assert len(chunks) == 2
    # second chunk should start with tail of first (overlap)
    assert chunks[1].text[:OVERLAP_CHARS].strip() != ""


# ── metadata propagation ──────────────────────────────────────────────────────

def test_metadata_propagated_to_all_chunks():
    doc = _doc("## X\nFoo.\n\n## Y\nBar.", title="MyNote", folder="DSA")
    chunks = chunk_document(doc)
    for c in chunks:
        assert c.title == "MyNote"
        assert c.folder == "DSA"
        assert c.source == "/vault/MyNote.md"


def test_empty_document_produces_no_chunks():
    doc = _doc("")
    chunks = chunk_document(doc)
    assert chunks == []
