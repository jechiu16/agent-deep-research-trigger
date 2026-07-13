"""Gemini Deep Research Interactions adapter, async submit/poll/extract.

The preview agent uses the Interactions API background mode. This adapter
deliberately sends no files or local content and keeps the provider response
as discovery-only output because the registry sets ``can_support_claims`` to
false.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit

from ..boundary import (
    AdapterParseError,
    AdapterTerminalFailure,
    BoundaryError,
    ParsedResult,
    RequestSpec,
)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
AGENT = "deep-research-preview-04-2026"


def _require_key(env: dict[str, str]) -> str:
    key = env.get("GEMINI_API_KEY")
    if not key:
        raise BoundaryError("GEMINI_API_KEY is not set")
    return key


def submit(query: str, env: dict[str, str]) -> RequestSpec:
    key = _require_key(env)
    body = json.dumps(
        {
            "input": query,
            "agent": AGENT,
            "background": True,
            "store": True,
            "agent_config": {
                "type": "deep-research",
                "thinking_summaries": "none",
                "visualization": "off",
                "collaborative_planning": False,
            },
        }
    ).encode("utf-8")
    return RequestSpec(
        method="POST",
        url=BASE_URL,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        body=body,
        timeout_s=60.0,
    )


def job_token(payload: bytes) -> str:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"gemini accept payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("gemini accept payload is not an object")
    token = data.get("id")
    if not isinstance(token, str) or not token.strip():
        raise AdapterParseError("gemini accept payload has no id")
    return token


def poll(token: str, env: dict[str, str]) -> RequestSpec:
    key = _require_key(env)
    return RequestSpec(
        method="GET",
        url=f"{BASE_URL}/{token}",
        headers={"x-goog-api-key": key},
        body=b"",
        timeout_s=30.0,
    )


def _terminal_failure_message(data: dict[str, Any]) -> str:
    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message
    if isinstance(error, str) and error.strip():
        return error
    return f"gemini deep job ended with status {data.get('status')!r}"


def extract(payload: bytes) -> ParsedResult | None:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"gemini poll payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("gemini poll payload is not an object")

    status = data.get("status")
    if not isinstance(status, str) or not status:
        raise AdapterParseError("gemini poll payload has no status")
    if status == "in_progress":
        return None
    if status == "requires_action":
        raise AdapterParseError(
            "gemini requires_action is an unsupported interactive state"
        )
    if status != "completed":
        raise AdapterTerminalFailure(_terminal_failure_message(data))

    steps = data.get("steps")
    if not isinstance(steps, list):
        raise AdapterParseError("gemini completed payload has no steps array")

    texts: list[str] = []
    citations: list[dict[str, object]] = []
    seen_urls: set[str] = set()
    for step in steps:
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        content = step.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)
            annotations = block.get("annotations")
            if not isinstance(annotations, list):
                continue
            for annotation in annotations:
                if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
                    continue
                raw_url = annotation.get("url")
                if not isinstance(raw_url, str):
                    continue
                normalized_url = raw_url.strip()
                parsed_url = urlsplit(normalized_url)
                if (
                    not normalized_url
                    or parsed_url.scheme not in {"http", "https"}
                    or not parsed_url.netloc
                    or normalized_url in seen_urls
                ):
                    continue
                seen_urls.add(normalized_url)
                citations.append(
                    {
                        "url": normalized_url,
                        "title": annotation.get("title"),
                        "date": annotation.get("date"),
                    }
                )

    synthesis_text = "\n\n".join(texts).strip()
    if not synthesis_text:
        raise AdapterParseError("gemini completed payload has no model output text")

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    returned_model = data.get("model") or data.get("agent") or AGENT
    model = returned_model if isinstance(returned_model, str) and returned_model else AGENT
    return ParsedResult(
        synthesis_text=synthesis_text,
        citations=citations,
        cost_usd=None,
        usage=usage,
        model=model,
        kind="search_synthesis",
    )
