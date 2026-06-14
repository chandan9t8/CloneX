import os

from openai import OpenAI

from store.vector_store import VectorStore

CHAT_MODEL = "gpt-4o-mini"
TOP_K = 5

_SYSTEM_PROMPT = """\
You are a personal knowledge assistant. Answer the user's question using ONLY
the notes provided below. If the notes don't contain enough information to
answer, say so — do not hallucinate. Be concise and direct.\
"""


def _build_context(hits: list[dict]) -> str:
    parts = []
    for i, hit in enumerate(hits, 1):
        heading = f" — {hit['heading']}" if hit["heading"] else ""
        parts.append(f"[{i}] {hit['title']}{heading}\n{hit['text']}")
    return "\n\n".join(parts)


def ask(question: str, db_path: str = "./brain_db", top_k: int = TOP_K) -> dict:
    """
    Returns {"answer": str, "sources": list[dict]}
    Each source has: title, folder, heading, score
    """
    store = VectorStore(db_path=db_path)
    hits = store.search(question, top_k=top_k)
    if not hits or hits[0]["score"] < 0.5:
        return {"answer": "No relevant notes found.", "sources": []}

    context = _build_context(hits)
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Notes:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content.strip()
    sources = [
        {
            "title": h["title"],
            "folder": h["folder"],
            "heading": h["heading"],
            "score": round(h["score"], 3),
        }
        for h in hits
    ]
    return {"answer": answer, "sources": sources}
