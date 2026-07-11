"""ietf adapter: RFC metadata record fetch (source of record).

Query is an RFC number ("9110") or RFC identifier ("rfc9110"), case-
insensitive. GET /rfc/rfc<n>.json on www.rfc-editor.org; the JSON body IS the
canonical RFC metadata record (no synthesis, no aggregation) — same
record-fetch shape as github/pypi, so
``evidence_capabilities.can_support_claims`` is true for this route.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec

# Accepts "9110" or "rfc9110" (case-insensitive); the "rfc" prefix is
# optional and stripped before validating the numeric part, which is then
# normalized to a plain int (so e.g. "rfc09110" would request rfc9110.json).
# Current RFC numbers are 4-5 digits; 1-5 digits leaves headroom without
# accepting unbounded input.
_RFC_QUERY_RE = re.compile(r"^(?:rfc)?(\d{1,5})$", re.IGNORECASE)


def build(query: str, env: dict[str, str]) -> RequestSpec:
    # www.rfc-editor.org/rfc/rfcN.json is keyless: no credential is ever
    # attached, so `env` is accepted only to satisfy the shared adapter
    # signature.
    del env
    match = _RFC_QUERY_RE.fullmatch(query)
    if not match:
        raise BoundaryError(
            f'ietf query must be an RFC number like "9110" or "rfc9110", got: {query!r}'
        )
    number = int(match.group(1))
    return RequestSpec(
        method="GET",
        url=f"https://www.rfc-editor.org/rfc/rfc{number}.json",
        headers={
            "Accept": "application/json",
            "User-Agent": "research-harness-v2",
        },
        body=b"",
        timeout_s=30.0,
    )


_RENDER_FIELDS = ("doc_id", "title", "status", "pub_date", "authors", "obsoletes", "obsoleted_by")


def _string_list(value: Any) -> list[str]:
    """A payload field that should be a list of strings, tolerantly. A
    present-but-malformed non-list (e.g. a bare string, which is itself
    iterable and would otherwise be silently walked character-by-character)
    degrades to empty rather than mis-parsing or raising an uncaught
    TypeError — only doc_id/title are load-bearing here."""

    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"ietf payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("ietf payload is not a JSON object")

    doc_id = data.get("doc_id")
    title = data.get("title")
    if not isinstance(doc_id, str) or not doc_id:
        raise AdapterParseError("ietf payload has no doc_id")
    if not isinstance(title, str) or not title:
        raise AdapterParseError("ietf payload has no title")

    status = data.get("status") if isinstance(data.get("status"), str) else None
    pub_date = data.get("pub_date") if isinstance(data.get("pub_date"), str) else None
    authors = _string_list(data.get("authors"))
    obsoletes = _string_list(data.get("obsoletes"))
    obsoleted_by = _string_list(data.get("obsoleted_by"))
    abstract = data.get("abstract")
    abstract = abstract if isinstance(abstract, str) and abstract.strip() else None

    # Deterministic compact rendering: fixed field order, one per line,
    # missing/empty values render as an empty string so line count and order
    # never shift between RFCs (matches github/pypi's _RENDER_FIELDS
    # pattern). abstract is free-form prose of unbounded length (unlike the
    # other fields here), so it is appended as one extra trailing line only
    # when present rather than folded into the fixed-field block.
    values = {
        "doc_id": doc_id,
        "title": title,
        "status": status,
        "pub_date": pub_date,
        "authors": ", ".join(authors),
        "obsoletes": ", ".join(obsoletes),
        "obsoleted_by": ", ".join(obsoleted_by),
    }
    lines = [f"{key}: {values[key] or ''}" for key in _RENDER_FIELDS]
    if abstract:
        lines.append(f"abstract: {abstract}")
    synthesis_text = "\n".join(lines)

    citations = [
        {
            "url": f"https://www.rfc-editor.org/rfc/{doc_id.lower()}",
            "title": f"{doc_id}: {title}",
            "date": pub_date,
        }
    ]

    return ParsedResult(
        synthesis_text=synthesis_text,
        citations=citations,
        cost_usd=None,
        usage={},
        model="rfc-editor-json/v1",
        kind="record_fetch",
    )
