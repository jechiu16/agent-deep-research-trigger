# V2 Runtime Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic v2 runtime spine that turns a user-confirmed research contract and versioned provider-capability snapshot into canonical JSON state, append-only events, mechanically enforced physical-request ceilings, fail-closed validation, and reproducible HTML.

**Architecture:** Keep provider adapters separate from a stdlib-only `research_harness` core. `state.json` is the only semantic source of truth; `events.jsonl` is an append-only operational journal from which permit use is recomputed. Thin scripts expose stable commands for the host Organizer, while validation and rendering share the same library functions to avoid policy drift.

**Tech Stack:** Python 3.9+, standard library (`dataclasses`, `enum`, `hashlib`, `html`, `json`, `pathlib`, `tempfile`, `unittest`), existing shell CLI conventions.

## Global Constraints

- `/deep` remains an explicit trigger; this runtime never initiates research by itself.
- The contract axes are `epistemic posture x cost tier`: posture is `lookup`, `synthesis`, `scientific`, or `decision`; tier is `low`, `medium`, `high`, or `custom`.
- No physical outbound action is authorized until the confirmation records `confirmed_at`, `confirmed_by=user`, and matching hashes for the normalized card, resolved registry, and referenced route records.
- Ceilings are integer action/request counts, not estimated dollars; unused capacity is never spent automatically.
- Action categories are `probe`, `deep`, `processor`, `network_experiment`, `transport`, `host_retrieval`, `local`, and `organizer_pass`. The contract keeps external, host, and local envelopes separate even though the stage map references all categories.
- Exactly one `primary_scout` mapping with `invocations=1` is required. Its physical `count` equals the selected route's registry-declared request multiplicity; ordinary routes are `1/1`, while an explicitly approved composite route may be `1/n`. Reserved challenge or verification mappings are stage-scoped and cannot be consumed by discovery.
- Provider IDs, roles, index families, retention rights, metering, and transport capabilities come from a versioned capability registry. Core state and quota code contain no fixed provider preference or pipeline.
- `enabled=true` requires a bound v2 execution path, compatible lifecycle/privacy/storage policy, preflight, and adoption evidence. Because worker request interception is a follow-on, this slice leaves every external network provider disabled; quota tests use deterministic no-network demo routes.
- A failed or uncertain outbound attempt does not refund a permit.
- Canonical state changes only through revision-checked validated JSON patches that emit a state-revision event; callers cannot directly overwrite arbitrary state.
- Canonical state has complete claim-to-evidence-to-artifact lineage before `PASS`.
- Raw artifact bytes are immutable; state records SHA-256, size, media type, sensitivity, retention, availability, and HTML inclusion.
- HTML is escaped and deterministically derived from `state.json`; it never becomes a second semantic state.
- Runtime code uses no new third-party dependency.
- After every task, compare the implementation against `docs/superpowers/session/2026-07-10-v2-decisions.md` and record any deliberate deviation before continuing.

---

## File Structure

- Create `research_harness/__init__.py`: public version and stable exports.
- Create `research_harness/contracts.py`: posture/tier vocabulary, contract normalization, and validation.
- Create `research_harness/providers.py`: versioned capability-registry loading, hashing, overlays, and route compatibility checks.
- Create `research_harness/provider_registry.json`: enabled baseline providers and disabled benchmark candidates as data, not routing code.
- Create `research_harness/storage.py`: session locking, atomic JSON replacement, append-only event writes, and hashes.
- Create `research_harness/state.py`: canonical state creation, loading, event replay helpers, and compact views.
- Create `research_harness/quota.py`: permit acquisition and physical-attempt lifecycle.
- Create `research_harness/artifacts.py`: immutable raw ingestion, path confinement, sensitivity policy, secret rejection, and purge transitions.
- Create `research_harness/operations.py`: cross-module operations that must validate and rerender, including public purge.
- Create `research_harness/validation.py`: fail-closed schema, quota, lineage, artifact, and tier gates.
- Create `research_harness/rendering.py`: deterministic self-contained HTML renderer.
- Create `scripts/research_state.py`: one Organizer-facing CLI for init, permit, attempt status, validate, render, and view.
- Create `scripts/render_report.py`: narrow rendering entry point for automation.
- Replace `scripts/validate_state.py`: v2 JSON session validator with explicit legacy Markdown fallback during migration.
- Create `tests/`: stdlib `unittest` suite and end-to-end fixtures.
- Create `tests/helpers.py`: valid confirmed contracts and complete positive `PASS` session fixtures shared by gate tests.
- Create `docs/superpowers/session/2026-07-10-v2-decisions.md`: durable summary of this design session and alignment checklist.

### Task 1: Contract Model and Canonical State Creation

**Files:**
- Create: `research_harness/__init__.py`
- Create: `research_harness/contracts.py`
- Create: `research_harness/providers.py`
- Create: `research_harness/provider_registry.json`
- Create: `research_harness/state.py`
- Create: `tests/helpers.py`
- Create: `tests/test_contracts.py`
- Create: `tests/test_state.py`

**Interfaces:**
- Produces: `normalize_contract(data: dict) -> dict`
- Produces: `validate_contract(contract: dict, registry: Optional[dict] = None) -> list[str]`
- Produces: `contract_card_sha256(contract: dict) -> str` over normalized contract data excluding `confirmation`.
- Produces: `load_provider_registry(path: Optional[Path] = None, overlay: Optional[Path] = None) -> dict`
- Produces: `validate_provider_registry(registry: dict) -> list[str]`
- Produces: `provider_registry_sha256(registry: dict) -> str`
- Produces: `provider_records_sha256(records: list[dict]) -> str`
- Produces: `referenced_provider_records(contract: dict, registry: dict) -> list[dict]`
- Produces: `preflight_contract_routes(contract: dict, registry: dict, environ: Mapping[str, str]) -> tuple[list[dict], list[str]]`; records names/presence only, never values.
- Produces: `ProviderRegistryError` for invalid files, overlays, or unbound enablement.
- Produces: `new_state(question: str, contract: dict, now: str, registry: Optional[dict] = None, environ: Optional[Mapping[str, str]] = None) -> dict`
- Produces: `validate_state_document(state: dict) -> list[str]`
- Produces: `state_sha256(state: dict) -> str`

- [ ] **Step 1: Write failing contract tests**

`tests/helpers.py` constructs a contract card first, resolves its referenced records, runs preflight, and then writes confirmation hashes. Deterministic quota cases use committed no-network `demo-probe` and `demo-cascade` routes; no production loader has a fixture-mode bypass.

