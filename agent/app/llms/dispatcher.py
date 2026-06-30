"""
Multi-LLM dispatcher. Routes by intent to the model best suited for the task,
streaming tokens via an async generator regardless of provider. Falls back to
a deterministic mock provider when no API key is configured, so the rest of
the pipeline (gateway, SSE, citations, memory) is fully testable with zero
setup.
"""

import asyncio
from typing import AsyncGenerator, List, Dict

from app.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, MOCK_MODE
from app.llms.prompts import SYSTEM, build_user_prompt


async def _mock_stream(query: str, rag_chunks: List[Dict]) -> AsyncGenerator[str, None]:
    """Deterministic mock response that still references retrieved chunks,
    so the citation pipeline can be tested without API keys."""
    if rag_chunks:
        cite_list = ", ".join(f"[{i}]" for i in range(1, len(rag_chunks) + 1))
        response = (
            f"Based on the available reference material {cite_list}, here is a "
            f"general analysis of your question: \"{query}\"\n\n"
            f"This is a mock response (no ANTHROPIC_API_KEY or OPENAI_API_KEY "
            f"configured) — it demonstrates the full pipeline including RAG "
            f"retrieval and citation extraction. The most relevant source is "
            f"{rag_chunks[0]['source']} {rag_chunks[0]['page']}, which states: "
            f"\"{rag_chunks[0]['text'][:160]}...\"\n\n"
            f"For a real answer, add an API key to agent/.env and restart the "
            f"agent service. This is general information, not formal legal advice — "
            f"consult a licensed attorney for case-specific guidance."
        )
    else:
        response = (
            f"This is a mock response to: \"{query}\" (no API key configured, "
            f"and no relevant reference material was retrieved for this query). "
            f"Add ANTHROPIC_API_KEY or OPENAI_API_KEY to agent/.env for real "
            f"model responses."
        )

    for word in response.split(" "):
        yield word + " "
        await asyncio.sleep(0.015)


async def _claude_stream(prompt: str) -> AsyncGenerator[str, None]:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _openai_stream(prompt: str) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def select_model(intent: str) -> str:
    if intent == "extract_clauses" and OPENAI_API_KEY:
        return "gpt-4o"
    if ANTHROPIC_API_KEY:
        return "claude-sonnet-4-6"
    if OPENAI_API_KEY:
        return "gpt-4o"
    return "mock"


async def generate(
    query: str,
    intent: str,
    rag_chunks: List[Dict],
    memory_context: Dict,
    tool_results: List[Dict],
) -> AsyncGenerator[str, None]:
    model = select_model(intent)
    prompt = build_user_prompt(query, rag_chunks, memory_context, tool_results)

    if model == "claude-sonnet-4-6":
        async for tok in _claude_stream(prompt):
            yield tok
    elif model == "gpt-4o":
        async for tok in _openai_stream(prompt):
            yield tok
    else:
        async for tok in _mock_stream(query, rag_chunks):
            yield tok
