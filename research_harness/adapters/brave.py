"""brave adapter: Brave Web Search, ranked result listing (no synthesis).

GET /res/v1/web/search on api.search.brave.com; results live under
``web.results[]``. Unlike sonar's model-written search_synthesis, this is a
ranked listing with no synthesis step, so
``evidence_capabilities.can_support_claims`` stays false — callers must
fetch a result's url directly before it can support a claim.

Brave's ``description`` field embeds literal ``<strong>``/``</strong>`` tags
around matched query terms (confirmed via live call 2026-07-11: present in
the recorded success fixture). The provider contract here is a plain-text
listing, so those tags are stripped before the ~160-char excerpt is taken;
tags are stripped first so truncation never leaves a dangling partial tag.
"""

from __future__ import annotations

import json
import re
import urllib.parse

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec

BASE_URL = "https://api.search.brave.com/res/v1/web/search"
COUNT = 20
EXCERPT_LIMIT = 160
_HIGHLIGHT_TAG_RE = re.compile(r"</?strong>")


def build(query: str, env: dict[str, str]) -> RequestSpec:
    key = env.get("BRAVE_SEARCH_API_KEY")
    if not key:
        raise BoundaryError("BRAVE_SEARCH_API_KEY is not set")
    params = {"q": query, "count": COUNT}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    return RequestSpec(
        method="GET",
        url=url,
        headers={"Accept": "application/json", "X-Subscription-Token": key},
        body=b"",
        timeout_s=30.0,
    )


def _date(item: dict) -> str | None:
    page_age = item.get("page_age")
    if isinstance(page_age, str) and page_age:
        return page_age
    age = item.get("age")
    return age if isinstance(age, str) and age else None


def _excerpt(item: dict) -> str:
    description = item.get("description")
    if not isinstance(description, str):
        return ""
    return _HIGHLIGHT_TAG_RE.sub("", description)[:EXCERPT_LIMIT]


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"brave payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("brave payload is not a JSON object")
    web = data.get("web")
    if not isinstance(web, dict):
        raise AdapterParseError("brave payload has no web.results")
    results = web.get("results")
    if not isinstance(results, list):
        raise AdapterParseError("brave payload has no web.results")

    lines: list[str] = []
    citations: list[dict] = []
    for index, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") if isinstance(item.get("title"), str) and item.get("title") else "(untitled)"
        url = item.get("url") if isinstance(item.get("url"), str) else None
        line = f"{index}. {title} — {url}"
        excerpt = _excerpt(item)
        if excerpt:
            line += f"\n   {excerpt}"
        lines.append(line)

        if url is not None and urllib.parse.urlsplit(url).scheme in {"http", "https"}:
            citations.append({"url": url, "title": title, "date": _date(item)})

    return ParsedResult(
        synthesis_text="\n".join(lines),
        citations=citations,
        cost_usd=None,
        usage={"result_count": len(results)},
        model="brave-web-search/v1",
        kind="result_listing",
    )
