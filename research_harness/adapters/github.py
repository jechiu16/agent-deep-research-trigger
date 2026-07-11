"""github adapter: repository record fetch (source of record).

Query is "owner/repo". GET /repos/{owner}/{repo} on api.github.com; the JSON
body IS the canonical record (no synthesis, no aggregation) — unlike sonar's
search_synthesis shape, this is a direct source-of-record fetch, so
``evidence_capabilities.can_support_claims`` is true for this route.
"""

from __future__ import annotations

import json
import re

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec

_OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def build(query: str, env: dict[str, str]) -> RequestSpec:
    if not _OWNER_REPO_RE.fullmatch(query):
        raise BoundaryError(f'github query must match "owner/repo", got: {query!r}')
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "research-harness-v2",
    }
    token = env.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return RequestSpec(
        method="GET",
        url=f"https://api.github.com/repos/{query}",
        headers=headers,
        # A true GET carries no body. RequestSpec.body is typed as plain
        # ``bytes`` (not Optional), so b"" is the only representable "no
        # body" value here — see the adapter build report for the urllib
        # transport friction that empty-but-not-None body causes.
        body=b"",
        timeout_s=30.0,
    )


_RENDER_FIELDS = (
    "full_name",
    "description",
    "default_branch",
    "license.spdx_id",
    "stargazers_count",
    "open_issues_count",
    "archived",
    "pushed_at",
)


def _field_value(data: dict, dotted_key: str):
    if dotted_key == "license.spdx_id":
        license_obj = data.get("license")
        return license_obj.get("spdx_id") if isinstance(license_obj, dict) else None
    return data.get(dotted_key)


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"github payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("github payload is not a JSON object")

    full_name = data.get("full_name")
    html_url = data.get("html_url")
    if not isinstance(full_name, str) or not full_name:
        raise AdapterParseError("github payload has no full_name")
    if not isinstance(html_url, str) or not html_url:
        raise AdapterParseError("github payload has no html_url")

    # Deterministic compact rendering: fixed field order, one per line,
    # missing/null values render as an empty string so line count and order
    # never shift between repos.
    lines = []
    for key in _RENDER_FIELDS:
        value = _field_value(data, key)
        lines.append(f"{key}: {'' if value is None else value}")
    synthesis_text = "\n".join(lines)

    citations = [{"url": html_url, "title": full_name, "date": data.get("pushed_at")}]

    return ParsedResult(
        synthesis_text=synthesis_text,
        citations=citations,
        cost_usd=None,
        usage={},
        model="github-repos/v3",
        kind="record_fetch",
    )