```python
def test_confirmed_contract_normalizes_all_physical_ceilings(self):
    contract = normalize_contract(self.medium_contract())
    self.assertEqual(contract["resource_envelope"]["physical_ceiling"]["host_retrieval"], 3)
    self.assertEqual(contract["resource_envelope"]["physical_ceiling"]["local"], 1)
    self.assertEqual(contract["resource_envelope"]["physical_ceiling"]["organizer_pass"], 3)
    self.assertEqual(validate_contract(contract), [])

def test_unconfirmed_contract_is_rejected(self):
    contract = self.medium_contract()
    contract["confirmation"] = {"confirmed_by": None, "confirmed_at": None}
    self.assertIn("contract is not user-confirmed", validate_contract(contract))

def test_confirmation_binds_card_and_resolved_registry_hashes(self):
    contract = self.medium_contract()
    contract["resource_envelope"]["physical_ceiling"]["host_retrieval"] += 1
    self.assertIn("confirmed card hash does not match contract", validate_contract(contract, self.registry))

def test_confirmed_contract_rejects_different_registry_overlay(self):
    contract = self.medium_contract()
    overlaid = load_provider_registry(overlay=self.restricted_host_overlay)
    errors = validate_contract(contract, overlaid)
    self.assertIn("confirmed registry hash does not match resolved registry", errors)

def test_preflight_records_presence_without_secret_values(self):
    records, errors = preflight_contract_routes(self.medium_contract(), self.registry, {"TOKEN": "secret-value"})
    self.assertEqual(errors, [])
    self.assertNotIn("secret-value", json.dumps(records))

def test_negative_or_boolean_ceiling_is_rejected(self):
    contract = self.medium_contract()
    contract["resource_envelope"]["physical_ceiling"]["deep"] = True
    self.assertIn("physical ceiling deep must be a non-negative integer", validate_contract(contract))

def test_contract_requires_exactly_one_primary_scout(self):
    contract = self.medium_contract()
    contract["stage_permit_map"].append(dict(contract["stage_permit_map"][0]))
    self.assertIn("exactly one primary_scout mapping with one invocation is required", validate_contract(contract))

def test_host_external_and_local_envelopes_are_distinct(self):
    contract = normalize_contract(self.medium_contract())
    self.assertEqual(contract["resource_envelope"]["host"]["context_class"], "standard")
    self.assertEqual(contract["resource_envelope"]["external"]["metered_ceiling"]["probe"], 0)
    self.assertEqual(contract["resource_envelope"]["external"]["metered_ceiling"]["transport"], 0)
    self.assertEqual(contract["resource_envelope"]["local"]["admitted_output_characters"], 12000)
    self.assertEqual(contract["resource_envelope"]["local"]["max_wall_time_seconds"], 900)

def test_metered_subceiling_cannot_exceed_physical_ceiling(self):
    contract = self.medium_contract()
    contract["resource_envelope"]["external"]["metered_ceiling"]["deep"] = 2
    self.assertIn("metered ceiling deep exceeds physical ceiling", validate_contract(contract))

def test_network_experiment_requires_endpoint_and_privacy_policy(self):
    contract = self.medium_contract()
    contract["resource_envelope"]["physical_ceiling"]["network_experiment"] = 1
    contract["resource_envelope"]["external"]["metered_ceiling"]["network_experiment"] = 1
    self.assertIn("network experiment endpoint policy is required", validate_contract(contract))

def test_route_must_exist_and_support_stage_category(self):
    contract = self.medium_contract()
    contract["stage_permit_map"][0]["route"] = "unknown-search"
    self.assertIn("route unknown-search is not enabled in capability registry", validate_contract(contract, self.registry))
    contract["stage_permit_map"][0]["route"] = "deepseek"
    self.assertIn("route deepseek does not support primary_scout/host_retrieval", validate_contract(contract, self.registry))

def test_physical_count_must_match_route_multiplicity(self):
    contract = self.medium_contract()
    contract["stage_permit_map"][0]["count"] = 2
    self.assertIn("route host-web invocation/count must be 1/1 for host_retrieval", validate_contract(contract, self.registry))

def test_registry_overlay_can_add_disabled_candidate_without_core_code_change(self):
    registry = load_provider_registry(overlay=self.brave_overlay)
    self.assertEqual(validate_provider_registry(registry), [])
    self.assertFalse(next(p for p in registry["providers"] if p["id"] == "brave")["enabled"])
    contract = self.medium_contract()
    contract["scout_route"] = "brave"
    contract["stage_permit_map"][0]["route"] = "brave"
    self.assertIn("route brave is not enabled in capability registry", validate_contract(contract, registry))

def test_registry_overlay_cannot_enable_unbound_candidate(self):
    with self.assertRaises(ProviderRegistryError):
        load_provider_registry(overlay=self.enabled_brave_overlay)

def test_registry_overlay_cannot_change_binding_multiplicity_or_broaden_storage(self):
    for overlay in (self.changed_host_binding, self.changed_host_multiplicity, self.broader_host_storage):
        with self.subTest(overlay=overlay), self.assertRaises(ProviderRegistryError):
            load_provider_registry(overlay=overlay)

def test_enabled_external_route_requires_bound_interceptor_and_adoption_evidence(self):
    registry = copy.deepcopy(self.registry)
    route = next(p for p in registry["providers"] if p["id"] == "sonar")
    route["enabled"] = True
    self.assertIn("enabled external route sonar is not v2-bound", validate_provider_registry(registry))
    route["execution_binding"] = "v2_request_boundary"
    self.assertIn("enabled external route sonar lacks adoption evidence", validate_provider_registry(registry))

def test_enabled_route_rejects_sunset_or_unknown_storage_policy(self):
    registry = copy.deepcopy(self.registry)
    route = next(p for p in registry["providers"] if p["id"] == "host-web")
    route["lifecycle"]["status"] = "sunset"
    route["storage_rights"]["payload_retention"] = "unknown"
    errors = validate_provider_registry(registry)
    self.assertIn("enabled route host-web is sunset", errors)
    self.assertIn("enabled route host-web has unknown storage rights", errors)

def test_state_snapshots_only_used_provider_capabilities_and_registry_hash(self):
    state = new_state("Q", normalize_contract(self.medium_contract()), self.now, self.registry)
    self.assertEqual(state["capabilities"]["registry_sha256"], provider_registry_sha256(self.registry))
    self.assertEqual(
        state["capabilities"]["referenced_records_sha256"],
        provider_records_sha256(state["capabilities"]["providers"]),
    )
    self.assertEqual(
        {p["id"] for p in state["capabilities"]["providers"]},
        {"host-web", "local", "host"},
    )
    self.assertTrue(all("value" not in p for p in state["capabilities"]["preflight"]))

def test_state_document_rejects_missing_sections_and_duplicate_ids(self):
    state = new_state("Q", normalize_contract(self.medium_contract()), self.now, self.registry)
    del state["claims"]
    state["evidence"] = [{"id": "E1"}, {"id": "E1"}]
    errors = validate_state_document(state)
    self.assertIn("state section claims is required", errors)
    self.assertIn("duplicate evidence id E1", errors)
```

- [ ] **Step 2: Run the tests and verify missing-module failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_contracts tests.test_state -v`

Expected: `ModuleNotFoundError: No module named 'research_harness'`.

- [ ] **Step 3: Implement the contract vocabulary and validation**

`normalize_contract()` must copy input data, fill every action and metered category with `0`, preserve the exact `stage_permit_map`, and never infer extra capacity. `contract_card_sha256()` excludes the entire confirmation object to avoid a self-reference. After routes resolve, confirmation stores that card hash plus `provider_registry_sha256()` and the exact `provider_records_sha256()`; `validate_contract()` rejects any mismatch before other execution decisions.

Contract validation also rejects unknown posture/tier, missing confirmation, booleans masquerading as integers, negative ceilings, missing external/host/local envelope fields, metered ceilings above their physical category ceiling, absent or non-positive wall-time bounds, missing endpoint/privacy policy, network experiments without an allowlisted non-production endpoint declaration, more or fewer than one primary scout, a primary scout invocation count other than `1`, registry-disabled or unknown routes, route/stage/category capability mismatches, an invocation/physical-count mismatch against route multiplicity, retention requests forbidden by provider terms, and stage mappings whose per-stage invocation or category request totals exceed their exact envelope.

`providers.py` validates unique IDs and the complete companion-spec registry fields: `id`, `adapter`, `adapter_version`, `enabled`, `roles`, `action_categories`, `stage_capabilities`, `request_multiplicity`, `execution_binding`, `adoption_status`, `adoption_evidence`, `index_family`, `index_provenance`, `upstream_provider`, `retrieval_shape`, `evidence_capabilities`, `controls`, `metering`, `transport`, `privacy`, `storage_rights`, `lifecycle`, `required_env`, `docs_url`, and `docs_verified_at`. `storage_rights` itself requires typed `payload_retention`, `html_allowed`, `allowed_operational_fields`, `verified_at`, and policy source. Registry order never implies routing priority.

Overlays are monotone-restrictive for committed enabled records: they may disable a route, remove roles/stages/categories, tighten privacy or retention, or lower operational ceilings, but cannot change adapter/version, request multiplicity, execution binding, index/upstream identity, grant broader storage rights, or add execution capability. Disabled candidate records may receive metadata corrections but cannot become enabled. Any broader change requires a reviewed committed registry update, adapter fixtures, and re-confirmation; schema-valid replacement alone is insufficient.

The default registry enables only host-native, local, and deterministic demo routes whose execution boundary exists in this slice. `demo-probe` and `demo-cascade` open no socket, can never contribute evidence, and exist to prove `1/1` and `1/4` quota behavior without a production bypass. Existing external CLI routes (`sonar`, `scholar`, `cascade`, `perplexity`, `openai`, `gemini`, and `deepseek`) remain disabled with `execution_binding=legacy_unbound` even when credential doctor says ready. Disabled metadata-only candidates also include `brave`, `openalex`, `crossref`, `europe-pmc`, `exa`, `mojeek`, `jina`, `firecrawl`, plus representative direct source-of-record candidates such as `github`, `pypi`, `osv`, `nvd`, and `ietf`. Disabled records are not executable and exist so contracts, docs, and future adapters share stable IDs and declared unknowns. Every `request_multiplicity` value is a positive non-boolean integer; `cascade.probe=4`, ordinary single-request routes declare `1`, and async polling remains a separate `transport` mapping rather than hidden multiplicity.

An enabled external record is valid only when `execution_binding=v2_request_boundary`, lifecycle is active, storage/privacy fields are complete, and `adoption_status` plus `adoption_evidence` authorize its query classes. Deterministic routes use `execution_binding=no_network_demo` and are structurally barred from evidence contribution. `preflight_contract_routes()` verifies the exact adapter/version binding and required environment-variable presence for referenced routes, plus lifecycle/privacy/storage/adoption compatibility; state snapshots only names, booleans, timestamps, and error codes.

```python
POSTURES = frozenset({"lookup", "synthesis", "scientific", "decision"})
TIERS = frozenset({"low", "medium", "high", "custom"})
ACTION_CATEGORIES = (
    "probe", "deep", "processor", "network_experiment", "transport",
    "host_retrieval", "local", "organizer_pass"
)

