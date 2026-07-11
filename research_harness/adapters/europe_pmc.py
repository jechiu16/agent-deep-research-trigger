"""europe_pmc adapter: Europe PMC REST search, sync scholarly paper listing.

Provider id in the capability registry is "europe-pmc" (hyphenated). Python
module names cannot contain a hyphen, so this module is "europe_pmc" and the
bridge lives in adapters/__init__.py's registration key
("europepmc-rest-search@v1" -> this module's build/parse) rather than in the
module name itself.

Query is free text against Europe PMC's federated literature index (MEDLINE,
PMC, Agricola, etc. — see ``source`` on each result). The endpoint is keyless;
``env`` is accepted only to satisfy the shared adapter signature.
"""

from __future__ import annotations

import json
import urllib.parse
from typing import Optional

from ..boundary import AdapterParseError, ParsedResult, RequestSpec

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE_SIZE = 20


def build(query: str, env: dict[str, str]) -> RequestSpec:
    # Keyless: the Europe PMC REST search endpoint never takes a credential.
    del env
    params = {"query": query, "format": "json", "pageSize": PAGE_SIZE}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    return RequestSpec(
        method="GET",
        url=url,
        headers={"User-Agent": "research-harness-v2"},
        body=b"",
        timeout_s=30.0,
    )


def _citation_url(result: dict) -> Optional[str]:
    doi = result.get("doi")
    if isinstance(doi, str) and doi:
        return f"https://doi.org/{doi}"
    # doi is absent on a minority of records (preprints, some PMC-only
    # entries); source+id is Europe PMC's own primary key for every record
    # and is what europepmc.org's own abstract pages resolve on, so it is a
    # reliable fallback rather than a last resort.
    source = result.get("source")
    identifier = result.get("id")
    if isinstance(source, str) and source and isinstance(identifier, str) and identifier:
        return f"https://europepmc.org/abstract/{source}/{identifier}"
    return None


def parse(payload: bytes) -> ParsedResult:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterParseError(f"europe_pmc payload is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AdapterParseError("europe_pmc payload is not a JSON object")
    result_list = data.get("resultList")
    if not isinstance(result_list, dict):
        raise AdapterParseError("europe_pmc payload has no resultList")
    results = result_list.get("result")
    if not isinstance(results, list):
        raise AdapterParseError("europe_pmc payload resultList has no result list")

    hit_count = data.get("hitCount")

    lines = [
        f"Europe PMC paper search: {len(results)} of "
        f"{hit_count if isinstance(hit_count, int) else '?'} results\n"
    ]
    citations = []
    for result in results:
        if not isinstance(result, dict):
            continue
        title = result.get("title") if isinstance(result.get("title"), str) else "(untitled)"
        author_string = (
            result.get("authorString") if isinstance(result.get("authorString"), str) else None
        )
        pub_year = result.get("pubYear") if isinstance(result.get("pubYear"), str) else None
        lines.append(
            f"\n- {title} ({pub_year if pub_year is not None else '?'})"
            + (f" — {author_string}" if author_string else "")
        )
        citation_url = _citation_url(result)
        # Only records that resolve to a usable URL count as citations, same
        # rule openalex/exa use — citation_count downstream is meant to
        # measure clickable evidence, not every listed row. In practice
        # source+id are always present on real Europe PMC records, so this
        # never trims a real response (see tests/fixtures/europe_pmc_success.json).
        if citation_url is not None:
            citations.append({"url": citation_url, "title": title, "date": pub_year})

    return ParsedResult(
        synthesis_text="".join(lines),
        citations=citations,
        cost_usd=None,
        usage={"total_results": hit_count, "returned": len(results)},
        model="europepmc/rest-search",
        kind="paper_listing",
    )
