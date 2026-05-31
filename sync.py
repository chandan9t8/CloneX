import os
import sys

from dotenv import load_dotenv

from ingest.chunker import chunk_document
from ingest.obsidian import load_vault
from store.vector_store import VectorStore


def run(vault_path: str, db_path: str = "./brain_db") -> dict:
    if not os.path.isdir(vault_path):
        raise ValueError(f"Vault not found: {vault_path}")

    print(f"Loading vault: {vault_path}")
    docs = load_vault(vault_path)
    print(f"  {len(docs)} notes found")

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    print(f"  {len(all_chunks)} chunks produced")

    store = VectorStore(db_path=db_path)
    upserted = store.upsert(all_chunks)
    print(f"  {upserted} chunks upserted (total in store: {store.count()})")

    return {"notes": len(docs), "chunks": len(all_chunks), "upserted": upserted}


if __name__ == "__main__":
    load_dotenv()

    vault_path = os.environ.get("VAULT_PATH", "").strip()
    if not vault_path:
        print("Error: VAULT_PATH is not set in .env", file=sys.stderr)
        sys.exit(1)

    try:
        result = run(vault_path)
        print(f"\nDone. {result['notes']} notes → {result['chunks']} chunks → {result['upserted']} upserted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
