import os
from typing import Any, Dict, List, Sequence

import requests
from langchain_core.tools import tool

from shared.config import SEARCH_MAX_EXCERPT_CHARS, SEARCH_MAX_EXCERPTS_PER_RESULT, SEARCH_TOP_K

try:
    import numexpr as ne
except ImportError:
    ne = None



PARALLEL_SEARCH_URL = "https://api.parallel.ai/v1/search"


def _truncate_text(text: Any, max_chars: int) -> str:
    value = str(text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _parallel_headers() -> Dict[str, str]:
    api_key = os.getenv("PARALLEL_API_KEY")
    if not api_key:
        raise RuntimeError("PARALLEL_API_KEY is not set")
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


def parallel_search(objective: str, search_queries: Sequence[str], top_k: int = SEARCH_TOP_K) -> Dict[str, Any]:
    """
    Run a Parallel web search with one objective and multiple query variants.

    Returns a normalized payload so downstream agents can consume it directly.
    """
    if not search_queries:
        raise ValueError("Search Queries must not be empty")

    payload = {
        "objective": objective,
        "search_queries": list(search_queries),
    }

    response = requests.post(
        PARALLEL_SEARCH_URL,
        headers=_parallel_headers(),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    raw_results = data.get("results", [])

    normalized_results: List[Dict[str, Any]] = []
    for item in raw_results[:top_k]:
        excerpts = []
        for excerpt in (item.get("excerpts", []) or [])[:SEARCH_MAX_EXCERPTS_PER_RESULT]:
            cleaned_excerpt = _truncate_text(excerpt, SEARCH_MAX_EXCERPT_CHARS)
            if cleaned_excerpt and cleaned_excerpt not in excerpts:
                excerpts.append(cleaned_excerpt)
        normalized_results.append(
            {
                "title": item.get("title"),
                "url": item.get("url") or item.get("link"),
                "publish_date": item.get("publish_date"),
                "excerpts": excerpts,
            }
        )

    return {
        "objective": objective,
        "search_queries": list(search_queries),
        "results": normalized_results,
    }


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a math expression using numexpr.

    Supported examples:
    - "2 * (3 + 5)"
    - "120 / 4"
    - "1.12 * 2500"
    """
    try:
        result = ne.evaluate(expression)
        if hasattr(result, "item"):
            result = result.item()
        return f"The result is: {result}"
    except Exception as exc:
        return f"Error evaluating expression: {exc}"
