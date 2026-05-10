import re
from dataclasses import dataclass

from ingest.obsidian import Document


@dataclass
class Chunk:
    text: str
    source: str
    title: str
    folder: str
    heading: str    # nearest heading above this chunk, "" for preamble
    chunk_index: int


_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)

MAX_CHARS = 1500    # ~375 tokens — safely under 512-token embedding limit
OVERLAP_CHARS = 150


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    """Return [(heading, body), ...] preserving document order."""
    sections: list[tuple[str, str]] = []
    last_heading = ""
    last_pos = 0

    for m in _HEADING_RE.finditer(text):
        body = text[last_pos:m.start()].strip()
        if body:
            sections.append((last_heading, body))
        last_heading = m.group().lstrip("#").strip()
        last_pos = m.end()

    tail = text[last_pos:].strip()
    if tail:
        sections.append((last_heading, tail))

    return sections


def _split_large_section(text: str) -> list[str]:
    """Break an oversized section at paragraph boundaries with overlap."""
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # paragraph is itself too large — hard-split at sentence boundaries
        if len(para) > MAX_CHARS:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(para):
                end = start + MAX_CHARS
                if end < len(para):
                    cut = para.rfind(". ", start, end)
                    cut = cut + 1 if cut != -1 else end
                else:
                    cut = len(para)
                chunks.append(para[start:cut].strip())
                next_start = cut - OVERLAP_CHARS
                start = next_start if next_start > start else cut
            continue

        if len(current) + len(para) + 2 > MAX_CHARS and current:
            chunks.append(current.strip())
            current = current[-OVERLAP_CHARS:] + "\n\n" + para
        else:
            current = (current + "\n\n" + para) if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_document(doc: Document) -> list[Chunk]:
    chunks: list[Chunk] = []
    idx = 0

    for heading, body in _split_by_headings(doc.text):
        parts = [body] if len(body) <= MAX_CHARS else _split_large_section(body)

        for part in parts:
            chunks.append(Chunk(
                text=part,
                source=doc.source,
                title=doc.title,
                folder=doc.folder,
                heading=heading,
                chunk_index=idx,
            ))
            idx += 1

    return chunks
