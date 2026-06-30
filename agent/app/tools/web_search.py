"""Stubbed legal web search — returns realistic mock sources. Swap the body
of this function for a real call to a search API (Serper, CourtListener,
Westlaw/LexisNexis) to go live; the return shape stays the same."""

async def web_search(query: str) -> list:
    return [
        {
            "title": f"Case law summary related to: {query}",
            "source": "CourtListener (mock)",
            "url": "https://www.courtlistener.com/",
            "snippet": "This is a stubbed search result. Wire up a real search "
                       "provider in app/tools/web_search.py to get live results.",
        }
    ]
