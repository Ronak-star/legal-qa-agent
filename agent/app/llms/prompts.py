from typing import List, Dict
from app.config import SYSTEM_PROMPT


def build_user_prompt(query: str, rag_chunks: List[Dict], memory_context: Dict, tool_results: List[Dict]) -> str:
    parts = []

    if memory_context.get("user_memories"):
        parts.append("Known context about this user:")
        for m in memory_context["user_memories"]:
            parts.append(f"- ({m['memory_type']}) {m['content']}")
        parts.append("")

    if memory_context.get("history"):
        parts.append("Recent conversation:")
        for turn in memory_context["history"][-6:]:
            parts.append(f"{turn['role']}: {turn['content']}")
        parts.append("")

    if rag_chunks:
        parts.append("Relevant reference material (cite using [n]):")
        for i, chunk in enumerate(rag_chunks, 1):
            parts.append(f"[{i}] {chunk['source']} ({chunk['page']}): {chunk['text']}")
        parts.append("")

    if tool_results:
        parts.append("Tool results:")
        for tr in tool_results:
            parts.append(f"- {tr['tool']}: {tr['result']}")
        parts.append("")

    parts.append(f"User question: {query}")
    return "\n".join(parts)


SYSTEM = SYSTEM_PROMPT
