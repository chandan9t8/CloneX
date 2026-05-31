# CloneX

A RAG-based personal knowledge assistant that lets you chat with your Obsidian notes. Ingests your vault, stores embeddings locally in ChromaDB, and answers questions using the OpenAI API — no server required.

## How it works

```
Obsidian vault (.md files)
        │
        ▼
sync.py  →  load → chunk → embed → store in ChromaDB (brain_db/)
        │
        ▼
cli.py ask "..."  →  retrieve top-k chunks → GPT synthesizes answer
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
VAULT_PATH=/path/to/your/obsidian/vault
```

## Usage

**Ingest your vault** (run once, re-run anytime — it's idempotent):

```bash
python sync.py
```

**Ask a question:**

```bash
python cli.py ask "What do I know about binary trees?"
```

Output:

```
A binary tree has at most 2 children per node, exactly 1 root...

Sources:
  [0.921] DSA/7. Trees › Trees
  [0.874] DSA/7. Trees › Array representation
```

## Project structure

```
ingest/
  obsidian.py     # loads .md files, strips wikilinks and frontmatter
  chunker.py      # splits documents into embedding-sized chunks
store/
  vector_store.py # ChromaDB wrapper — upsert and search
brain/
  query.py        # retrieves chunks, calls GPT for a synthesized answer
sync.py           # ingestion entry point
cli.py            # query entry point
```

## Running tests

```bash
python -m pytest
```
