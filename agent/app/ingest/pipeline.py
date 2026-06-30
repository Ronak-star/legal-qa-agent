"""
Document ingestion: chunk → embed → index. Accepts raw text (the gateway
extracts text from uploaded files before forwarding here, or you can POST
plain text directly for testing).
"""

from typing import List
from app.memory.vector_store import add_documents

_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


async def ingest_document(doc_id: str, source_name: str, text: str) -> int:
    chunks = chunk_text(text)
    docs = [
        {
            "id": f"{doc_id}-chunk-{i}",
            "source": source_name,
            "page": f"chunk {i + 1}/{len(chunks)}",
            "text": chunk,
        }
        for i, chunk in enumerate(chunks)
    ]
    await add_documents(docs)
    return len(docs)
