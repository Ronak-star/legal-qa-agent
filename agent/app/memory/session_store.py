"""
Short-term conversation memory, keyed by session id.

PRODUCTION SWAP: replace this in-memory dict with Redis.
  - get_history(session_id)  ->  await redis.lrange(f"session:{id}:history", 0, 19)
  - append(session_id, msg)  ->  await redis.rpush(f"session:{id}:history", json.dumps(msg))
                                   await redis.expire(key, 60*60*24*7)  # 7 day TTL
The function signatures below are the contract the rest of the app relies on,
so swapping the implementation requires no changes elsewhere.
"""

from collections import defaultdict
from typing import List, Dict
import time

_MAX_TURNS = 20

_store: Dict[str, List[dict]] = defaultdict(list)


async def get_history(session_id: str) -> List[dict]:
    return _store[session_id][-_MAX_TURNS:]


async def append(session_id: str, role: str, content: str) -> None:
    _store[session_id].append({
        "role": role,
        "content": content,
        "ts": time.time(),
    })
    _store[session_id] = _store[session_id][-_MAX_TURNS:]


async def list_sessions(user_id: str) -> List[str]:
    # In this simple store, session ids aren't partitioned by user beyond naming
    # convention used by the gateway (session ids are opaque to the agent).
    return [sid for sid in _store.keys() if sid.startswith(user_id)]


async def clear(session_id: str) -> None:
    _store.pop(session_id, None)
