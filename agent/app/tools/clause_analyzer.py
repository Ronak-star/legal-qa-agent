"""Classifies likely contract clause type and risk level from keywords.
In production this would call an LLM with a structured function-calling schema
(see ARCHITECTURE.md — GPT-4o is routed here for that reason)."""

_CLAUSE_KEYWORDS = {
    "non-compete": ["non-compete", "noncompete", "restraint of trade", "compete with"],
    "confidentiality": ["confidential", "non-disclosure", "nda", "proprietary information"],
    "indemnification": ["indemnify", "indemnification", "hold harmless"],
    "force majeure": ["force majeure", "act of god", "beyond reasonable control"],
    "arbitration": ["arbitration", "binding arbitration", "waive jury trial"],
    "ip assignment": ["assign", "intellectual property", "invention", "work for hire"],
    "termination": ["terminate", "termination", "notice period"],
}

_RISK_BY_TYPE = {
    "non-compete": "high — frequently unenforceable depending on jurisdiction",
    "confidentiality": "moderate — standard but check survival period",
    "indemnification": "high — review scope and caps carefully",
    "force majeure": "low to moderate — depends on enumerated events",
    "arbitration": "moderate — affects dispute resolution rights",
    "ip assignment": "moderate — check state-law carve-outs",
    "termination": "low — standard, check notice requirements",
}


async def clause_analyzer(text: str) -> dict:
    text_lower = text.lower()
    matches = []
    for clause_type, keywords in _CLAUSE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matches.append(clause_type)

    if not matches:
        return {"clause_types": [], "risk": "unknown", "note": "No recognizable clause keywords found."}

    primary = matches[0]
    return {
        "clause_types": matches,
        "primary_type": primary,
        "risk": _RISK_BY_TYPE.get(primary, "unknown"),
    }
