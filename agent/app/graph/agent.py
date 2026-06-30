"""
Orchestrates the node pipeline and streams SSE events. Structurally this is
exactly what a LangGraph StateGraph.compile().astream(...) call would do —
see the comment block at the bottom for the literal LangGraph equivalent.
"""

import json
from typing import AsyncGenerator

from app.graph.state import AgentState
from app.graph import nodes
from app.llms.dispatcher import generate


async def run_agent_stream(query: str, session_id: str, user_id: str) -> AsyncGenerator[str, None]:
    state = AgentState(query=query, session_id=session_id, user_id=user_id)

    yield _sse("status", {"msg": "Classifying intent..."})
    state = await nodes.classify_intent(state)

    yield _sse("status", {"msg": "Retrieving memory..."})
    state = await nodes.retrieve_memory(state)

    yield _sse("status", {"msg": "Searching reference material..."})
    state = await nodes.rag_retrieval(state)

    yield _sse("status", {"msg": "Running tools..."})
    state = await nodes.select_and_run_tools(state)

    state = await nodes.extract_citations(state)

    yield _sse("status", {"msg": f"Generating response ({_model_label(state)})..."})

    full_response = []
    async for token in generate(
        query=state.query,
        intent=state.intent,
        rag_chunks=state.rag_chunks,
        memory_context=state.memory_context,
        tool_results=state.tool_results,
    ):
        full_response.append(token)
        yield _sse("token", {"text": token})

    response_text = "".join(full_response)
    await nodes.persist_memory(state, response_text)

    yield _sse("done", {
        "citations": state.citations,
        "intent": state.intent,
        "tool_results": state.tool_results,
    })


def _model_label(state: AgentState) -> str:
    from app.llms.dispatcher import select_model
    return select_model(state.intent)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# --- For reference: the literal LangGraph version of this pipeline ---------
# from langgraph.graph import StateGraph, END
# graph = StateGraph(AgentState)
# graph.add_node("classify_intent", nodes.classify_intent)
# graph.add_node("retrieve_memory", nodes.retrieve_memory)
# graph.add_node("rag_retrieval", nodes.rag_retrieval)
# graph.add_node("select_and_run_tools", nodes.select_and_run_tools)
# graph.add_node("extract_citations", nodes.extract_citations)
# graph.set_entry_point("classify_intent")
# graph.add_edge("classify_intent", "retrieve_memory")
# graph.add_edge("retrieve_memory", "rag_retrieval")
# graph.add_edge("rag_retrieval", "select_and_run_tools")
# graph.add_edge("select_and_run_tools", "extract_citations")
# graph.add_edge("extract_citations", END)
# agent = graph.compile()
# This file's run_agent_stream() is functionally equivalent, plus inline SSE
# emission and the final LLM generation step.
