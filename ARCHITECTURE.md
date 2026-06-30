# Architecture detail

## Request lifecycle

1. **React** (`frontend/src/hooks/useChat.js`) POSTs the query to the gateway, then
   opens an `EventSource` against `GET /api/v1/chat/stream` to receive tokens.
2. **Gateway** (`gateway/src/app.js`):
   - `middleware/auth.js` verifies the JWT and attaches `req.user`
   - `middleware/rateLimit.js` applies a per-user token bucket
   - `middleware/audit.js` logs the request
   - `routes/chat.js` proxies the request to the FastAPI agent and streams the SSE
     response straight through to the browser, byte for byte
3. **Agent** (`agent/app/main.py`) calls `agent/app/graph/agent.py`, an async pipeline
   of steps defined in `agent/app/graph/nodes.py`:
   - `classify_intent` — routes the query to a model based on keywords (reasoning vs
     extraction vs summarization)
   - `retrieve_memory` — loads short-term session history + long-term user memory
   - `rag_retrieval` — embeds the query, does cosine-similarity search over the vector
     index, returns top-k chunks with source metadata
   - `select_and_run_tools` — runs statute lookup / clause analyzer if the query implies
     them
   - `llm_generate` — dispatches to the selected LLM (or mock), streaming tokens via an
     async generator
   - `extract_citations` — maps the retrieved chunks used into a citations list
   - the whole pipeline result is streamed back as SSE: `token`, `status`, and `done`
     events
4. **Memory** lives in `agent/app/memory/`:
   - `session_store.py` — short-term conversation history, in-memory dict keyed by
     session id (swap for Redis: see comment in file)
   - `user_memory.py` — long-term per-user facts in SQLite (swap for Postgres+pgvector:
     see comment in file)
   - `vector_store.py` — JSON-backed embedding index with cosine similarity search (swap
     for Chroma/Qdrant: identical interface, see comment in file)

## Swapping in production infra

Every local implementation exposes the same function signatures a production version
would use, so swapping is additive, not a rewrite:

| Local (ships here) | Production swap | File |
|---|---|---|
| In-memory dict | Redis | `agent/app/memory/session_store.py` |
| SQLite | PostgreSQL + pgvector | `agent/app/memory/user_memory.py` |
| JSON vector index | Chroma / Qdrant | `agent/app/memory/vector_store.py` |
| In-memory token bucket | Redis token bucket | `gateway/src/middleware/rateLimit.js` |

## Multi-LLM routing

`agent/app/llms/dispatcher.py`:

- `legal_reasoning` intent → Claude (long context, nuanced reasoning)
- `extract_clauses` intent → GPT-4o (structured output)
- no API key configured → mock provider (deterministic canned responses, still streams
  token-by-token so the UI behaves identically)

## Tools

`agent/app/tools/`, registered in `agent/app/tools/__init__.py`:

- `statute_lookup.py` — looks up statute text from a small seeded mock dataset by
  jurisdiction + topic
- `clause_analyzer.py` — classifies a contract clause's type and risk level using the
  LLM dispatcher
- `web_search.py` — stubbed web search returning realistic mock legal sources (swap in
  a real search API by editing one function)

## File structure

```
legal-qa-agent/
├── frontend/                 React + Vite
│   └── src/
│       ├── components/       ChatInterface, LoginPage, Sidebar, MessageBubble, CitationPanel
│       ├── hooks/             useChat.js (SSE)
│       ├── stores/            simple React context-based stores
│       └── api/               client.js (fetch wrapper)
├── gateway/                  Node.js + Express
│   └── src/
│       ├── middleware/        auth, rateLimit, audit
│       ├── routes/            auth, chat, sessions
│       └── app.js
├── agent/                    Python FastAPI
│   └── app/
│       ├── graph/             agent.py, nodes.py, state.py
│       ├── memory/            session_store, user_memory, vector_store
│       ├── llms/               dispatcher.py, prompts.py
│       ├── tools/              statute_lookup, clause_analyzer, web_search
│       └── main.py
├── infra/                    nginx.conf, init.sql
└── docker-compose.yml
```