def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
```

The normalized resource and stage shape is fixed for this slice:

```json
{
  "scout_route": "host-web",
  "resource_envelope": {
    "physical_ceiling": {
      "probe": 0,
      "deep": 0,
      "processor": 0,
      "network_experiment": 0,
      "transport": 0,
      "host_retrieval": 3,
      "local": 1,
      "organizer_pass": 3
    },
    "external": {
      "metered_ceiling": {
        "probe": 0,
        "deep": 0,
        "processor": 0,
        "network_experiment": 0,
        "transport": 0
      },
      "max_wall_time_seconds": 3600,
      "allowed_endpoint_classes": [],
      "local_file_egress": false,
      "network_experiment_endpoints": [],
      "estimated_spend_usd": {"minimum": 0.0, "maximum": 0.0, "hard_cap": false},
      "raw_storage_bytes": 10485760
    },
    "host": {"context_class": "standard", "admitted_characters": 24000, "estimated_tokens": 6000},
    "local": {"admitted_output_characters": 12000, "max_wall_time_seconds": 900, "network_egress": false}
  },
  "stage_permit_map": [
    {"stage": "primary_scout", "category": "host_retrieval", "route": "host-web", "invocations": 1, "count": 1, "reserved": false},
    {"stage": "local_applicability", "category": "local", "route": "local", "invocations": 1, "count": 1, "reserved": false},
    {"stage": "anti_lock_in", "category": "host_retrieval", "route": "host-web", "invocations": 1, "count": 1, "reserved": true},
    {"stage": "verification", "category": "host_retrieval", "route": "host-web", "invocations": 1, "count": 1, "reserved": true},
    {"stage": "final_inference_review", "category": "organizer_pass", "route": "host", "invocations": 1, "count": 1, "reserved": true}
  ]
}
```

The fixture helper resolves this shape against the registry, runs preflight, computes `card_sha256`, `registry_sha256`, and `referenced_records_sha256`, and only then adds the user confirmation object. Hand-written placeholder hashes never count as confirmation.

- [ ] **Step 4: Implement canonical state creation and stable hashing**

`new_state()` must fail when registry, confirmation binding, contract, or route preflight returns errors, set `session.revision=0`, snapshot the full resolved registry hash, the exact records for every route referenced by the contract, a separately recomputable referenced-records hash, and secret-free preflight records, then create every top-level section from spec section 20.1 including `capabilities` and `retrieval_occurrences`. Historical validation uses the snapshotted records plus their own hash; it does not require the later live registry or current credentials to match, and it does not pretend that a partial snapshot can reproduce the full-registry hash. `validate_state_document()` is the write-boundary structural validator: required sections, confirmation hashes and contract validity against the immutable capability snapshot, ID uniqueness, and references must be internally consistent while a run is still incomplete; posture/tier `PASS` gates remain Task 5. `state_sha256()` must hash compact JSON with sorted keys and UTF-8, excluding no fields.

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
- Consumes: `new_state()`, `validate_state_document()`, and `state_sha256()` from Task 1.
- Produces: `create_session(session_dir: Path, state: dict) -> None`
- Produces: `load_state(session_dir: Path) -> dict`
- Produces: `apply_state_patch(session_dir: Path, operations: list[dict], expected_revision: int, now: str) -> dict`
- Produces: `read_events(session_dir: Path) -> tuple[list[dict], list[str]]`
- Produces: `recover_session(session_dir: Path) -> dict`
- Produces: `session_lock(session_dir: Path, timeout_s: float = 5.0)` context manager.
- Internal domain-operation interfaces: `_load_state_unlocked()`, `_read_events_unlocked()`, `_recover_session_unlocked()`, `_append_event_unlocked()`, and `_apply_artifact_state_patch_unlocked(session_dir: Path, transition_kind: str, operations: list[dict], expected_revision: int, now: str) -> dict`; none is re-exported or exposed by a generic CLI, and every unlocked helper requires the caller to hold the session lock.
- Produces: `RevisionConflict`, `StateValidationError`, and `ProtectedStatePath` exceptions.

- [ ] **Step 1: Write failing storage tests**

```python
def test_create_session_writes_state_and_genesis_event(self):
    create_session(self.session, self.state)
    self.assertEqual(load_state(self.session)["schema_version"], "2.0")
    genesis = read_events(self.session)[0][0]
    self.assertEqual(genesis["event"], "session_created")
    self.assertEqual(genesis["state_sha256"], state_sha256(load_state(self.session)))

def test_state_transitions_assign_monotonic_sequence_and_hash_chain(self):
    first_state = apply_state_patch(
        self.session, [{"op": "replace", "path": "/summary/decision", "value": "one"}], 0, self.now,
    )
    apply_state_patch(
        self.session, [{"op": "replace", "path": "/summary/decision", "value": "two"}],
        first_state["session"]["revision"], self.later,
    )
    revision_events = [e for e in read_events(self.session)[0] if e["event"] == "state_revision"]
    self.assertEqual(revision_events[1]["seq"], revision_events[0]["seq"] + 1)
    self.assertEqual(revision_events[1]["prev_hash"], revision_events[0]["event_hash"])

def test_malformed_trailing_event_is_reported_without_losing_prior_events(self):
    events, errors = read_events(self.session)
    self.assertEqual(len(events), 1)
    self.assertEqual(errors, ["events.jsonl:2 invalid JSON"])

def test_validated_patch_increments_revision_and_records_hashes(self):
    updated = apply_state_patch(
        self.session,
        [{"op": "replace", "path": "/summary/decision", "value": "Use bounded cache"}],
        expected_revision=0,
        now=self.now,
    )
    self.assertEqual(updated["session"]["revision"], 1)
    event = read_events(self.session)[0][-1]
    self.assertEqual(event["event"], "state_revision")
    self.assertEqual(event["new_state_sha256"], state_sha256(updated))

def test_invalid_patch_never_replaces_canonical_state(self):
    before = load_state(self.session)
    with self.assertRaises(StateValidationError):
        apply_state_patch(
            self.session,
            [{"op": "remove", "path": "/contract"}],
            expected_revision=0,
            now=self.now,
        )
    self.assertEqual(load_state(self.session), before)

def test_organizer_patch_cannot_change_contract_capabilities_or_session_identity(self):
    protected = (
        ("/contract/resource_envelope/physical_ceiling/probe", 99),
        ("/capabilities/providers/0/enabled", False),
        ("/session/revision", 99),
        ("/session/id", "forged"),
        ("/artifact_index", []),
    )
    for path, value in protected:
        with self.subTest(path=path), self.assertRaises(ProtectedStatePath):
            apply_state_patch(
                self.session, [{"op": "replace", "path": path, "value": value}], 0, self.now,
            )

def test_artifact_transition_cannot_modify_contract_or_capabilities(self):
    for path in ("/contract", "/capabilities"):
        with self.subTest(path=path), self.assertRaises(ProtectedStatePath):
            with session_lock(self.session):
                _apply_artifact_state_patch_unlocked(
                    self.session, "ingest", [{"op": "replace", "path": path, "value": {}}], 0, self.now,
                )

def test_stale_revision_is_rejected(self):
    with self.assertRaises(RevisionConflict):
        apply_state_patch(self.session, [], expected_revision=9, now=self.now)

def test_recovery_rolls_forward_after_state_replace_before_event_append(self):
    with mock.patch("research_harness.storage._append_event_unlocked", side_effect=OSError("crash")):
        with self.assertRaises(OSError):
            apply_state_patch(
                self.session,
                [{"op": "replace", "path": "/summary/decision", "value": "new"}],
                expected_revision=0,
                now=self.now,
            )
    self.assertTrue((self.session / "transaction.json").exists())
    recovered = recover_session(self.session)
    self.assertEqual(recovered["resolution"], "rolled_forward")
    self.assertEqual(load_state(self.session)["summary"]["decision"], "new")
    self.assertEqual(read_events(self.session)[0][-1]["event"], "state_revision")
    self.assertFalse((self.session / "transaction.json").exists())

def test_recovery_rolls_back_prepared_transaction_before_state_replace(self):
    self.write_prepared_transaction_without_replacing_state()
    recovered = recover_session(self.session)
    self.assertEqual(recovered["resolution"], "rolled_back")
    self.assertEqual(load_state(self.session)["session"]["revision"], 0)

