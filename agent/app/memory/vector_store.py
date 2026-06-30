"""
Document vector index for RAG.

PRODUCTION SWAP: replace this JSON/in-memory cosine-similarity index with
Chroma, Qdrant, or pgvector. The interface (`add_documents`, `search`) is the
same shape a real vector DB client would expose, so callers don't change.

Embeddings: if an OpenAI key is configured, uses text-embedding-3-small.
Otherwise falls back to a deterministic hash-based pseudo-embedding so RAG
still "works" (returns consistent, query-relevant-ish results) with zero
API keys configured, for local testing.
"""

import hashlib
import math
from typing import List, Dict, Tuple

from app.config import OPENAI_API_KEY

_DOCS: List[Dict] = []
_VECTORS: List[List[float]] = []

_DIM = 64


def _hash_embed(text: str) -> List[float]:
    """Deterministic fallback embedding — bag-of-words hashed into a fixed-size
    vector. Not semantically rich, but stable and good enough for demo RAG
    without any API key."""
    vec = [0.0] * _DIM
    for word in text.lower().split():
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % _DIM
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed(text: str) -> List[float]:
    if OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            resp = await client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            return resp.data[0].embedding
        except Exception:
            pass
    return _hash_embed(text)


def _cosine(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        # mismatched dims (e.g. real embedding vs hash fallback) — treat as no match
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


async def add_documents(docs: List[Dict]) -> None:
    """docs: [{id, source, page, text}]"""
    for doc in docs:
        vec = await embed(doc["text"])
        _DOCS.append(doc)
        _VECTORS.append(vec)


async def search(query: str, k: int = 5) -> List[Tuple[Dict, float]]:
    if not _DOCS:
        return []
    qvec = await embed(query)
    scored = [(_DOCS[i], _cosine(qvec, _VECTORS[i])) for i in range(len(_DOCS))]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# --- Seed corpus: a small set of legal/policy reference snippets ----------
_SEED_CORPUS = [
    {
        "id": "ca-bpc-16600",
        "source": "California Business and Professions Code",
        "page": "§16600",
        "text": (
            "Except as provided in this chapter, every contract by which anyone "
            "is restrained from engaging in a lawful profession, trade, or "
            "business of any kind is to that extent void. California courts "
            "have interpreted this to make most employee non-compete clauses "
            "unenforceable, with narrow statutory exceptions for the sale of a "
            "business or dissolution of a partnership."
        ),
    },
    {
        "id": "nda-clause-standard",
        "source": "Standard NDA Clause Library",
        "page": "Confidentiality §3.2",
        "text": (
            "Confidentiality obligations under a non-disclosure agreement "
            "typically survive termination for a defined period, commonly 2-5 "
            "years, though trade secret protection can be indefinite under "
            "applicable trade secret law such as the Uniform Trade Secrets Act "
            "or the federal Defend Trade Secrets Act."
        ),
    },
    {
        "id": "gdpr-art-6",
        "source": "GDPR",
        "page": "Article 6",
        "text": (
            "Processing of personal data is lawful only if at least one legal "
            "basis applies: consent, contract necessity, legal obligation, "
            "vital interests, public task, or legitimate interests, with "
            "legitimate interests requiring a balancing test against the "
            "rights of the data subject."
        ),
    },
    {
        "id": "ccpa-overview",
        "source": "California Consumer Privacy Act (CCPA)",
        "page": "§1798.100",
        "text": (
            "The CCPA grants California residents the right to know what "
            "personal information is collected, the right to delete it, the "
            "right to opt out of its sale, and the right to non-discrimination "
            "for exercising these rights. It applies to for-profit businesses "
            "meeting certain revenue or data-volume thresholds."
        ),
    },
    {
        "id": "at-will-employment",
        "source": "Employment Law Primer",
        "page": "Ch. 4 — At-Will Doctrine",
        "text": (
            "Most U.S. states follow the at-will employment doctrine, allowing "
            "either party to terminate employment at any time for any lawful "
            "reason, subject to exceptions for discrimination, retaliation, "
            "public policy violations, and implied contract claims."
        ),
    },
    {
        "id": "force-majeure-clause",
        "source": "Contract Drafting Handbook",
        "page": "Ch. 9 — Force Majeure",
        "text": (
            "Force majeure clauses excuse contractual performance when an "
            "extraordinary event beyond a party's control prevents performance. "
            "Courts generally construe these clauses narrowly and require the "
            "triggering event to be specifically enumerated or reasonably "
            "encompassed by catch-all language."
        ),
    },
    {
        "id": "ip-assignment-clause",
        "source": "Standard Employment Agreement Library",
        "page": "IP Assignment §7",
        "text": (
            "Intellectual property assignment clauses typically require "
            "employees to assign inventions created within the scope of "
            "employment to the employer, though several states including "
            "California (Labor Code §2870) carve out inventions developed "
            "entirely on the employee's own time without employer resources."
        ),
    },
    {
        "id": "arbitration-clause",
        "source": "Contract Drafting Handbook",
        "page": "Ch. 12 — Dispute Resolution",
        "text": (
            "Mandatory arbitration clauses require disputes to be resolved "
            "through binding arbitration rather than litigation. The Federal "
            "Arbitration Act generally preempts state laws that single out "
            "arbitration agreements for disfavored treatment, though "
            "unconscionability defenses remain available in limited circumstances."
        ),
    },
]


async def seed_corpus():
    if _DOCS:
        return  # already seeded
    await add_documents(_SEED_CORPUS)
