"""openai_deep adapter: OpenAI Deep Research (o4-mini-deep-research), async submit/poll/extract.

Verified against the OpenAI Responses API docs (fetched 2026-07-12):
https://platform.openai.com/docs/guides/deep-research (redirects to
developers.openai.com/api/docs/guides/deep-research) for the model name and
request shape (model/input/background/tools); background-mode submit/poll
contract and the status enum (queued/in_progress/completed/failed/cancelled/
incomplete) confirmed at https://platform.openai.com/docs/guides/background
(redirects to developers.openai.com/api/docs/guides/background); the GET
path and the error/incomplete_details shapes confirmed at
https://developers.openai.com/api/reference/resources/responses/methods/retrieve;
a concrete "output" array worked example (message/content/output_text/
annotations with type url_citation) confirmed at
https://developers.openai.com/cookbook/examples/responses_api/responses_example.
The usage object shape (input_tokens/input_tokens_details.cached_tokens/
output_tokens/output_tokens_details.reasoning_tokens/total_tokens) matches
the same Responses API usage block described across OpenAI developer-
community threads. Unlike Perplexity's async sonar job, nothing in this
payload carries a dollar cost, so cost_usd is always None here rather than
invented from token counts.
"""

from __future__ import annotations

import json

from ..boundary import (
    AdapterParseError,
    AdapterTerminalFailure,
    BoundaryError,
    ParsedResult,
    RequestSpec,
)

BASE_URL = "https://api.openai.com/v1/responses"
MODEL = "o4-mini-deep-research"

# Non-terminal statuses: the job is still queued or running.
_RUNNING_STATUSES = frozenset({"queued", "in_progress"})


def _require_key(env: dict[str, str]) -> str:
    key = env.get("OPENAI_API_KEY")
    if not key:
        raise BoundaryError("OPENAI_API_KEY is not set")
    return key


def submit(query: str, env: dict[str, str]) -> RequestSpec:
    key = _require_key(env)
    body = json.dumps(
        {
            "model": MODEL,
            "input": query,
            "background": True,
            "tools": [{"type": "web_search_preview"}],
        }
    ).encode("utf-8")
    return RequestSpec(
        method="POST",
        url=BASE_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        body=body,
        timeout_s=60.0,
    )


def job_token(payload: bytes) -> str:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"openai accept payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("openai accept payload is not an object")
    token = data.get("id")
    if not isinstance(token, str) or not token:
        raise AdapterParseError("openai accept payload has no id")
    return token


def poll(token: str, env: dict[str, str]) -> RequestSpec:
    key = _require_key(env)
    return RequestSpec(
        method="GET",
        url=f"{BASE_URL}/{token}",
        headers={"Authorization": f"Bearer {key}"},
        body=b"",
        timeout_s=30.0,
    )


def _terminal_failure_message(data: dict) -> str:
    error = data.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str) and error["message"]:
        return error["message"]
    incomplete = data.get("incomplete_details")
    if isinstance(incomplete, dict) and isinstance(incomplete.get("reason"), str) and incomplete["reason"]:
        return f"incomplete: {incomplete['reason']}"
    return f"openai deep job ended with status {data.get('status')!r}"


def extract(payload: bytes) -> ParsedResult | None:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"openai poll payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("openai poll payload is not an object")

    status = data.get("status")
    if not isinstance(status, str) or not status:
        raise AdapterParseError("openai poll payload has no status")
    if status in _RUNNING_STATUSES:
        return None  # queued / in_progress
    if status != "completed":
        # failed / cancelled / incomplete: a well-formed provider-reported
        # terminal state that is not success. Distinct from AdapterParseError:
        # the payload is not malformed -- the job simply did not succeed.
        raise AdapterTerminalFailure(_terminal_failure_message(data))

    output = data.get("output")
    if not isinstance(output, list):
        raise AdapterParseError("openai completed payload has no output array")

    texts: list[str] = []
    citations: list[dict[str, object]] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict) or content.get("type") != "output_text":
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)
            for annotation in content.get("annotations") or []:
                if (
                    isinstance(annotation, dict)
                    and annotation.get("type") == "url_citation"
                    and isinstance(annotation.get("url"), str)
                ):
                    citations.append(
                        {"url": annotation.get("url"), "title": annotation.get("title"), "date": None}
                    )

    synthesis_text = "\n\n".join(texts).strip()
    if not synthesis_text:
        raise AdapterParseError("openai completed payload has no message text")

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return ParsedResult(
        synthesis_text=synthesis_text,
        citations=citations,
        cost_usd=None,  # Responses API reports token usage only, never a dollar cost
        usage=usage,
        model=MODEL,
        kind="search_synthesis",
    )
