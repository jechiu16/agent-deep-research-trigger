# V2 Runtime Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic v2 runtime spine that turns a user-confirmed research contract into canonical JSON state, append-only events, mechanically enforced physical-request ceilings, fail-closed validation, and reproducible HTML.

**Architecture:** Keep provider adapters separate from a stdlib-only `research_harness` core. `state.json` is the only semantic source of truth; `events.jsonl` is an append-only operational journal from which permit use is recomputed. Thin scripts expose stable commands for the host Organizer, while validation and rendering share the same library functions to avoid policy drift.

**Tech Stack:** Python 3.9+, standard library (`dataclasses`, `enum`, `hashlib`, `html`, `json`, `pathlib`, `tempfile`, `unittest`), existing shell CLI conventions.

## Global Constraints

- `/deep` remains an explicit trigger; this runtime never initiates research by itself.
- The contract axes are `epistemic posture x cost tier`: posture is `lookup`, `synthesis`, `scientific`, or `decision`; tier is `low`, `medium`, `high`, or `custom`.
- No physical outbound action is authorized until `contract.confirmed_at` and `contract.confirmed_by=user` exist.
- Ceilings are integer physical-request counts, not estimated dollars; unused permits are never spent automatically.
- Permit categories are `probe`, `deep`, `processor`, `network_experiment`, `transport`, and requested `host_retrieval`.
- A failed or uncertain outbound attempt does not refund a permit.
- Canonical state has complete claim-to-evidence-to-artifact lineage before `PASS`.
- Raw artifact bytes are immutable; state records SHA-256, size, media type, sensitivity, retention, availability, and HTML inclusion.
- HTML is escaped and deterministically derived from `state.json`; it never becomes a second semantic state.
- Runtime code uses no new third-party dependency.
- After every task, compare the implementation against `docs/superpowers/session/2026-07-10-v2-decisions.md` and record any deliberate deviation before continuing.

---

## File Structure

- Create `research_harness/__init__.py`: public version and stable exports.
- Create `research_harness/contracts.py`: posture/tier vocabulary, contract normalization, and validation.
- Create `research_harness/storage.py`: session locking, atomic JSON replacement, append-only event writes, and hashes.
- Create `research_harness/state.py`: canonical state creation, loading, event replay helpers, and compact views.
- Create `research_harness/quota.py`: permit acquisition and physical-attempt lifecycle.
- Create `research_harness/validation.py`: fail-closed schema, quota, lineage, artifact, and tier gates.
- Create `research_harness/rendering.py`: deterministic self-contained HTML renderer.
- Create `scripts/research_state.py`: one Organizer-facing CLI for init, permit, attempt status, validate, render, and view.
- Create `scripts/render_report.py`: narrow rendering entry point for automation.
- Replace `scripts/validate_state.py`: v2 JSON session validator with explicit legacy Markdown fallback during migration.
- Create `tests/`: stdlib `unittest` suite and end-to-end fixtures.
- Create `docs/superpowers/session/2026-07-10-v2-decisions.md`: durable summary of this design session and alignment checklist.

### Task 1: Contract Model and Canonical State Creation

**Files:**
- Create: `research_harness/__init__.py`
- Create: `research_harness/contracts.py`
- Create: `research_harness/state.py`
- Create: `tests/test_contracts.py`
- Create: `tests/test_state.py`

**Interfaces:**
- Produces: `normalize_contract(data: dict) -> dict`
- Produces: `validate_contract(contract: dict) -> list[str]`
- Produces: `new_state(question: str, contract: dict, now: str) -> dict`
- Produces: `state_sha256(state: dict) -> str`

- [ ] **Step 1: Write failing contract tests**

```python
def test_confirmed_contract_normalizes_all_physical_ceilings(self):
    contract = normalize_contract(self.medium_contract())
    self.assertEqual(contract["resource_envelope"]["physical_ceiling"]["probe"], 2)
    self.assertEqual(validate_contract(contract), [])

def test_unconfirmed_contract_is_rejected(self):
    contract = self.medium_contract()
    contract["confirmation"] = {"confirmed_by": None, "confirmed_at": None}
    self.assertIn("contract is not user-confirmed", validate_contract(contract))

def test_negative_or_boolean_ceiling_is_rejected(self):
    contract = self.medium_contract()
    contract["resource_envelope"]["physical_ceiling"]["deep"] = True
    self.assertIn("physical ceiling deep must be a non-negative integer", validate_contract(contract))
```