def test_recovery_truncates_only_transaction_owned_partial_revision_tail(self):
    boundary = (self.session / "events.jsonl").stat().st_size
    self.simulate_replaced_state_and_transaction(events_size_before=boundary)
    with (self.session / "events.jsonl").open("ab") as handle:
        handle.write(b'{"event":"state_revision","seq":2')
        handle.flush()
        os.fsync(handle.fileno())
    recovered = recover_session(self.session)
    events, errors = read_events(self.session)
    self.assertEqual(recovered["resolution"], "rolled_forward")
    self.assertEqual(errors, [])
    self.assertEqual(events[-1]["event"], "state_revision")

def test_recovery_never_truncates_unowned_malformed_tail(self):
    with (self.session / "events.jsonl").open("ab") as handle:
        handle.write(b'{"event":"unknown"')
    with self.assertRaises(RecoveryError):
        recover_session(self.session)

def test_recovery_completes_owned_partial_event_without_state_change(self):
    self.simulate_event_only_transaction_with_partial_line({"event": "report_generated", "at": self.now})
    recovered = recover_session(self.session)
    events, errors = read_events(self.session)
    self.assertEqual(recovered["resolution"], "event_rolled_forward")
    self.assertEqual(errors, [])
    self.assertEqual(events[-1]["event"], "report_generated")
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_storage -v`

Expected: import failure for `research_harness.storage`.

- [ ] **Step 3: Implement cross-platform lock files and atomic replacement**

Use `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` for the lock, bounded retry with `time.monotonic()`, and cleanup in `finally`. Write JSON to a sibling temporary file, flush and `os.fsync()`, then `os.replace()`.

The lock file records PID, hostname, and acquisition timestamp. Timeout raises without mutation. A stale lock may be broken only when its owner PID is demonstrably absent on the same host; uncertain ownership fails closed. Public operations acquire exactly one lock and call private `_append_event_unlocked()` / `_atomic_write_json_unlocked()` helpers so nested lock acquisition cannot deadlock. `_append_event_unlocked()` is not re-exported from `research_harness.__init__`; only domain modules already holding the session lock use it for reserved event types.

- [ ] **Step 4: Implement validated revision-checked JSON patches**

Support only `add`, `replace`, and `remove` JSON Pointer operations over exact transition-kind allowlists. The Organizer wrapper may update `framing`, `summary`, `hypotheses`, `planned_checks`, `observations`, `retrieval_occurrences`, `claims`, `evidence`, `sources`, `source_origins`, `branch_manifests`, `evidence_deltas`, `action_metrics`, `inference_joints`, `engineering_handoff`, `open_questions`, and `verification`. The internal artifact wrapper accepts only `ingest`, `purge_pending`, or `purge_tombstone`: ingest may add one immutable artifact record without changing claims/status; purge-pending may move an available artifact to pending, downgrade affected claims, and move status only from `PASS` toward `PARTIAL` or `BLOCKED`; purge-tombstone may only replace that pending record with a purged tombstone and cannot upgrade status or claims. `schema_version`, confirmed `contract`, `capabilities`, and session identity/timestamps/revision are protected for every caller; revision and `updated_at` are modified only by the commit machinery. Contract amendments create a newly confirmed session in this slice.

Apply operations to a deep copy, validate required top-level structure, contract validity against the immutable capability snapshot, ID uniqueness, and referential integrity, then increment `session.revision` and set `session.updated_at`. There is no public arbitrary `save_state()` or arbitrary-event append API.

Use a write-ahead transaction under one session lock: write and fsync `state.next.json`; precompute the complete matching `state_revision` event and write and fsync `transaction.json` containing previous hash, next hash, patch hash, revision, prior event-file byte length, and expected event hash/bytes; atomically replace `state.json`; append the matching event; remove the transaction and staged files; fsync the session directory after every rename or unlink. Canonical state is therefore always either the validated previous or validated next document.

- [ ] **Step 5: Implement deterministic interruption recovery**

Every public mutating operation calls recovery before new work. When `transaction.json` exists, compare current `state.json` with its previous and next hashes. Previous hash means replacement did not occur and is rolled back only when the event file still ends exactly at the recorded boundary. Next hash means replacement occurred: verify the event file through that boundary. If bytes after it are exactly a prefix of this transaction's precomputed event line, truncate only to the recorded boundary, fsync, and append the complete expected event. If the identical complete event already exists, clear the transaction without duplication. Event-only operations use the same boundary/prefix protocol through `event.transaction.json`. Any third state hash, malformed transaction, corruption before the boundary, unowned trailing bytes, or conflicting revision event raises `RecoveryError` and leaves all evidence intact. Recovery without a matching state/event transaction never truncates a malformed event tail.

- [ ] **Step 6: Implement hash-chained event append**

Each domain-generated event receives `seq`, `prev_hash`, and `event_hash`. Hash the event without `event_hash` using sorted compact JSON. Before an event-only append, persist and fsync `event.transaction.json` with the prior byte boundary and complete expected line/hash. Open `events.jsonl` with `O_APPEND`, loop until the full UTF-8 line is written, flush and fsync, then remove the marker and fsync the directory. State transitions reuse their state transaction's event payload rather than nesting markers. The storage module exposes no generic public function that could inject `permit_acquired`, `state_revision`, attempt-status, recovery, or report-generation events.

- [ ] **Step 7: Run Task 2 and prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_contracts tests.test_state tests.test_storage -v`

Expected: all tests pass.

- [ ] **Step 8: Commit Task 2**

```bash
git add research_harness/storage.py tests/test_storage.py
git commit -m "feat: add atomic session storage and event journal"
```

### Task 3: Physical Permit Enforcement

**Files:**
- Create: `research_harness/quota.py`
- Create: `tests/test_quota.py`

**Interfaces:**
- Consumes: `session_lock()` and storage's internal unlocked recover/load/read/event helpers while already holding that lock.
- Produces: `acquire_permits(session_dir: Path, action_id: str, stage: str, category: str, route: str, count: int, fingerprint: str, now: str) -> list[dict]`
- Produces: `record_attempt_status(session_dir: Path, action_id: str, status: str, now: str, details: Optional[dict] = None) -> dict`
- Produces: `permit_usage(session_dir: Path) -> dict[str, int]`
- Produces: `QuotaExceeded`, `ContractNotConfirmed`, and `DuplicateAction` exceptions.

- [ ] **Step 1: Write failing quota tests**

Quota unit fixtures use signed contracts over committed `demo-probe`/`demo-cascade` routes that never open a socket and are ineligible for evidence. The real Sonar/cascade records remain disabled until worker interception is implemented. The unconfirmed defense-in-depth case is built by a test-only unsafe fixture constructor because production `new_state()` already rejects it.

```python
def test_unconfirmed_contract_cannot_acquire(self):
    with self.assertRaises(ContractNotConfirmed):
        acquire_permits(self.session, "A1", "primary_scout", "probe", "demo-probe", 1, "sha256:x", self.now)

def test_atomic_reservation_never_partially_consumes(self):
    with self.assertRaises(QuotaExceeded):
        acquire_permits(self.session, "A1", "primary_scout", "probe", "demo-probe", 4, "sha256:x", self.now)
    self.assertEqual(permit_usage(self.session)["probe"], 0)

def test_one_composite_scout_invocation_reserves_its_full_request_multiplicity(self):
    session = self.make_session_with_primary_scout(
        route="demo-cascade", invocations=1, count=4, probe_ceiling=4,
    )
    permits = acquire_permits(session, "A1", "primary_scout", "probe", "demo-cascade", 4, "sha256:x", self.now)
    self.assertEqual(len(permits), 4)
    self.assertEqual(permit_usage(session)["probe"], 4)

def test_composite_route_cannot_reserve_less_than_one_declared_invocation(self):
    session = self.make_session_with_primary_scout(
        route="demo-cascade", invocations=1, count=4, probe_ceiling=4,
    )
    with self.assertRaises(QuotaExceeded):
        acquire_permits(session, "A1", "primary_scout", "probe", "demo-cascade", 1, "sha256:x", self.now)
    self.assertEqual(permit_usage(session)["probe"], 0)

def test_uncertain_attempt_does_not_refund(self):
    acquire_permits(self.session, "A1", "primary_scout", "probe", "demo-probe", 1, "sha256:x", self.now)
    record_attempt_status(self.session, "A1", "attempted", self.now)
    record_attempt_status(self.session, "A1", "uncertain", self.now)
    self.assertEqual(permit_usage(self.session)["probe"], 1)

def test_second_primary_scout_is_rejected_even_with_category_capacity(self):
    acquire_permits(self.session, "A1", "primary_scout", "probe", "demo-probe", 1, "sha256:a", self.now)
    with self.assertRaises(QuotaExceeded):
        acquire_permits(self.session, "A2", "primary_scout", "probe", "demo-probe", 1, "sha256:b", self.now)

def test_discovery_cannot_consume_reserved_challenge_mapping(self):
    with self.assertRaises(QuotaExceeded):
        acquire_permits(self.session, "A1", "primary_scout", "host_retrieval", "host-web", 1, "sha256:x", self.now)

def test_local_and_organizer_actions_are_recorded_without_external_spend(self):
    acquire_permits(self.session, "L1", "local_applicability", "local", "local", 1, "sha256:l", self.now)
    acquire_permits(self.session, "O1", "final_inference_review", "organizer_pass", "host", 1, "sha256:o", self.now)
    self.assertEqual(permit_usage(self.session)["local"], 1)
    self.assertEqual(permit_usage(self.session)["organizer_pass"], 1)
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_quota -v`

