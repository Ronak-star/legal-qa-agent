from typing import List, Dict, Optional
from pydantic import BaseModel


class AgentState(BaseModel):
    query: str
    session_id: str
    user_id: str

    intent: str = "legal_reasoning"
    memory_context: Dict = {}
    rag_chunks: List[Dict] = []
    tool_results: List[Dict] = []
    citations: List[Dict] = []