- [ ] **Step 2: Run the tests and verify missing-module failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_contracts tests.test_state -v`

Expected: `ModuleNotFoundError: No module named 'research_harness'`.

- [ ] **Step 3: Implement the contract vocabulary and validation**

`normalize_contract()` must copy input data, fill every physical category with `0`, preserve the exact `stage_permit_map`, and never infer extra capacity. `validate_contract()` must reject unknown posture/tier, missing confirmation, booleans masquerading as integers, negative ceilings, missing host context/admitted-character ceilings, and stage mappings whose category totals exceed the physical envelope.

```python
POSTURES = frozenset({"lookup", "synthesis", "scientific", "decision"})
TIERS = frozenset({"low", "medium", "high", "custom"})
PHYSICAL_CATEGORIES = (
    "probe", "deep", "processor", "network_experiment", "transport", "host_retrieval"
)

def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
```

- [ ] **Step 4: Implement canonical state creation and stable hashing**

`new_state()` must fail when `validate_contract()` returns errors and create every top-level section from spec section 20.1. `state_sha256()` must hash compact JSON with sorted keys and UTF-8, excluding no fields.

```python
def state_sha256(state):
    payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

- [ ] **Step 5: Run Task 1 tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_contracts tests.test_state -v`

Expected: all Task 1 tests pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add research_harness tests/test_contracts.py tests/test_state.py
git commit -m "feat: add v2 contract and canonical state model"
```

### Task 2: Atomic Session Storage and Append-Only Events

**Files:**
- Create: `research_harness/storage.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Consumes: `new_state()`, `state_sha256()` from Task 1.
- Produces: `create_session(session_dir: Path, state: dict) -> None`
- Produces: `load_state(session_dir: Path) -> dict`
- Produces: `save_state(session_dir: Path, state: dict) -> None`
- Produces: `append_event(session_dir: Path, event: dict) -> dict`
- Produces: `read_events(session_dir: Path) -> tuple[list[dict], list[str]]`
- Produces: `session_lock(session_dir: Path, timeout_s: float = 5.0)` context manager.

- [ ] **Step 1: Write failing storage tests**

```python
def test_create_session_writes_state_and_genesis_event(self):
    create_session(self.session, self.state)
    self.assertEqual(load_state(self.session)["schema_version"], "2.0")
    self.assertEqual(read_events(self.session)[0][0]["event"], "session_created")

def test_append_event_assigns_monotonic_sequence_and_hash_chain(self):
    create_session(self.session, self.state)
    first = append_event(self.session, {"event": "contract_confirmed", "at": self.now})
    second = append_event(self.session, {"event": "note", "at": self.now})
    self.assertEqual(second["seq"], first["seq"] + 1)
    self.assertEqual(second["prev_hash"], first["event_hash"])

def test_malformed_trailing_event_is_reported_without_losing_prior_events(self):
    events, errors = read_events(self.session)
    self.assertEqual(len(events), 1)
    self.assertEqual(errors, ["events.jsonl:2 invalid JSON"])
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_storage -v`

Expected: import failure for `research_harness.storage`.

- [ ] **Step 3: Implement cross-platform lock files and atomic replacement**

Use `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` for the lock, bounded retry with `time.monotonic()`, and cleanup in `finally`. Write JSON to a sibling temporary file, flush and `os.fsync()`, then `os.replace()`.

- [ ] **Step 4: Implement hash-chained event append**

Each event receives `seq`, `prev_hash`, and `event_hash`. Hash the event without `event_hash` using sorted compact JSON. Open `events.jsonl` with `O_APPEND`, write one UTF-8 line, flush, and fsync before returning.

- [ ] **Step 5: Run Task 2 and prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_contracts tests.test_state tests.test_storage -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add research_harness/storage.py tests/test_storage.py
git commit -m "feat: add atomic session storage and event journal"
```

### Task 3: Physical Permit Enforcement

**Files:**
- Create: `research_harness/quota.py`
- Create: `tests/test_quota.py`

**Interfaces:**
- Consumes: `load_state()`, `read_events()`, `append_event()`, `session_lock()`.
- Produces: `acquire_permits(session_dir: Path, action_id: str, stage: str, category: str, count: int, fingerprint: str, now: str) -> list[dict]`
- Produces: `record_attempt_status(session_dir: Path, action_id: str, status: str, now: str, details: Optional[dict] = None) -> dict`
- Produces: `permit_usage(session_dir: Path) -> dict[str, int]`
- Produces: `QuotaExceeded`, `ContractNotConfirmed`, and `DuplicateAction` exceptions.

