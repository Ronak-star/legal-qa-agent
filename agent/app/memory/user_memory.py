"""
Long-term, per-user memory: facts the agent has learned about a user across
sessions (jurisdiction, practice area, recurring topics).

PRODUCTION SWAP: replace SQLite with PostgreSQL + pgvector. The schema below
maps directly:

  CREATE TABLE user_memory (
    id          UUID PRIMARY KEY,
    user_id     TEXT,
    memory_type TEXT,
    content     TEXT,
    embedding   VECTOR(1536),
    created_at  TIMESTAMPTZ DEFAULT now()
  );

and `recall()` becomes an ORDER BY embedding <=> $vector LIMIT k query instead
of the naive keyword scan used here.
"""

import aiosqlite
import os
import uuid
import time
from typing import List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "user_memory.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_memory (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def remember(user_id: str, memory_type: str, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_memory (id, user_id, memory_type, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, memory_type, content, time.time()),
        )
        await db.commit()


async def recall(user_id: str, limit: int = 5) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT memory_type, content, created_at FROM user_memory "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
