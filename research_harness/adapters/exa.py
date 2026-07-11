"""Exa adapter: one synchronous auto search with bounded result highlights."""

from __future__ import annotations

import json
import urllib.parse

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec


SEARCH_URL = "https://api.exa.ai/search"
RESULT_LIMIT = 10
HIGHLIGHT_LIMIT = 500


def build(query: str, env: dict[str, str]) -> RequestSpec:
    key = env.get("EXA_API_KEY")
    if not key:
        raise BoundaryError("EXA_API_KEY is not set")
    body = json.dumps(
        {
            "query": query,
            "type": "auto",
            "numResults": RESULT_LIMIT,
            "contents": {"highlights": True},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return RequestSpec(
        method="POST",
        url=SEARCH_URL,
        headers={"x-api-key": key, "Content-Type": "application/json"},
        body=body,
        timeout_s=60.0,
    )


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"exa payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("exa payload is not a JSON object")
    results = data.get("results")
    if not isinstance(results, list):
        raise AdapterParseError("exa payload has no results list")

    lines: list[str] = []
    citations: list[dict] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get("title") if isinstance(item.get("title"), str) else "(untitled)"
        published = item.get("publishedDate")
        date = published if isinstance(published, str) and published else None
        author = item.get("author") if isinstance(item.get("author"), str) else ""
        line = f"- {title}"
        if date is not None:
            line += f" ({date})"
        if author:
            line += f" — {author}"
        highlights = item.get("highlights")
        if isinstance(highlights, list) and highlights and isinstance(highlights[0], str):
            line += f"\n  {highlights[0][:HIGHLIGHT_LIMIT]}"
        lines.append(line)

        url = item.get("url")
        if isinstance(url, str) and urllib.parse.urlsplit(url).scheme in {"http", "https"}:
            citations.append({"url": url, "title": title, "date": date})

    cost_breakdown = data.get("costDollars")
    cost = cost_breakdown.get("total") if isinstance(cost_breakdown, dict) else None
    if not isinstance(cost, (int, float)) or isinstance(cost, bool):
        cost = None
    else:
        cost = round(cost, 6)

    return ParsedResult(
        synthesis_text="\n".join(lines),
        citations=citations,
        cost_usd=cost,
        usage={
            "request_id": data.get("requestId"),
            "returned": len(results),
            "cost_breakdown": cost_breakdown if isinstance(cost_breakdown, dict) else {},
        },
        model="exa/search-auto",
        kind="result_listing",
    )