- [ ] **Step 1: Write failing quota tests**

```python
def test_unconfirmed_contract_cannot_acquire(self):
    with self.assertRaises(ContractNotConfirmed):
        acquire_permits(self.session, "A1", "scout", "probe", 1, "sha256:x", self.now)

def test_atomic_reservation_never_partially_consumes(self):
    with self.assertRaises(QuotaExceeded):
        acquire_permits(self.session, "A1", "scout", "probe", 4, "sha256:x", self.now)
    self.assertEqual(permit_usage(self.session)["probe"], 0)

def test_uncertain_attempt_does_not_refund(self):
    acquire_permits(self.session, "A1", "scout", "probe", 1, "sha256:x", self.now)
    record_attempt_status(self.session, "A1", "uncertain", self.now)
    self.assertEqual(permit_usage(self.session)["probe"], 1)
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_quota -v`

Expected: import failure for `research_harness.quota`.

- [ ] **Step 3: Implement permit reconstruction and atomic acquisition**

Only `permit_acquired` events count toward use. Under one session lock, validate confirmation, category, positive non-boolean count, unique action ID, stage-map allowance, and remaining ceiling before appending one event containing the full count. A failed check appends nothing.

- [ ] **Step 4: Implement attempt lifecycle validation**

Allowed transitions are `acquired -> attempted -> accepted|failed|uncertain`, `accepted -> completed|failed|interrupted`, and `interrupted -> completed|failed`. Reject terminal-to-new-attempt transitions and unknown action IDs. Status events never reduce permit use.

- [ ] **Step 5: Run Task 3 and prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 3**

```bash
git add research_harness/quota.py tests/test_quota.py
git commit -m "feat: enforce physical request permits"
```

### Task 4: Fail-Closed State and Artifact Validation

**Files:**
- Create: `research_harness/validation.py`
- Create: `tests/test_validation.py`

**Interfaces:**
- Consumes: contracts, storage, quota, and state hashing.
- Produces: `Issue(level: str, code: str, message: str, path: str)` dataclass.
- Produces: `ValidationReport(issues: tuple[Issue, ...], state_sha256: str)` with `ok`, `errors`, `warnings`, and `to_dict()`.
- Produces: `validate_session(session_dir: Path) -> ValidationReport`.

- [ ] **Step 1: Write failing validation tests**

```python
def test_pass_rejects_missing_load_bearing_raw_artifact(self):
    self.state["summary"]["status"] = "PASS"
    report = validate_session(self.session)
    self.assertIn("claim.raw_missing", {issue.code for issue in report.errors})

def test_quota_overrun_in_manual_event_fails_validation(self):
    append_event(self.session, self.over_limit_event())
    report = validate_session(self.session)
    self.assertIn("quota.exceeded", {issue.code for issue in report.errors})

def test_high_pass_requires_context_separated_verifier(self):
    self.state["contract"]["tier"] = "high"
    self.state["summary"]["status"] = "PASS"
    report = validate_session(self.session)
    self.assertIn("tier.high_verifier_missing", {issue.code for issue in report.errors})
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_validation -v`

Expected: import failure for `research_harness.validation`.

- [ ] **Step 3: Implement universal structural gates**

Validate required top-level sections, contract, event hash chain, exact permit reconciliation, claim/evidence/source/artifact IDs, exact excerpt bounds, SHA-256 and size of available raw files, and absence of `purge_pending` artifacts.

- [ ] **Step 4: Implement fail-closed `PASS` gates**

For every load-bearing claim, require a recognized passing status, supporting evidence, source origin, available raw artifact, and applicability when required. Scientific/decision Medium and High require anti-lock-in and coverage-audit verification records. High requires a verifier record with `context_separated=true` and `produced_candidate=false`.

- [ ] **Step 5: Run Task 4 and all prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 4**

```bash
git add research_harness/validation.py tests/test_validation.py
git commit -m "feat: add fail-closed v2 session validation"
```

### Task 5: Deterministic HTML Renderer

**Files:**
- Create: `research_harness/rendering.py`
- Create: `tests/test_rendering.py`

