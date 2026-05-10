import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Document:
    text: str
    source: str          # absolute file path
    title: str           # filename without extension
    folder: str          # vault-relative folder
    frontmatter: dict = field(default_factory=dict)


def _strip_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) — frontmatter is {} when absent."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    try:
        fm = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, text[end + 4:].lstrip("\n")


def _clean_markdown(text: str) -> str:
    # drop image embeds: ![[...]]
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    # convert note links [[note|alias]] or [[note]] → alias or note
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    # collapse blank lines left by removed embeds
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_vault(vault_path: str) -> list[Document]:
    vault = Path(vault_path)
    docs: list[Document] = []

    for md_file in vault.rglob("*.md"):
        # skip .obsidian internals
        if ".obsidian" in md_file.parts:
            continue

        raw = md_file.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body = _strip_frontmatter(raw)
        text = _clean_markdown(body)

        if not text:
            continue

        folder = str(md_file.parent.relative_to(vault))
        docs.append(Document(
            text=text,
            source=str(md_file),
            title=md_file.stem,
            folder=folder,
            frontmatter=frontmatter,
        ))

    return docs
