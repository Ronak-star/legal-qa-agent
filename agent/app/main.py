from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.graph.agent import run_agent_stream
from app.memory.vector_store import seed_corpus
from app.memory.user_memory import init_db
from app.ingest.pipeline import ingest_document
import uuid

app = FastAPI(title="Legal / Policy Q&A Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    await seed_corpus()


@app.get("/health")
async def health():
    return {"status": "ok"}


class QueryRequest(BaseModel):
    query: str
    session_id: str
    user_id: str = "anonymous"


@app.post("/agent/query")
async def query_agent(req: QueryRequest):
    """Streams an SSE response: status events, token events, then a done event
    carrying citations and metadata."""
    return StreamingResponse(
        run_agent_stream(req.query, req.session_id, req.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class IngestRequest(BaseModel):
    source_name: str
    text: str
    user_id: str = "anonymous"


@app.post("/ingest")
async def ingest(req: IngestRequest):
    doc_id = str(uuid.uuid4())
    chunk_count = await ingest_document(doc_id, req.source_name, req.text)
    return {"doc_id": doc_id, "chunks_indexed": chunk_count}