**Interfaces:**
- Consumes: `load_state()`, `state_sha256()`, `validate_session()`.
- Produces: `render_html(state: dict, report: ValidationReport) -> str`
- Produces: `render_session(session_dir: Path) -> Path`.

- [ ] **Step 1: Write failing renderer tests**

```python
def test_same_state_renders_identical_bytes(self):
    first = render_session(self.session).read_bytes()
    second = render_session(self.session).read_bytes()
    self.assertEqual(first, second)

def test_untrusted_content_is_escaped(self):
    self.state["summary"]["decision"] = '<script>alert("x")</script>'
    html = render_html(self.state, self.report)
    self.assertNotIn("<script>", html)
    self.assertIn("&lt;script&gt;", html)

def test_html_embeds_current_state_hash(self):
    html = render_html(self.state, self.report)
    self.assertIn(state_sha256(self.state), html)
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_rendering -v`

Expected: import failure for `research_harness.rendering`.

- [ ] **Step 3: Implement escaped, self-contained rendering**

Use only inline CSS, semantic HTML, `<details>` for evidence, text labels in addition to colors, bounded exact excerpts, artifact links only when `include_in_html=true` and sensitivity permits, and no JavaScript or network assets. Use `state.session.updated_at` as the displayed generation time so identical state yields identical bytes.

- [ ] **Step 4: Implement atomic `report.html` replacement**

Write and fsync a sibling temporary file, then replace `report.html`. Rendering may display validation failures but must label the report `INVALID`; it never changes canonical verdicts.

- [ ] **Step 5: Run Task 5 and all prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 5**

```bash
git add research_harness/rendering.py tests/test_rendering.py
git commit -m "feat: render deterministic research reports"
```

### Task 6: Organizer CLI and End-to-End Contract Test

**Files:**
- Create: `scripts/research_state.py`
- Create: `scripts/render_report.py`
- Replace: `scripts/validate_state.py`
- Create: `tests/test_cli.py`
- Create: `examples/v2/medium-contract.json`
- Create: `examples/v2/README.md`

**Interfaces:**
- Consumes all Task 1-5 library interfaces.
- Produces CLI commands `init`, `permit`, `status`, `validate`, `render`, and `view`.

- [ ] **Step 1: Write failing CLI end-to-end tests**

```python
def test_init_permit_validate_render_flow(self):
    self.run_cli("init", str(self.session), "--question", "Choose a cache", "--contract", str(self.contract))
    self.run_cli("permit", str(self.session), "--action-id", "A1", "--stage", "scout",
                 "--category", "probe", "--count", "1", "--fingerprint", "sha256:test")
    validated = self.run_cli("validate", str(self.session), "--json")
    rendered = self.run_cli("render", str(self.session), "--json")
    self.assertTrue(json.loads(validated.stdout)["ok"])
    self.assertTrue(Path(json.loads(rendered.stdout)["report_path"]).exists())

def test_cli_refuses_unconfirmed_contract(self):
    result = self.run_cli("init", str(self.session), "--question", "Q", "--contract", str(self.unconfirmed), check=False)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("contract is not user-confirmed", result.stderr)
```

- [ ] **Step 2: Run tests and verify missing-command failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_cli -v`

Expected: CLI path or command failure.

- [ ] **Step 3: Implement thin JSON-first CLIs**

All successful commands print exactly one JSON object on stdout when `--json` is passed; progress and errors go to stderr. `validate_state.py` accepts a v2 session directory or `state.json`; when given legacy Markdown, it calls the retained legacy validator path and labels output `schema_version=legacy`.

- [ ] **Step 4: Add a real confirmed Medium contract example**

The example uses one Sonar scout probe, optional one deep permit, one host anti-lock-in action, one host verification/audit pass, zero processors, four transport requests, a `standard` host context class, and exact admitted-character/raw-storage ceilings.

- [ ] **Step 5: Run the end-to-end suite and CLI smoke**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Run: `tmp=$(mktemp -d); /Users/jechiu/dev/parallax/.venv/bin/python scripts/research_state.py init "$tmp/session" --question "CLI smoke" --contract examples/v2/medium-contract.json --json`

Expected: all tests pass and init prints a JSON object containing `state_path` and `session_id`.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts research_harness tests examples/v2
git commit -m "feat: add v2 organizer runtime CLI"
```