Expected: import failure for `research_harness.quota`.

- [ ] **Step 3: Implement permit reconstruction and atomic acquisition**

Only `permit_acquired` events emitted by this module count toward use. Under one session lock, run recovery, revalidate the immutable confirmation/card/registry/referenced-record hashes, and rerun current secret-free route preflight, then validate category, enabled execution binding, route, positive non-boolean physical count, unique action ID, exact `(stage, category, route)` mapping invocation capacity, registry-declared request multiplicity for one invocation, reserved-stage ownership, mapping request capacity, and remaining category ceiling before calling `_append_event_unlocked()` once with the full atomic request reservation. A failed check appends nothing. The event records logical invocation index and physical count. This mechanically enforces one primary scout, proves deterministic demo `1/1` and `1/4` mappings, and prevents discovery from borrowing challenge or verification capacity. It is not itself an outbound interceptor; production external routes remain disabled until the follow-on supplies that boundary.

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

### Task 4: Immutable Raw Artifact Lifecycle

**Files:**
- Create: `research_harness/artifacts.py`
- Modify: `tests/helpers.py`
- Create: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `load_state()`, `session_lock()`, storage's unlocked recovery/state/artifact-transition helpers, and `state_sha256()`.
- Produces: `ingest_local_artifact(session_dir: Path, source_path: Path, artifact_id: str, media_type: str, sensitivity: str, retention: str, include_in_html: bool, provenance: dict, now: str, redaction_review: Optional[dict] = None) -> dict` for `local_output` or `user_file` only.
- Produces: `ingest_fetched_source(session_dir: Path, source_path: Path, artifact_id: str, media_type: str, source_id: str, fetch_occurrence_id: str, sensitivity: str, retention: str, include_in_html: bool, now: str) -> dict`.
- Produces: `ingest_provider_artifact(session_dir: Path, source_path: Path, artifact_id: str, media_type: str, provider_id: str, attempt_or_occurrence_id: str, sensitivity: str, retention: str, include_in_html: bool, now: str) -> dict`; called only by bound adapter/processor operations, not generic CLI.
- Produces: `purge_raw_artifact(session_dir: Path, artifact_id: str, reason: str, requested_status: str, safe_action_ids: tuple[str, ...], now: str) -> dict`
- Produces: `recover_pending_purges(session_dir: Path, now: str) -> list[dict]`; resumes only already-authorized persisted transitions and never initiates a new purge.
- Produces: `ArtifactPolicyError`, `ArtifactExists`, and `SecretDetected` exceptions.

- [ ] **Step 1: Write failing artifact policy tests**

```python
def test_ingest_confines_bytes_under_raw_and_records_integrity(self):
    artifact = ingest_local_artifact(
        self.session, self.source, "A1", "application/json", "public",
        "session", True, {"origin_kind": "local_output", "action_id": "L1"}, self.now,
    )
    path = self.session / artifact["relative_path"]
    self.assertEqual(path.parent, self.session / "raw")
    self.assertEqual(artifact["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
    self.assertEqual(path.stat().st_mode & 0o777, 0o600)

def test_secret_like_content_is_rejected_without_persisting(self):
    self.source.write_text("OPENAI_API_KEY=secret-value", encoding="utf-8")
    with self.assertRaises(SecretDetected):
        ingest_local_artifact(
            self.session, self.source, "A1", "text/plain", "public", "session", True,
            {"origin_kind": "local_output", "action_id": "L1"}, self.now,
        )
    self.assertFalse((self.session / "raw" / "A1.txt").exists())

def test_local_sensitive_requires_redaction_review_and_never_enters_html(self):
    with self.assertRaises(ArtifactPolicyError):
        ingest_local_artifact(
            self.session, self.source, "A1", "text/plain", "local-sensitive", "session", False,
            {"origin_kind": "user_file", "supplied_by": "user"}, self.now,
        )
    artifact = ingest_local_artifact(
        self.session, self.source, "A1", "text/plain", "local-sensitive", "session", False,
        {"origin_kind": "user_file", "supplied_by": "user"}, self.now,
        {"reviewed_by": "user", "reviewed_at": self.now, "method": "manual"},
    )
    self.assertFalse(artifact["include_in_html"])

def test_artifact_id_traversal_symlink_and_overwrite_are_rejected(self):
    with self.assertRaises(ArtifactPolicyError):
        ingest_local_artifact(
            self.session, self.source, "../escape", "text/plain", "public", "session", True,
            {"origin_kind": "local_output", "action_id": "L1"}, self.now,
        )
    with self.assertRaises(ArtifactPolicyError):
        ingest_local_artifact(
            self.session, self.symlink, "A1", "text/plain", "public", "session", True,
            {"origin_kind": "local_output", "action_id": "L1"}, self.now,
        )

def test_provider_payload_requires_snapshotted_provider_and_attempt(self):
    with self.assertRaises(ArtifactPolicyError):
        ingest_provider_artifact(
            self.session, self.source, "A1", "application/json", "brave", "ATT-unknown",
            "public", "session", False, self.now,
        )

def test_provider_storage_rights_fail_closed_before_persistence(self):
    session = self.make_host_occurrence_session()
    with self.assertRaises(ArtifactPolicyError):
        ingest_provider_artifact(
            session, self.source, "A1", "application/json", "host-web", "ATT1",
            "public", "session", False, self.now,
        )
    self.assertFalse((session / "raw" / "A1.json").exists())

def test_provider_payload_cannot_exceed_html_or_retention_rights(self):
    session = self.make_host_occurrence_session()
    with self.assertRaises(ArtifactPolicyError):
        ingest_provider_artifact(
            session, self.source, "A1", "application/json", "host-web", "ATT1",
            "public", "persistent", True, self.now,
        )

def test_purge_blocks_by_default_before_removing_load_bearing_bytes(self):
    self.make_complete_pass_using("A1", safe_action=False)
    tombstone = purge_raw_artifact(
        self.session, "A1", "retention expired", "BLOCKED", (), self.now,
    )
    state = load_state(self.session)
    self.assertEqual(state["summary"]["status"], "BLOCKED")
    self.assertEqual(tombstone["availability"], "purged")
    self.assertFalse((self.session / tombstone["former_relative_path"]).exists())

def test_purge_allows_partial_only_with_independent_safe_reversible_action(self):
    self.make_complete_pass_using("A1", safe_action=True)
    tombstone = purge_raw_artifact(
        self.session, "A1", "retention expired", "PARTIAL", ("SA1",), self.now,
    )
    state = load_state(self.session)
    self.assertEqual(state["summary"]["status"], "PARTIAL")
    self.assertEqual(tombstone["availability"], "purged")

def test_purge_rejects_partial_when_safe_action_depends_on_affected_claim(self):
    self.make_complete_pass_using("A1", safe_action=True, safe_action_depends_on=("C1",))
    with self.assertRaises(ArtifactPolicyError):
        purge_raw_artifact(self.session, "A1", "retention expired", "PARTIAL", ("SA1",), self.now)

def test_purge_resumes_after_unlink_before_tombstone(self):
    self.make_complete_pass_using("A1", safe_action=False)
    with mock.patch("research_harness.artifacts._finalize_purge_tombstone", side_effect=OSError("crash")):
        with self.assertRaises(OSError):
            purge_raw_artifact(self.session, "A1", "retention expired", "BLOCKED", (), self.now)
    self.assertEqual(load_state(self.session)["artifact_index"][0]["availability"], "purge_pending")
    self.assertFalse((self.session / "raw" / "A1.json").exists())
    tombstone = recover_pending_purges(self.session, self.later)[0]
    self.assertEqual(tombstone["availability"], "purged")
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_artifacts -v`

Expected: import failure for `research_harness.artifacts`.

- [ ] **Step 3: Implement confined immutable ingestion**

All three typed ingestion functions acquire one session lock, run recovery, and share an internal copier only after their origin-specific policy passes. Accept only regular non-symlink files and artifact IDs matching `^[A-Za-z][A-Za-z0-9_-]{0,63}$`. Map an allowlisted media type to a fixed extension; never reuse the source filename. Reject size above remaining `raw_storage_bytes`. Stream-copy to `raw/.<artifact_id>.tmp` created with `O_EXCL` and mode `0o600`, hash while copying, fsync, then atomically rename. Refuse an existing destination or artifact ID even when bytes match. Validator rejects unindexed final files and incomplete ingest state; recovery never guesses their origin.

