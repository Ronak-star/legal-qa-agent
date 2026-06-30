"""Mock statute lookup tool — in production, swap the lookup table for calls
to government APIs (congress.gov, state leginfo sites, etc.)."""

_STATUTES = {
    ("california", "non-compete"): "Cal. Bus. & Prof. Code §16600 — non-competes are void except in narrow statutory exceptions (sale of business, dissolution of partnership/LLC).",
    ("california", "trade secret"): "Cal. Civ. Code §3426 (Uniform Trade Secrets Act) — defines trade secrets and remedies for misappropriation.",
    ("federal", "trade secret"): "18 U.S.C. §1836 (Defend Trade Secrets Act) — federal civil cause of action for trade secret misappropriation.",
    ("california", "privacy"): "Cal. Civ. Code §1798.100 et seq. (CCPA/CPRA) — consumer data rights including access, deletion, opt-out of sale.",
    ("eu", "privacy"): "GDPR Article 6 — lawful bases for processing personal data.",
}


async def statute_lookup(jurisdiction: str, topic: str) -> str:
    key = (jurisdiction.lower(), topic.lower())
    if key in _STATUTES:
        return _STATUTES[key]
    for (j, t), v in _STATUTES.items():
        if j == jurisdiction.lower() or t in topic.lower():
            return v
    return f"No statute found in mock dataset for jurisdiction='{jurisdiction}', topic='{topic}'."