### Task 7: Documentation, Regression Gates, and Slice Review

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `SKILL.md`
- Modify: `AGENTS.md`
- Modify: `HARNESS.md`
- Modify: `requirements.txt`
- Create: `tests/test_docs.py`
- Create: `docs/superpowers/session/2026-07-10-v2-decisions.md`

**Interfaces:**
- Consumes: stable CLI from Task 6.
- Produces: host-neutral v2 invocation contract and exact verification commands.

- [ ] **Step 1: Write failing documentation consistency tests**

```python
def test_bindings_use_posture_and_tier(self):
    for path in ("SKILL.md", "AGENTS.md", "HARNESS.md"):
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("posture", text.lower())
        self.assertIn("tier", text.lower())
        self.assertNotIn("depth x independence x strictness", text)

def test_readmes_reference_v2_cli(self):
    for path in ("README.md", "README.zh-TW.md"):
        self.assertIn("scripts/research_state.py", Path(path).read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the tests and verify they fail on v1 bindings**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_docs -v`

Expected: failures showing old contract language and missing CLI references.

- [ ] **Step 3: Rewrite runtime-facing documentation to v2**

Keep the design spec as rationale. Make `HARNESS.md` the concise executable protocol: contract card, stage permit map, one scout route, adaptive tuple, anti-lock-in, coverage audit, validation, render, and delivery. Update both host bindings to require user confirmation before `research_state.py init` and require `validate` before `PASS`.

- [ ] **Step 4: Keep runtime requirements minimal**

Do not add a core dependency. Retain provider dependencies in `requirements.txt`; tests use stdlib `unittest`.

- [ ] **Step 5: Run all deterministic release checks**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m py_compile research_harness/*.py scripts/*.py`

Run: `/Users/jechiu/dev/parallax/.venv/bin/python /Users/jechiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py .`

Run: `/Users/jechiu/dev/parallax/.venv/bin/python scripts/validate_transcripts.py --json`

Expected: all unit tests pass, every Python file compiles, skill metadata is valid, and all golden transcript fixtures pass or have been intentionally migrated with matching validator changes.

- [ ] **Step 6: Request independent spec and code review**

Give the reviewer the v2 design spec, this plan, the full branch diff, and the test output. Ask only for concrete Critical/High correctness, bypass, data-loss, privacy, or contract-drift findings. Resolve every demonstrated finding and rerun Step 5.

- [ ] **Step 7: Run the session-alignment audit**

Compare every row in `docs/superpowers/session/2026-07-10-v2-decisions.md` against code, tests, and runtime-facing docs. Mark each item `implemented`, `deferred with named follow-on plan`, or `contradicted`. Any contradiction blocks the slice; a deferral is allowed only when the slice exit criteria do not claim it.

- [ ] **Step 8: Commit Task 7**

```bash
git add README.md README.zh-TW.md SKILL.md AGENTS.md HARNESS.md requirements.txt tests/test_docs.py docs/superpowers/session/2026-07-10-v2-decisions.md
git commit -m "docs: bind hosts to the v2 runtime"
```

## Slice Exit Criteria

- A user-confirmed Medium contract can create a v2 session without network access.
- The runtime rejects every permit acquisition before confirmation or beyond the exact category ceiling.
- Multi-permit reservations are atomic; failed and uncertain attempts remain consumed.
- Event history is append-only, sequence-numbered, and hash-chained.
- `PASS` fails closed on missing load-bearing lineage, missing raw evidence, quota mismatch, incomplete scientific checkpoints, or missing High verifier separation.
- The same canonical state renders byte-identical escaped HTML.
- CLI output is machine-readable and host-neutral.
- All deterministic tests pass from a clean worktree.
- No paid provider call is required for this slice.

## Deferred Follow-On Plans

This slice deliberately does not claim the full goal is complete. The next independently testable plans are:

1. Worker enforcement: bind `deep_research.py` provider submission, retry, polling, resume, and raw payload handling to v2 research and transport permits.
2. Organizer protocol: branch manifests, evidence deltas, adaptive routing tuple, anti-lock-in, coverage audit, verifier packets, and purge state transitions.
3. Comparative evaluation: deterministic adversarial fixtures, paired baseline runner, blinded adjudication artifacts, sequential stopping, and tier-specific release ledgers.
4. Distribution and polish: global installer, migration tooling, bilingual docs, examples, terminal UX, CI matrix, release provenance, and GitHub-ready packaging.
