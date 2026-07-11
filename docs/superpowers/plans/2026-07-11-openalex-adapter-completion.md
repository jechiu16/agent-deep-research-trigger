# OpenAlex Adapter Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete and adopt the OpenAlex scholarly-search adapter against the current authenticated API contract without weakening v2 permit, provenance, or storage controls.

**Architecture:** Keep OpenAlex as a synchronous `build/parse` adapter behind `execute_probe`. Require `OPENALEX_API_KEY`, request only fields needed for a deterministic paper listing, derive provider-reported request cost from `meta.cost_usd`, and keep search output discovery-only until direct sources are fetched.

**Tech Stack:** Python 3.12 standard library, `unittest`, fixture replay, v2 request boundary.

## Global Constraints

- One acquired `probe` permit authorizes one physical OpenAlex request.
- API credentials come from `env` and never appear in committed fixtures or reports.
- OpenAlex search results are `paper_listing` discovery output and cannot directly support claims.
- The committed success fixture must be a recorded provider response.
- Live verification uses one user-authorized request and records only secret-free evidence.

---

### Task 1: Correct The OpenAlex Request Contract

**Files:**
- Modify: `tests/test_openalex.py`
- Modify: `research_harness/adapters/openalex.py`

**Interfaces:**
- Consumes: `build(query: str, env: dict[str, str]) -> RequestSpec`
- Produces: an authenticated GET request using `OPENALEX_API_KEY` and bounded response fields

- [x] **Step 1: Write failing build tests**

Assert that an empty environment raises `BoundaryError`, the key is sent as the documented `api_key` query parameter, the deprecated `mailto` parameter is absent, and a fixed `select` field list is present.

- [x] **Step 2: Run the build-test class and confirm the old keyless behavior fails**

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_openalex.OpenAlexBuildTests -v`

Expected: failures showing that the old adapter accepts a missing key and still emits `mailto`.

- [x] **Step 3: Implement the authenticated request**

Use `BoundaryError("OPENALEX_API_KEY is not set")`, remove `MAILTO`, and construct the URL from `search`, `per_page`, `select`, and `api_key` only.

- [x] **Step 4: Re-run the build tests**

Expected: all `OpenAlexBuildTests` pass.

### Task 2: Preserve Cost And Reliability Metadata

**Files:**
- Modify: `tests/test_openalex.py`
- Modify: `research_harness/adapters/openalex.py`

**Interfaces:**
- Consumes: recorded OpenAlex response bytes
- Produces: `ParsedResult(kind="paper_listing")` with `cost_usd`, citations, and deterministic synthesis

- [x] **Step 1: Write failing parse tests**

Assert `cost_usd == meta.cost_usd`, include a visible retraction marker when `is_retracted` is true, and reject an empty result set as a valid but empty listing rather than fabricating evidence.

- [x] **Step 2: Run the parse-test class and confirm the cost assertion fails**

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_openalex.OpenAlexParseTests -v`

Expected: failure because the current adapter always returns `cost_usd=None`.

- [x] **Step 3: Implement minimal parsing changes**

Read numeric `meta.cost_usd`, round it to six decimal places, add `[RETRACTED]` to retracted listing lines, and keep citations source-resolvable through DOI, landing page, or OpenAlex ID.

- [x] **Step 4: Re-run adapter tests**

Expected: all OpenAlex tests pass.

### Task 3: Verify And Adopt The Route

**Files:**
- Modify: `research_harness/provider_registry.json`
- Modify: `research_harness/adapters/__init__.py`
- Verify: `tests/fixtures/openalex_*.json`

**Interfaces:**
- Produces: enabled `openalex-works-search@v1` registry binding with live adoption evidence

- [x] **Step 1: Run fixture and full-suite verification**

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_openalex -v`

Run: `PYTHONPATH=. /Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -q`

- [x] **Step 2: Run one live v2 boundary session**

Create a scratch confirmed session, acquire one OpenAlex `probe` permit, call `execute_probe`, and require validation with no errors. Do not commit the session or credential.

- [x] **Step 3: Update registry adoption facts**

Set `required_env` to `OPENALEX_API_KEY`, document the current search price, retain `can_support_claims=false`, and enable only after fixture plus live evidence pass.

- [ ] **Step 4: Rebase the isolated commit onto current runtime head**

Commit the OpenAlex worktree, cherry-pick it onto `codex/v2-runtime-foundation`, resolve registry/adapter registration conflicts surgically, and rerun the full suite there.