`ingest_local_artifact()` accepts only explicit `local_output` with a recorded local action ID or `user_file` with supplier identity. `ingest_fetched_source()` requires existing source and fetch-occurrence records. `ingest_provider_artifact()` requires a provider in the immutable capability snapshot and a matching attempt/occurrence event; it rejects disabled/unbound routes and checks typed `storage_rights.payload_retention` and `html_allowed` before writing any bytes. `forbidden`, `ephemeral`, `unknown`, missing, or stale rights never persist a raw payload. Managed provider spool paths are mode `0o700`, carry attempt metadata, and are rejected by local/user ingestion. The generic Organizer CLI does not expose provider/processor ingestion. This prevents accidental workflow relabeling; a malicious local filesystem owner is outside the process-integrity boundary and must not be described as cryptographically prevented.

- [ ] **Step 4: Implement privacy and secret rejection**

Reject `.env` sources, assignment-like names containing `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, or `PRIVATE_KEY`, PEM private-key headers, and configured provider key prefixes before rename. `local-sensitive` requires a complete redaction-review record and forces `include_in_html=false`. `secret` sensitivity is never persistable. Record origin kind, immutable provenance IDs, policy snapshot/hash, scanner version, and redaction review in the artifact index; state explicitly that deterministic scanning is a rejection floor, not proof that arbitrary content is secret-free.

- [ ] **Step 5: Implement fail-closed raw purge transitions**

Accept only requested status `PARTIAL` or `BLOCKED`. `purge_raw_artifact()` acquires one session lock for the full state/bytes/state sequence, runs storage recovery, and uses unlocked artifact transitions so it never nests locks. Before mutation, identify every affected claim. `PARTIAL` requires at least one named `engineering_handoff.safe_actions` entry with `reversible=true` whose `depends_on_claim_ids` excludes every affected claim; otherwise reject before deletion. First patch the artifact to `purge_pending` with target status/reason/former path, affected claims to `unverified`, and the summary to the validated requested status. Only then unlink and fsync the raw directory. Patch the artifact to an `availability=purged` tombstone retaining hash, former path, timestamp, and reason.

The operation is idempotently resumable: the same artifact/reason/target request or `recover_pending_purges()` may continue a matching `purge_pending` record whether bytes are still present or already absent; conflicting parameters fail closed. The pending record itself is the durable proof of prior authorization, so recovery never invents a new deletion target. Interruption after the first patch leaves a non-`PASS` session, and no recovery restores evidence or upgrades status. These low-level functions return `requires_revalidation=true` and never claim the report is current; Task 7's public recovery operation performs mandatory gate validation and rerender. Purge never deletes the tombstone or event history, and artifact code cannot change the confirmed contract or capability snapshot.

- [ ] **Step 6: Run Task 4 and all prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 7: Commit Task 4**

```bash
git add research_harness/artifacts.py tests/helpers.py tests/test_artifacts.py
git commit -m "feat: secure raw artifact lifecycle"
```

### Task 5: Fail-Closed State and Artifact Validation

**Files:**
- Create: `research_harness/validation.py`
- Create: `tests/test_validation.py`
- Modify: `tests/helpers.py`

**Interfaces:**
- Consumes: contracts, storage, quota, and state hashing.
- Produces: `Issue(level: str, code: str, message: str, path: str)` dataclass.
- Produces: `ValidationReport(issues: tuple[Issue, ...], state_sha256: str)` with `ok`, `errors`, `warnings`, and `to_dict()`.
- Produces: `validate_session(session_dir: Path, check_report: bool = True) -> ValidationReport`.
- Internal pure interface: `_validate_loaded_session(session_dir: Path, state: dict, events: list[dict], event_errors: list[str], check_report: bool) -> ValidationReport` for callers that already hold the session lock.

- [ ] **Step 1: Write failing validation tests**

```python
def test_pass_rejects_missing_load_bearing_raw_artifact(self):
    session = make_incomplete_session(self.tempdir, tier="medium", posture="lookup", requested_status="PASS")
    report = validate_session(session)
    self.assertIn("claim.raw_missing", {issue.code for issue in report.errors})

