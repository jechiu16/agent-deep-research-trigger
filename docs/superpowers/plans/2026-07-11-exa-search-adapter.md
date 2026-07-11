# Exa Search Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a permit-gated Exa web-search adapter that returns context-efficient result listings with provider-reported cost while keeping model synthesis and deep-search modes out of the probe route.

**Architecture:** Bind one synchronous `POST https://api.exa.ai/search` to `execute_probe`. Request `type=auto`, ten results, and highlights in one provider request; parse only resolvable result URLs into discovery citations. Record fixture and live-boundary evidence, but keep the route disabled until its required paired index benchmark clears the portfolio adoption gate.

**Tech Stack:** Python 3.12 standard library, `unittest`, fixture replay, v2 request boundary.

## Global Constraints

- One `probe` permit authorizes exactly one Exa Search API request.
- `EXA_API_KEY` is required and sent only in the `x-api-key` header.
- The route does not request `outputSchema`, summaries, deep modes, or streaming.
- Search results and highlights are discovery metadata and cannot directly support claims.
- The live response fixture must contain no credential and must remain session-retention only.

---

### Task 1: Define The Request And Parse Contracts

**Files:**
- Create: `tests/test_exa.py`
- Create: `research_harness/adapters/exa.py`

**Interfaces:**
- Produces: `build(query: str, env: dict[str, str]) -> RequestSpec`
- Produces: `parse(payload: bytes) -> ParsedResult`

- [x] **Step 1: Write failing build tests**

Require `EXA_API_KEY`, `POST /search`, `x-api-key`, JSON content type, `type=auto`, `numResults=10`, and `contents.highlights=true`. Assert no deep mode, output schema, summary, text, or stream option is present.

- [x] **Step 2: Run build tests and observe the missing module failure**

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_exa.ExaBuildTests -v`

- [x] **Step 3: Implement the minimal build function**

Return a 60-second `RequestSpec` and raise `BoundaryError("EXA_API_KEY is not set")` before any request is attempted.

- [x] **Step 4: Write failing parse tests**

Cover invalid JSON, missing/non-list results, valid URL filtering, bounded highlight rendering, provider cost extraction, empty result sets, and malformed optional fields.

- [x] **Step 5: Implement minimal deterministic parsing**

Produce `kind="result_listing"`, `model="exa/search-auto"`, citation records shaped as URL/title/date, and `cost_usd` from numeric `costDollars.total`.

### Task 2: Bind Fixtures And Boundary Lifecycle

**Files:**
- Modify: `research_harness/adapters/__init__.py`
- Modify: `research_harness/provider_registry.json`
- Create: `tests/fixtures/exa_success.json`
- Create: `tests/fixtures/exa_error_body.json`
- Create: `tests/fixtures/exa_missing_results.json`

**Interfaces:**
- Produces: `exa-search@v1` adapter binding and fixture-replay coverage

- [x] **Step 1: Add boundary lifecycle tests**

Cover successful occurrence creation, raw spool preservation, missing-key refusal before attempt, HTTP failure consumption, parse failure, timeout uncertainty, transport failure, duplicate execution, and unknown action refusal.

- [x] **Step 2: Add the disabled validated registry record**

Declare `probe` only, `result-listing`, independent Exa index, `can_support_claims=false`, session payload retention, exact required environment, current metering, and sync transport.

- [x] **Step 3: Record one live provider response through the v2 boundary**

Use one user-authorized physical request, preserve the secret-free response as `exa_success.json`, validate the scratch session, and record citation count, cost, and occurrence evidence.

- [x] **Step 4: Run adapter and full-suite verification**

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_exa -v`

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -q`

### Task 3: Review, Commit, And Integrate

**Files:**
- Review all files above

- [x] **Step 1: Run secret scan, compile, transcript, skill, and diff checks**

- [x] **Step 2: Request an independent read-only code review**

- [ ] **Step 3: Commit the isolated Exa branch**

- [ ] **Step 4: Cherry-pick onto `codex/v2-runtime-foundation` and rerun the current full suite**
