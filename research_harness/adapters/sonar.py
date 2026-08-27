"""sonar adapter: Perplexity chat/completions, sync cited synthesis."""

from __future__ import annotations

import json

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec


def build(query: str, env: dict[str, str], *, model: str | None = None) -> RequestSpec:
    key = env.get("PERPLEXITY_API_KEY")
    if not key:
        raise BoundaryError("PERPLEXITY_API_KEY is not set")
    if not model:
        raise BoundaryError(
            "sonar provider record has no model configured "
            "(provider_registry.json is missing the \"model\" field)"
        )
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": query}]}
    ).encode("utf-8")
    return RequestSpec(
        method="POST",
        url="https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        body=body,
        timeout_s=120.0,
    )


def parse(payload: bytes, *, model: str | None = None) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"sonar payload is not JSON: {exc}") from exc
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AdapterParseError("sonar payload has no message content") from exc
    if not isinstance(text, str) or not text.strip():
        raise AdapterParseError("sonar message content is empty")
    raw_citations = data.get("search_results") or [
        {"url": url} for url in (data.get("citations") or [])
    ]
    citations = [
        {"url": item.get("url"), "title": item.get("title"), "date": item.get("date")}
        for item in raw_citations
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    ]
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    cost = (usage.get("cost") or {}).get("total_cost") if isinstance(usage.get("cost"), dict) else None
    returned_model = data.get("model")
    if isinstance(returned_model, str) and returned_model:
        resolved_model = returned_model
    elif model:
        resolved_model = model
    else:
        raise AdapterParseError(
            "sonar payload has no model and none is configured "
            "(provider_registry.json is missing the \"model\" field)"
        )
    return ParsedResult(
        synthesis_text=text,
        citations=citations,
        cost_usd=round(cost, 4) if isinstance(cost, (int, float)) else None,
        usage=usage,
        model=resolved_model,
        kind="search_synthesis",
    )
