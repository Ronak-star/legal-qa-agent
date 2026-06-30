<div align="center">

# Legal / Policy Q&A Agent

**Full-stack, multi-tier AI agent for legal and policy question answering** — React, Node.js, FastAPI, RAG retrieval, persistent memory, and pluggable multi-LLM routing.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)

</div>

---

## Architecture

```mermaid
flowchart TB
    subgraph Client["Presentation layer"]
        UI["React + Vite\nChat UI · SSE rendering"]
    end

    subgraph Gateway["API gateway — Node.js + Express"]
        Auth["JWT auth"]
        Rate["Rate limiter"]
        Audit["Audit logger"]
        Proxy["SSE proxy → agent"]
    end

    subgraph Agent["Agent core — Python FastAPI"]
        Intent["Classify intent"]
        Mem["Retrieve memory"]
        RAG["RAG retrieval"]
        Tools["Run tools"]
        LLM["Multi-LLM dispatch"]
        Cite["Extract citations"]
    end

    subgraph Data["Memory & retrieval"]
        Session["Session store\n(short-term)"]
        UserMem["User memory\n(long-term)"]
        Vector["Vector index\n(legal corpus)"]
    end

    subgraph Models["LLM providers"]
        Claude["Claude\nreasoning"]
        GPT["GPT-4o\nextraction"]
        Mock["Mock provider\nno key required"]
    end

    UI -->|"POST /chat + SSE"| Proxy
    Auth --> Rate --> Audit --> Proxy
    Proxy -->|"forward query"| Intent
    Intent --> Mem --> RAG --> Tools --> LLM --> Cite
    Cite -->|"stream tokens + citations"| Proxy
    Proxy -->|"SSE stream"| UI

    Mem -.-> Session
    Mem -.-> UserMem
    RAG -.-> Vector
    LLM -.-> Claude
    LLM -.-> GPT
    LLM -.-> Mock

    classDef client fill:#E6F1FB,stroke:#185FA5,color:#0C447C
    classDef gateway fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    classDef agent fill:#EEEDFE,stroke:#534AB7,color:#26215C
    classDef data fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    classDef model fill:#FAEEDA,stroke:#854F0B,color:#412402

    class UI client
    class Auth,Rate,Audit,Proxy gateway
    class Intent,Mem,RAG,Tools,LLM,Cite agent
    class Session,UserMem,Vector data
    class Claude,GPT,Mock model
```

A user's question flows: **React UI → Node.js gateway (auth, rate limiting, SSE proxy) → FastAPI agent (intent classification → memory retrieval → RAG → tools → LLM generation → citation extraction)**, streaming back token-by-token with cited sources.

---

## Request lifecycle

```mermaid
sequenceDiagram
    participant U as React UI
    participant G as Node gateway
    participant A as FastAPI agent
    participant M as Memory + vector store
    participant L as LLM (Claude / GPT-4o)

    U->>G: POST /api/v1/chat/stream (JWT)
    G->>G: verify JWT, rate limit, audit log
    G->>A: POST /agent/query
    A->>A: classify intent
    A->>M: get session history + user memory
    M-->>A: short-term + long-term context
    A->>M: embed query, search vector index
    M-->>A: top-k cited chunks
    A->>A: run tools (statute lookup, clause analysis)
    A->>L: generate (prompt + context + chunks)
    L-->>A: streamed tokens
    A-->>G: SSE: token, token, ... done (citations)
    G-->>U: SSE passthrough
    U->>U: render tokens live + citation panel
    A->>M: persist turn to memory
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Server-Sent Events |
| Gateway | Node.js, Express, JWT, token-bucket rate limiting |
| Agent | Python, FastAPI, async orchestration pipeline |
| Memory | Session store (short-term) + user memory (long-term) |
| Retrieval | Embedding + cosine-similarity vector search, seeded legal corpus |
| LLMs | Claude (reasoning), GPT-4o (structured extraction), mock fallback |
| Infra | Docker Compose, nginx (optional single-origin deployment) |

---

## Features

- **Streaming chat UI** with live token rendering and a sources panel
- **Multi-LLM routing** by intent, with automatic mock-mode fallback when no API key is set — the whole pipeline is testable with zero cost
- **RAG retrieval** over a seeded legal/policy corpus with inline `[n]` citations
- **Persistent memory** — short-term session history, long-term per-user facts across sessions
- **Domain tools** — statute lookup, contract clause risk analysis, pluggable web search
- **Auth & rate limiting** — JWT auth, per-user token bucket, audit logging
- **Zero-dependency local dev** — only Node + Python needed, no external services required to start
- **Production-shaped** — every local component documents its drop-in production swap (Redis, Postgres + pgvector, Chroma/Qdrant)

---

## Quick start

**Requirements:** Node.js 18+, Python 3.10+

```bash
git clone https://github.com/<your-username>/legal-qa-agent.git
cd legal-qa-agent

cp agent/.env.example agent/.env
cp gateway/.env.example gateway/.env
cp frontend/.env.example frontend/.env
```

Add a key to `agent/.env` for real LLM responses (optional — see [below](#running-without-api-keys)):

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
```

Run all three services:

```bash
# Terminal 1 — agent
cd agent && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — gateway
cd gateway && npm install && npm run dev

# Terminal 3 — frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**, sign in with any username/password, and ask:

> "Is a non-compete clause enforceable in California?"

### Docker

```bash
cp .env.example .env   # add API keys at the repo root, optional
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Gateway | http://localhost:4000 |
| Agent (Swagger docs) | http://localhost:8000/docs |

---

## Running without API keys

With no `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` set, the agent runs in **mock mode** automatically — deterministic, realistic responses that still exercise the full pipeline (auth, SSE streaming, RAG retrieval, tool calls, citations, memory). Add a real key and restart the agent to switch to live model output; no code changes needed.

---

## Project structure

```
legal-qa-agent/
├── frontend/                 React + Vite chat UI
│   └── src/
│       ├── components/        ChatInterface, LoginPage, Sidebar
│       ├── hooks/              useChat.js — SSE streaming
│       └── api/                client.js
│
├── gateway/                  Node.js + Express API gateway
│   └── src/
│       ├── middleware/         auth, rateLimit, audit
│       ├── routes/             auth, chat, documents
│       └── app.js
│
├── agent/                    Python FastAPI agent service
│   └── app/
│       ├── graph/              agent.py, nodes.py, state.py — orchestration
│       ├── memory/             session_store, user_memory, vector_store
│       ├── llms/                dispatcher.py — multi-LLM routing
│       ├── tools/               statute_lookup, clause_analyzer, web_search
│       └── main.py
│
├── infra/                    nginx.conf for single-origin deployment
└── docker-compose.yml
```

---

## Swapping in production infrastructure

Every local component exposes the same interface a production version would use — swapping is additive, not a rewrite.

| Local (ships here) | Production swap | File |
|---|---|---|
| In-memory dict | Redis | `agent/app/memory/session_store.py` |
| SQLite | PostgreSQL + pgvector | `agent/app/memory/user_memory.py` |
| JSON vector index | Chroma / Qdrant | `agent/app/memory/vector_store.py` |
| In-memory token bucket | Redis token bucket | `gateway/src/middleware/rateLimit.js` |

---

## Security note

`.env` files are excluded via `.gitignore` — **never commit real API keys**. Check `git status` before pushing if you've added your own keys locally. If a secret is ever committed by accident, revoke it immediately in the provider's console and scrub it from git history before pushing again.

---

## License

MIT — use this however you'd like.

---

## Disclaimer

This project provides general legal and policy information for research and demonstration purposes. It is not a substitute for advice from a licensed attorney.