def test_pass_cannot_succeed_vacuously_with_empty_answer_or_claim_set(self):
    session = make_incomplete_session(self.tempdir, tier="medium", posture="lookup", requested_status="PASS")
    apply_state_patch(
        session,
        [
            {"op": "replace", "path": "/summary/decision", "value": ""},
            {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": []},
        ],
        expected_revision=load_state(session)["session"]["revision"], now=self.now,
    )
    report = validate_session(session)
    codes = {issue.code for issue in report.errors}
    self.assertIn("status.pass_answer_missing", codes)
    self.assertIn("status.pass_claim_set_empty", codes)

def test_quota_overrun_in_manual_event_fails_validation(self):
    append_valid_test_event_line(self.session, self.over_limit_event())
    report = validate_session(self.session)
    self.assertIn("quota.exceeded", {issue.code for issue in report.errors})

def test_no_network_demo_route_can_never_contribute_evidence(self):
    session = make_session_with_demo_evidence(self.tempdir)
    report = validate_session(session)
    self.assertIn("evidence.demo_route_forbidden", {issue.code for issue in report.errors})

def test_high_pass_requires_context_separated_verifier(self):
    session = make_incomplete_session(self.tempdir, tier="high", posture="decision", requested_status="PASS")
    report = validate_session(session)
    self.assertIn("tier.high_verifier_missing", {issue.code for issue in report.errors})

def test_complete_medium_lookup_passes_every_gate(self):
    session = make_complete_pass_session(self.tempdir, tier="medium", posture="lookup")
    report = validate_session(session)
    self.assertTrue(report.ok, report.to_dict())

def test_complete_high_decision_with_separated_verifier_passes(self):
    session = make_complete_pass_session(self.tempdir, tier="high", posture="decision")
    report = validate_session(session)
    self.assertTrue(report.ok, report.to_dict())

def test_existing_html_with_old_state_hash_fails_validation(self):
    session = make_complete_pass_session(self.tempdir, tier="medium", posture="lookup")
    (session / "report.html").write_text('<meta data-state-sha256="stale">', encoding="utf-8")
    report = validate_session(session)
    self.assertIn("report.stale", {issue.code for issue in report.errors})

def test_partial_requires_safe_reversible_action_independent_of_gap(self):
    session = make_partial_session(self.tempdir, safe_action=False)
    report = validate_session(session)
    self.assertIn("status.partial_safe_action_missing", {issue.code for issue in report.errors})

def test_partial_with_independent_safe_reversible_action_passes(self):
    session = make_partial_session(self.tempdir, safe_action=True)
    report = validate_session(session)
    self.assertTrue(report.ok, report.to_dict())
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_validation -v`

Expected: import failure for `research_harness.validation`.

- [ ] **Step 3: Implement universal structural gates**

`validate_session()` acquires one session lock, runs `_recover_session_unlocked()`, loads state and events with unlocked helpers, and calls the pure validator so state/revision/event reconciliation is one consistent snapshot. Callers already holding the lock use `_validate_loaded_session()` and never re-enter `validate_session()`.

Validate required top-level sections, immutable confirmation/contract/capability snapshot integrity, current state hash against the revision-zero genesis event or latest state-revision event, event hash chain, exact permit reconciliation by category and stage mapping, claim/evidence/source/artifact IDs, exact excerpt bounds, path confinement, SHA-256 and size of available raw files, absence of unindexed raw files or `purge_pending` artifacts, artifact origin/provenance IDs, provider attempt/occurrence existence, snapshotted storage-rights compatibility, prohibition on any `no_network_demo` route contributing evidence, and the embedded state hash of any existing `report.html`. `append_valid_test_event_line()` exists only under `tests/helpers.py` to construct a correctly chained hostile fixture; production exports no arbitrary-event writer.

- [ ] **Step 4: Implement fail-closed `PASS` gates**

`PASS` is never vacuous: require a non-empty bounded answer/decision, a non-empty `summary.load_bearing_claim_ids`, exact agreement between those IDs and claims marked load-bearing, and satisfaction of the contract's declared evidence floor. For every load-bearing claim, require a recognized passing status, supporting evidence, source origin, available raw artifact, and applicability when required. Scientific/decision Medium and High require anti-lock-in and coverage-audit verification records. High requires a verifier record with `context_separated=true` and `produced_candidate=false`. `PARTIAL` permits explicit load-bearing gaps only when at least one named safe action is `reversible=true` and its `depends_on_claim_ids` excludes all unresolved or purged-evidence claims; otherwise the valid status is `BLOCKED`.

- [ ] **Step 5: Build complete positive gate fixtures**

`make_complete_pass_session()` must create real raw bytes through `ingest_fetched_source()` or an explicitly local artifact path, source/origin/fetch-occurrence records, exact excerpt offsets that match those bytes, load-bearing claims, applicability, reconciled events, and the tier/posture-specific verification records. The High decision fixture includes anti-lock-in, coverage audit, inference-joint review, and a verifier with `context_separated=true` and `produced_candidate=false`. A validator that rejects these fixtures is broken.

- [ ] **Step 6: Run Task 5 and all prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 7: Commit Task 5**

```bash
git add research_harness/validation.py tests/helpers.py tests/test_validation.py
git commit -m "feat: add fail-closed v2 session validation"
```

### Task 6: Deterministic HTML Renderer

**Files:**
- Create: `research_harness/rendering.py`
- Create: `tests/test_rendering.py`

**Interfaces:**
- Consumes: `state_sha256()`, `session_lock()`, storage's unlocked load/recover/read/event helpers, and validation's `_validate_loaded_session()`.
- Produces: `render_html(state: dict, report: ValidationReport) -> str`
- Produces: `RenderedReport(path: Path, validation: ValidationReport, state_sha256: str, report_sha256: str)`.
- Produces: `render_session_result(session_dir: Path) -> RenderedReport`.
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

def test_state_change_makes_existing_report_stale(self):
    render_session(self.session)
    revision = load_state(self.session)["session"]["revision"]
    apply_state_patch(
        self.session,
        [{"op": "replace", "path": "/summary/decision", "value": "changed"}],
        expected_revision=revision,
        now=self.now,
    )
    self.assertIn("report.stale", {issue.code for issue in validate_session(self.session).errors})

def test_render_records_hash_bound_report_event(self):
    path = render_session(self.session)
    event = read_events(self.session)[0][-1]
    self.assertEqual(event["event"], "report_generated")
    self.assertEqual(event["state_sha256"], state_sha256(load_state(self.session)))
    self.assertEqual(event["report_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
```

- [ ] **Step 2: Run the tests and verify import failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_rendering -v`

Expected: import failure for `research_harness.rendering`.

- [ ] **Step 3: Implement escaped, self-contained rendering**

Use only inline CSS, semantic HTML, `<details>` for evidence, text labels in addition to colors, bounded exact excerpts, artifact links only when `include_in_html=true` and sensitivity permits, and no JavaScript or network assets. Use `state.session.updated_at` as the displayed generation time so identical state yields identical bytes.

- [ ] **Step 4: Implement atomic `report.html` replacement**

`render_session_result()` acquires one session lock, runs `_recover_session_unlocked()`, loads state and events once, and calls `_validate_loaded_session(..., check_report=False)` so an old stale report does not poison its replacement and no nested lock occurs. Render that exact snapshot, write and fsync a sibling temporary file, atomically replace `report.html`, fsync the directory, and append a `report_generated` event containing the state and report hashes before releasing the lock. Return the exact validation and hashes used for that report. `render_session()` is a convenience wrapper that returns only `.path`. Rendering may display other validation failures but must label the report `INVALID`; it never changes canonical verdicts. A later state transition makes the report stale by hash.

- [ ] **Step 5: Run Task 6 and all prior tests**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 6**

```bash
git add research_harness/rendering.py tests/test_rendering.py
git commit -m "feat: render deterministic research reports"
```

### Task 7: Organizer CLI and End-to-End Contract Test

**Files:**
- Create: `research_harness/operations.py`
- Create: `scripts/research_state.py`
- Create: `scripts/render_report.py`
- Replace: `scripts/validate_state.py`
- Create: `tests/test_cli.py`
- Create: `examples/v2/medium-contract.json`
- Create: `examples/v2/README.md`

**Interfaces:**
- Consumes all Task 1-6 library interfaces.
- Produces: `purge_artifact(session_dir: Path, artifact_id: str, reason: str, requested_status: str, safe_action_ids: tuple[str, ...], now: str) -> dict`
- Produces: `recover_operation(session_dir: Path, now: str) -> dict` for storage/event and already-pending artifact recovery plus validation/render.
- Produces CLI commands `providers`, `prepare`, `confirm`, `init`, `patch`, `permit`, `status`, `artifact-add`, `artifact-purge`, `recover`, `validate`, `render`, and `view`.
- `providers` and `init` accept an optional `--registry-overlay`; `init` snapshots the resolved registry, never a path-only reference.

- [ ] **Step 1: Write failing CLI end-to-end tests**

```python
def test_init_permit_validate_render_flow(self):
    self.run_cli("init", str(self.session), "--question", "Choose a cache", "--contract", str(self.contract))
    self.run_cli("permit", str(self.session), "--action-id", "A1", "--stage", "primary_scout",
                 "--category", "host_retrieval", "--route", "host-web", "--count", "1",
                 "--fingerprint", "sha256:test")
    validated = self.run_cli("validate", str(self.session), "--json")
    rendered = self.run_cli("render", str(self.session), "--json")
    self.assertTrue(json.loads(validated.stdout)["ok"])
    self.assertTrue(Path(json.loads(rendered.stdout)["report_path"]).exists())

def test_prepare_then_explicit_confirm_binds_exact_card_and_registry(self):
    prepared = self.run_cli("prepare", "--contract", str(self.draft), "--json")
    prepared_payload = json.loads(prepared.stdout)
    self.assertIsNone(prepared_payload["contract"]["confirmation"]["confirmed_at"])
    confirmed = self.run_cli(
        "confirm", "--prepared", str(self.write_json(prepared_payload)),
        "--card-sha256", prepared_payload["binding"]["card_sha256"],
        "--confirmed-at", self.now, "--confirmed-by", "user", "--json",
    )
    contract = json.loads(confirmed.stdout)["contract"]
    self.assertEqual(contract["confirmation"]["registry_sha256"], prepared_payload["binding"]["registry_sha256"])
    self.run_cli("init", str(self.session), "--question", "Q", "--contract", str(self.write_json(contract)))

def test_confirm_rejects_card_hash_not_shown_to_user(self):
    prepared = self.prepare_contract()
    result = self.run_cli(
        "confirm", "--prepared", str(prepared), "--card-sha256", "0" * 64,
        "--confirmed-at", self.now, "--confirmed-by", "user", "--json", check=False,
    )
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("card hash does not match prepared contract", result.stderr)

def test_cli_refuses_unconfirmed_contract(self):
    result = self.run_cli("init", str(self.session), "--question", "Q", "--contract", str(self.unconfirmed), check=False)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("contract is not user-confirmed", result.stderr)

def test_cli_lists_capabilities_without_secret_values(self):
    result = self.run_cli("providers", "--json")
    payload = json.loads(result.stdout)
    self.assertIn("registry_sha256", payload)
    self.assertIn("required_env", payload["providers"][0])
    self.assertNotIn(os.environ.get("OPENAI_API_KEY", "never-match"), result.stdout)

def test_init_snapshots_validated_registry_overlay(self):
    self.run_cli(
        "init", str(self.session), "--question", "Q", "--contract", str(self.contract_for_overlay),
        "--registry-overlay", str(self.overlay),
    )
    state = load_state(self.session)
    self.assertEqual(state["capabilities"]["registry_sha256"], self.expected_overlay_hash)

def test_cli_artifact_add_uses_secure_ingestion(self):
    self.init_session()
    self.acquire_local_action("L1")
    result = self.run_cli(
        "artifact-add", str(self.session), "--source", str(self.source), "--artifact-id", "A1",
        "--media-type", "text/plain", "--origin-kind", "local_output", "--action-id", "L1",
        "--sensitivity", "public", "--retention", "session", "--json",
    )
    artifact = json.loads(result.stdout)["artifact"]
    self.assertTrue((self.session / artifact["relative_path"]).exists())

def test_cli_cannot_relabel_provider_payload_as_generic_artifact(self):
    self.init_session()
    result = self.run_cli(
        "artifact-add", str(self.session), "--source", str(self.source), "--artifact-id", "A1",
        "--media-type", "application/json", "--origin-kind", "provider_payload",
        "--provider-id", "brave", "--attempt-id", "ATT1", "--json", check=False,
    )
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("provider artifacts require a bound adapter operation", result.stderr)

def test_public_purge_revalidates_and_rerenders_partial_session(self):
    session = make_complete_pass_session(self.tempdir, tier="medium", posture="lookup", safe_action=True)
    render_session(session)
    result = purge_artifact(
        session, "A1", "retention expired", "PARTIAL", ("SA1",), self.now,
    )
    state = load_state(session)
    self.assertEqual(state["summary"]["status"], "PARTIAL")
    self.assertTrue(result["validation"]["ok"])
    self.assertIn(state_sha256(state), (session / "report.html").read_text(encoding="utf-8"))

def test_public_purge_defaults_to_blocked_and_renders_current_report(self):
    session = make_complete_pass_session(self.tempdir, tier="medium", posture="lookup", safe_action=False)
    result = purge_artifact(session, "A1", "retention expired", "BLOCKED", (), self.now)
    self.assertEqual(load_state(session)["summary"]["status"], "BLOCKED")
    self.assertTrue(Path(result["report_path"]).exists())

def test_public_recover_completes_pending_purge_validates_and_renders(self):
    session = self.make_crashed_purge_after_unlink()
    result = recover_operation(session, self.later)
    state = load_state(session)
    self.assertEqual(state["artifact_index"][0]["availability"], "purged")
    self.assertEqual(result["validation"]["state_sha256"], state_sha256(state))
    self.assertIn(state_sha256(state), Path(result["report_path"]).read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run tests and verify missing-command failures**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_cli -v`

Expected: CLI path or command failure.

- [ ] **Step 3: Implement thin JSON-first CLIs**

All successful commands print exactly one JSON object on stdout when `--json` is passed; progress and errors go to stderr. `providers` reports registry hash, route capabilities, enabled/binding/adoption state, and only the names/presence of required environment variables; it never reads or prints secret values. `prepare` normalizes a draft, resolves routes, runs preflight, and emits the exact card/registry/referenced-record hashes with confirmation unset. Only after the user responds may the host call `confirm` with the exact displayed card hash; `confirm` copies all three prepared binding hashes and refuses changed bytes. `init` recomputes every hash against the resolved default-plus-overlay registry before snapshotting. Generic `artifact-add` accepts only `local_output`, `user_file`, or a referenced `fetched_source`; provider and processor payloads require typed bound-adapter operations. `validate_state.py` accepts a v2 session directory or `state.json`; when given legacy Markdown, it calls the retained legacy validator path and labels output `schema_version=legacy`.

Implement public purge in `research_harness.operations`: call `purge_raw_artifact()`, then always call `render_session_result()` so validation and the surviving HTML use one locked state/event snapshot and the HTML embeds that state hash. Return the tombstone plus the rendered result's validation, state hash, report hash, and path. A validation error remains visible and never restores `PASS`; rendering an invalid session labels it `INVALID`.

`recover_operation()` first completes storage/event WAL recovery, then calls `recover_pending_purges()` to resume only persisted authorized purge transitions, and finally calls `render_session_result()`. It returns every recovery action plus the exact validation/report hashes. A recovery with no pending work is idempotent. Conflicting purge metadata, unowned malformed event bytes, missing hashes, or unexpected artifact paths fail closed without deletion.

- [ ] **Step 4: Add a real confirmed Medium contract example**

The foundation example is deliberately no-network: one predeclared host-native scout action, one local applicability action, one reserved host anti-lock-in action, one host verification/audit action, zero external providers/processors/transports, a `standard` host context class, and exact admitted-character/raw-storage ceilings. It includes real card/registry/referenced-record hashes generated from the committed registry. External-provider examples arrive only with the worker-boundary follow-on.

- [ ] **Step 5: Run the end-to-end suite and CLI smoke**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest discover -s tests -v`

Run: `tmp=$(mktemp -d); /Users/jechiu/dev/parallax/.venv/bin/python scripts/research_state.py init "$tmp/session" --question "CLI smoke" --contract examples/v2/medium-contract.json --json`

Expected: all tests pass and init prints a JSON object containing `state_path` and `session_id`.

- [ ] **Step 6: Commit Task 7**

```bash
git add scripts research_harness/operations.py tests examples/v2
git commit -m "feat: add v2 organizer runtime CLI"
```

### Task 8: Documentation, Regression Gates, and Slice Review

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `SKILL.md`
- Modify: `AGENTS.md`
- Modify: `HARNESS.md`
- Modify: `requirements.txt`
- Create: `tests/test_docs.py`
- Create: `docs/superpowers/session/2026-07-10-v2-decisions.md`
- Modify: `docs/superpowers/specs/2026-07-10-provider-portfolio-design.md`

**Interfaces:**
- Consumes: stable CLI from Task 7.
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

def test_runtime_docs_name_registry_and_provider_portfolio(self):
    for path in ("README.md", "README.zh-TW.md", "HARNESS.md"):
        text = Path(path).read_text(encoding="utf-8").lower()
        self.assertIn("provider", text)
        self.assertIn("registry", text)

def test_foundation_docs_disclose_external_routes_are_not_yet_v2_bound(self):
    for path in ("README.md", "README.zh-TW.md", "HARNESS.md"):
        text = Path(path).read_text(encoding="utf-8").lower()
        self.assertIn("external", text)
        self.assertIn("disabled", text)
        self.assertIn("worker", text)
```

- [ ] **Step 2: Run the tests and verify they fail on v1 bindings**

Run: `/Users/jechiu/dev/parallax/.venv/bin/python -m unittest tests.test_docs -v`

Expected: failures showing old contract language and missing CLI references.

- [ ] **Step 3: Rewrite runtime-facing documentation to v2**

Keep the main and provider-portfolio design specs as rationale. Make `HARNESS.md` the concise executable protocol: hash-bound contract card and registry snapshot, stage permit map with logical invocations and physical request counts, one scout route, adaptive tuple, anti-lock-in, coverage audit, provenance-gated artifacts, recovery, validation, render, and delivery. Update both host bindings to require user confirmation before `research_state.py init` and require `validate` before `PASS`. Document `providers`, registry overlays, disabled benchmark candidates, and the rule that no new key is requested before adapter fixtures and a named adoption budget exist. State prominently that external network routes remain disabled in this foundation slice until the worker request boundary is integrated; credential doctor readiness is not v2 execution readiness.

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

- [ ] **Step 8: Commit Task 8**

```bash
git add README.md README.zh-TW.md SKILL.md AGENTS.md HARNESS.md requirements.txt tests/test_docs.py docs/superpowers/session/2026-07-10-v2-decisions.md docs/superpowers/specs/2026-07-10-provider-portfolio-design.md
git commit -m "docs: bind hosts to the v2 runtime"
```

## Slice Exit Criteria

- A user-confirmed no-network Medium contract can create a v2 session only when its card, resolved-registry, and referenced-record hashes match.
- The session snapshots the validated registry hash, exact referenced route records, their recomputable hash, and secret-free preflight; disabled, unbound, unavailable, or incompatible routes cannot enter a confirmed contract.
- External, host, and local envelopes remain distinct while one exact stage map accounts for every category.
- The runtime enforces exactly one logical primary-scout invocation, accounts its full registry-declared physical request multiplicity, and rejects discovery use of reserved challenge or verification mappings.
- The runtime rejects every action acquisition before confirmation or beyond its exact `(stage, category, route)` invocation, request, and category ceilings.
- Multi-permit reservations are atomic; failed and uncertain attempts remain consumed.
- Event history is append-only, sequence-numbered, and hash-chained; transaction-owned partial tails recover, while unowned malformed bytes fail closed without truncation.
- Canonical state changes only through validated revision-checked patches with state-revision events.
- Raw ingestion is path-confined, immutable, secret-rejecting, sensitivity-aware, size-bounded, origin/provenance-required, and storage-rights-gated; purge invalidates dependent `PASS` before deletion.
- A crash before or after purge unlink is resumable only from the persisted authorized pending transition, after which the public recovery operation validates and rerenders.
- `PASS` fails closed on missing load-bearing lineage, missing raw evidence, quota mismatch, incomplete scientific checkpoints, or missing High verifier separation.
- Complete Medium lookup and High decision fixtures prove that valid `PASS` is reachable.
- The same canonical state renders byte-identical escaped HTML, and state mutation makes an old report fail stale-hash validation.
- CLI output is machine-readable and host-neutral.
- Production registry external network routes remain disabled until their adapters share the v2 request boundary; deterministic no-network demo routes cannot contribute evidence.
- All deterministic tests pass from a clean worktree.
- No paid provider call is required for this slice.

## Deferred Follow-On Plans

This slice deliberately does not claim the full goal is complete. The next independently testable plans are:

1. Worker enforcement: bind every `deep_research.py` provider submission, retry, polling, resume, and raw-payload path to the v2 request interceptor, add adapter contract fixtures/preflight, and only then enable existing external routes.
2. Organizer protocol: branch manifests, evidence deltas, adaptive routing tuple, anti-lock-in, coverage audit, and verifier packets.
3. Provider portfolio: common retrieval-occurrence/fusion code, source-of-record adapters, Brave and scholarly adapters, Exa-versus-Mojeek evaluation, classified fetch fallbacks, and query-class enablement ledgers.
4. Comparative evaluation: deterministic adversarial fixtures, paired baseline runner, blinded adjudication artifacts, sequential stopping, and tier-specific release ledgers.
5. Distribution and polish: global installer, migration tooling, bilingual docs, examples, terminal UX, CI matrix, release provenance, and GitHub-ready packaging.
