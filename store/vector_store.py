import hashlib
import os

import chromadb
from openai import OpenAI

from ingest.chunker import Chunk

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 500


def _chunk_id(chunk: Chunk) -> str:
    key = chunk.source + str(chunk.chunk_index)
    return hashlib.md5(key.encode()).hexdigest()


def _embed(client: OpenAI, texts: list[str]) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        embeddings.extend([r.embedding for r in response.data])
    return embeddings


class VectorStore:
    def __init__(self, db_path: str = "./brain_db", collection: str = "notes"):
        self._chroma = chromadb.PersistentClient(path=db_path)
        self._col = self._chroma.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )
        self._openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def upsert(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0

        ids = [_chunk_id(c) for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [
            {
                "title": c.title,
                "folder": c.folder,
                "source": c.source,
                "heading": c.heading,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        embeddings = _embed(self._openai, texts)

        self._col.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = _embed(self._openai, [query])[0]
        results = self._col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({"text": doc, "score": 1 - dist, **meta})
        return hits

    def count(self) -> int:
        return self._col.count()
