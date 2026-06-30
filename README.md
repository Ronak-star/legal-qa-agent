# Legal / Policy Q&A Agent — Full Stack

A multi-tier AI agent system for legal and policy question answering.

```
React (frontend) → Node.js/Express (gateway) → FastAPI (agent) → Memory + RAG + Multi-LLM
```

This is a complete, runnable reference implementation. It ships with lightweight local
equivalents of production infra (in-memory session store instead of Redis, SQLite
instead of Postgres, a JSON-backed vector index instead of Chroma/Qdrant) so the whole
stack runs with just Node + Python — no Docker or external services required. A
docker-compose file is also included for running it with real Postgres/Redis.

---

## Quick start — no Docker (fastest, 3 terminals)

Requires **Node.js 18+** and **Python 3.10+**.

### Terminal 1 — Agent (FastAPI)

```bash
cd agent
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional: add ANTHROPIC_API_KEY / OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — Gateway (Node.js)

```bash
cd gateway
npm install
cp .env.example .env
npm run dev
```

### Terminal 3 — Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### Open it

Go to **http://localhost:5173**. Log in with any username/password (demo auth accepts
anything and issues a JWT). Ask something like:

> "Is a non-compete clause enforceable in California?"

You'll see the agent stream its answer live, with a citations panel populated from the
RAG retrieval step.

---

## Quick start — Docker Compose (all services + Postgres + Redis)

```bash
cp .env.example .env    # fill in API keys at repo root (optional)
docker-compose up --build
```

- Frontend → http://localhost:3000
- Gateway → http://localhost:4000
- Agent (Swagger docs) → http://localhost:8000/docs

---

## Running without API keys

If `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` are not set, the agent runs in **mock mode**
automatically — it returns deterministic, realistic canned answers so you can exercise
the entire pipeline (gateway auth, SSE streaming, memory, RAG retrieval, citations,
multi-LLM routing logic) without spending money. Drop real keys into `agent/.env` to get
real model responses — no code changes needed.

---

## What's actually wired up

- **Auth**: JWT issued by the gateway, verified on every protected route
- **Rate limiting**: token-bucket per user (in-memory; swappable for Redis)
- **SSE streaming**: agent streams tokens → gateway pipes them → React renders live
- **Memory**: short-term (last N turns per session) + long-term (per-user facts in
  SQLite), both read and written every turn
- **RAG**: a small seeded legal/policy corpus is embedded and indexed at agent startup;
  queries are embedded and matched via cosine similarity, top chunks are cited
- **Multi-LLM routing**: intent classifier picks Claude for reasoning, GPT-4o for
  structured extraction, with mock fallback
- **Tools**: statute lookup, clause analyzer, web search — registered and callable by
  the agent, with mock data so they work with zero config

See `ARCHITECTURE.md` for the full request-by-request breakdown.
