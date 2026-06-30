"""
Individual pipeline steps ("nodes" in LangGraph terminology). Each is a plain
async function taking and returning AgentState — this mirrors a LangGraph
StateGraph's node signature exactly, so swapping in real LangGraph later is a
drop-in change (see app/graph/agent.py for the orchestration that would
become graph.add_node(...) calls).
"""

from app.graph.state import AgentState
from app.memory import session_store, user_memory, vector_store
from app.tools import statute_lookup, clause_analyzer


_REASONING_KEYWORDS = ["enforceable", "valid", "liable", "interpret", "analysis", "risk"]
_EXTRACTION_KEYWORDS = ["extract", "classify", "what type of clause", "list the"]
_CLAUSE_KEYWORDS = ["clause", "non-compete", "nda", "confidentiality", "indemnif", "arbitration"]
_STATUTE_KEYWORDS = ["statute", "code section", "law says", "§"]


async def classify_intent(state: AgentState) -> AgentState:
    q = state.query.lower()
    if any(k in q for k in _EXTRACTION_KEYWORDS):
        state.intent = "extract_clauses"
    else:
        state.intent = "legal_reasoning"
    return state


async def retrieve_memory(state: AgentState) -> AgentState:
    history = await session_store.get_history(state.session_id)
    memories = await user_memory.recall(state.user_id)
    state.memory_context = {"history": history, "user_memories": memories}
    return state


async def rag_retrieval(state: AgentState) -> AgentState:
    results = await vector_store.search(state.query, k=4)
    state.rag_chunks = [doc for doc, score in results if score > -0.5]
    return state


async def select_and_run_tools(state: AgentState) -> AgentState:
    q = state.query.lower()
    results = []

    if any(k in q for k in _STATUTE_KEYWORDS):
        jurisdiction = "california" if "california" in q else "federal"
        topic = "non-compete" if "compete" in q else ("privacy" if "privacy" in q else "trade secret")
        result = await statute_lookup(jurisdiction, topic)
        results.append({"tool": "statute_lookup", "result": result})

    if any(k in q for k in _CLAUSE_KEYWORDS):
        result = await clause_analyzer(state.query)
        results.append({"tool": "clause_analyzer", "result": str(result)})

    state.tool_results = results
    return state


async def extract_citations(state: AgentState) -> AgentState:
    state.citations = [
        {
            "n": i + 1,
            "source": chunk["source"],
            "page": chunk["page"],
            "excerpt": chunk["text"][:220],
        }
        for i, chunk in enumerate(state.rag_chunks)
    ]
    return state


async def persist_memory(state: AgentState, response_text: str) -> None:
    await session_store.append(state.session_id, "user", state.query)
    await session_store.append(state.session_id, "assistant", response_text)

    # naive long-term fact extraction — production would use a cheap LLM call
    q = state.query.lower()
    if "california" in q:
        await user_memory.remember(state.user_id, "jurisdiction", "California")
    if "non-compete" in q or "noncompete" in q:
        await user_memory.remember(state.user_id, "practice_area", "Employment / non-compete")
    if "nda" in q or "confidential" in q:
        await user_memory.remember(state.user_id, "practice_area", "Confidentiality / NDA")
