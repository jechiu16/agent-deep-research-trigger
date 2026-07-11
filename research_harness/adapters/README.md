# Adapter Development Guide

One provider, one module, one exact contract. `sonar.py` is the golden
example; `tests/test_boundary.py` is the golden test pattern. Deviating from
either needs a written reason in your report.

## Deliverables (definition of done)

1. `research_harness/adapters/<provider>.py` with two pure functions:
   - `build(query, env) -> RequestSpec` — no network, no side effects; raise
     `BoundaryError` naming the missing env var if a credential is absent.
   - `parse(payload: bytes) -> ParsedResult` — raise `AdapterParseError` on
     any payload that does not match the provider contract. Never return a
     half-parsed result.
2. One registration line in `adapters/__init__.py`, key `<adapter>@<version>`
   exactly matching the capability registry record.
3. Registry record in `provider_registry.json` completed to enabled-route
   standard (see the `sonar` block): adapter/version, `execution_binding:
   "v2_request_boundary"`, honest `evidence_capabilities`, conservative
   `storage_rights` with `verified_at` + `source`, `metering`, `transport`,
   `controls`, `docs_verified_at`. Leave `enabled: false` — the orchestrator
   flips it after verifying evidence.
4. Fixtures under `tests/fixtures/`:
   - `<provider>_success.json` — a RECORDED real response (run one live call;
     keyless routes need no credentials). Synthetic success fixtures are not
     acceptable; fixtures must reflect the real API shape.
   - At least two failure fixtures (malformed/missing-field, provider error
     body such as 429 or 4xx).
5. `tests/test_<provider>.py` following `test_boundary.py`: success
   expectations read dynamically FROM the fixture (re-recording must not break
   tests), plus HTTP-error, parse-failure, and permit-consumption checks.
   Build sessions with `confirmed_demo_contract(route="<provider>", ...)`.
6. Full suite green: `python -m unittest discover -s tests -q`.
7. A live end-to-end evidence run in a scratch directory (NOT committed):
   contract → `init` → `permit` → `execute` → `validate` returns `ok=true`.
   Record its cost, citation/record count, and occurrence id in your report.

## Rules that are not negotiable

- stdlib only. No `requests`, no third-party packages.
- Credentials come in via `env`; they never appear in code, fixtures,
  occurrences, fingerprints, or reports.
- Respect provider rate limits during the live call (Semantic Scholar: one
  request per second, never parallel).
- `ParsedResult.kind` must be honest: `search_synthesis` (model-written
  synthesis over search), `paper_listing` (scholarly metadata listing),
  `record_fetch` (the payload IS the canonical record).
- `evidence_capabilities.can_support_claims`: `false` for search/listing
  shapes (their output guides retrieval; it is not claim evidence). `true`
  only for direct source-of-record fetch shapes, and then
  `requires_direct_fetch: true` stays.
- Do not touch other adapters, the boundary core, storage, quota, or docs.
- Report any friction with the adapter protocol instead of working around
  it — the schema is in DRAFT and your friction report is the input that
  locks it.
