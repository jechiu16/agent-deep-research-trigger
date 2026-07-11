"""nvd adapter: NVD CVE record fetch (source of record).

Query is a CVE id (``CVE-YYYY-NNNN...``, case-insensitive on input, always
uppercased before the request). GET
https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<id> on
services.nvd.nist.gov; ``vulnerabilities[0].cve`` IS the canonical CVE
record (no synthesis, no aggregation) — same record-fetch shape as github
and pypi, so ``evidence_capabilities.can_support_claims`` is true for this
route.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from ..boundary import AdapterParseError, BoundaryError, ParsedResult, RequestSpec

_CVE_ID_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)

_DESCRIPTION_LIMIT = 300

# Preference order when more than one CVSS metric version is present: newest
# schema first. Within a version's entry list, the NVD-authored "Primary"
# entry wins over "Secondary" (CNA-supplied) entries; if none is marked
# Primary, the first entry is used.
_CVSS_METRIC_KEYS = ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2")


def build(query: str, env: dict[str, str]) -> RequestSpec:
    if not _CVE_ID_RE.fullmatch(query):
        raise BoundaryError(f"nvd query must be a CVE id like CVE-YYYY-NNNN, got: {query!r}")
    cve_id = query.upper()
    headers = {"User-Agent": "research-harness-v2"}
    key = env.get("NVD_API_KEY")
    if key:
        headers["apiKey"] = key
    return RequestSpec(
        method="GET",
        url=f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}",
        headers=headers,
        # A true GET carries no body. RequestSpec.body is typed as plain
        # ``bytes`` (not Optional), so b"" is the only representable "no
        # body" value here — see boundary._urllib_transport, which sends
        # data=None for an empty body so the request stays a true GET.
        body=b"",
        timeout_s=30.0,
    )


def _base_score(cve: dict[str, Any]) -> Optional[float]:
    metrics = cve.get("metrics")
    if not isinstance(metrics, dict):
        return None
    for key in _CVSS_METRIC_KEYS:
        entries = metrics.get(key)
        if not isinstance(entries, list) or not entries:
            continue
        primary = next(
            (item for item in entries if isinstance(item, dict) and item.get("type") == "Primary"),
            entries[0],
        )
        if not isinstance(primary, dict):
            continue
        cvss_data = primary.get("cvssData")
        if not isinstance(cvss_data, dict):
            continue
        score = cvss_data.get("baseScore")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            return float(score)
    return None


def _en_description(cve: dict[str, Any]) -> str:
    descriptions = cve.get("descriptions")
    if not isinstance(descriptions, list):
        return ""
    for item in descriptions:
        if isinstance(item, dict) and item.get("lang") == "en" and isinstance(item.get("value"), str):
            return item["value"]
    return ""


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"nvd payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("nvd payload is not a JSON object")

    vulnerabilities = data.get("vulnerabilities")
    if not isinstance(vulnerabilities, list) or not vulnerabilities:
        raise AdapterParseError("nvd payload has no vulnerabilities")
    first = vulnerabilities[0]
    if not isinstance(first, dict):
        raise AdapterParseError("nvd payload vulnerabilities[0] is not an object")
    cve = first.get("cve")
    if not isinstance(cve, dict):
        raise AdapterParseError("nvd payload has no cve object")
    cve_id = cve.get("id")
    if not isinstance(cve_id, str) or not cve_id:
        raise AdapterParseError("nvd payload cve.id is absent")

    vuln_status = cve.get("vulnStatus")
    published = cve.get("published")
    last_modified = cve.get("lastModified")
    base_score = _base_score(cve)
    description = _en_description(cve)[:_DESCRIPTION_LIMIT]

    # Deterministic compact rendering: fixed field order, one per line,
    # missing/null values render as an empty string so line count and order
    # never shift between CVE records (matches github/pypi's rendering
    # pattern).
    lines = [
        f"id: {cve_id}",
        f"vulnStatus: {vuln_status if isinstance(vuln_status, str) else ''}",
        f"published: {published if isinstance(published, str) else ''}",
        f"lastModified: {last_modified if isinstance(last_modified, str) else ''}",
        f"baseScore: {'' if base_score is None else base_score}",
        f"description: {description}",
    ]
    synthesis_text = "\n".join(lines)

    citations = [
        {
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "title": cve_id,
            "date": last_modified if isinstance(last_modified, str) else None,
        }
    ]

    return ParsedResult(
        synthesis_text=synthesis_text,
        citations=citations,
        cost_usd=None,
        usage={"total_results": data.get("totalResults")},
        model="nvd-cve/v2.0",
        kind="record_fetch",
    )
