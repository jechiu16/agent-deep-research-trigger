from __future__ import annotations

import copy
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

from research_harness._canon import sha256_hex
from research_harness.contracts import contract_card_sha256, normalize_contract
from research_harness.providers import (
    load_provider_registry,
    provider_records_sha256,
    provider_registry_sha256,
    referenced_provider_records,
)


NOW = "2026-07-10T12:00:00Z"


def draft_medium_contract() -> dict[str, Any]:
    """A confirmed-shape host-led fixture contract (the live, non-legacy shape).

    Named for historical reasons -- callers pass a `tier` label purely to
    pick a fixture variant (see `confirmed_contract`); the contract itself
    always carries the live `tier: "custom"` / `research_workflow:
    host_led_v1` shape the public CLI actually emits. `profile: "light"`
    keeps it below the profile-keyed evidence floor (`_profile_evidence_
    contract` in validation.py), matching the historical "no extra floor"
    baseline this fixture has always represented.
    """

    return {
        "question": "Choose a cache",
        "posture": "lookup",
        "tier": "custom",
        "execution": "external_managed",
        "durability": "canonical_package",
        "research_workflow": "host_led_v1",
        "conclusion_author": "host",
        "provider_reports_role": "discovery_only",
        "scout_route": "host-web",
        "resource_envelope": {
            "cost_budget": {"profile": "light", "deep": 0, "search": 0, "free": "unlimited"},
            "physical_ceiling": {
                "probe": 0,
                "deep": 0,
                "processor": 0,
                "network_experiment": 0,
                "transport": 0,
                "host_retrieval": 3,
                "local": 1,
                "organizer_pass": 1,
            },
            "external": {
                "metered_ceiling": {
                    "probe": 0,
                    "deep": 0,
                    "processor": 0,
                    "network_experiment": 0,
                    "transport": 0,
                },
                "max_wall_time_seconds": 3600,
                "allowed_endpoint_classes": [],
                "local_file_egress": False,
                "network_experiment_endpoints": [],
                "estimated_spend_usd": {
                    "minimum": 0.0,
                    "maximum": 0.0,
                    "hard_cap": False,
                },
                "raw_storage_bytes": 10 * 1024 * 1024,
            },
            "host": {
                "context_class": "standard",
                "admitted_characters": 24000,
                "estimated_tokens": 6000,
            },
            "local": {
                "admitted_output_characters": 12000,
                "max_wall_time_seconds": 900,
                "network_egress": False,
            },
        },
        "stage_permit_map": [
            {
                "stage": "primary_scout",
                "category": "host_retrieval",
                "route": "host-web",
                "invocations": 1,
                "count": 1,
                "reserved": False,
            },
            {
                "stage": "local_applicability",
                "category": "local",
                "route": "local",
                "invocations": 1,
                "count": 1,
                "reserved": False,
            },
            {
                "stage": "anti_lock_in",
                "category": "host_retrieval",
                "route": "host-web",
                "invocations": 1,
                "count": 1,
                "reserved": True,
            },
            {
                "stage": "verification",
                "category": "host_retrieval",
                "route": "host-web",
                "invocations": 1,
                "count": 1,
                "reserved": True,
            },
            {
                "stage": "final_inference_review",
                "category": "organizer_pass",
                "route": "host",
                "invocations": 1,
                "count": 1,
                "reserved": True,
            },
        ],
        "evidence_floor": {
            "minimum_load_bearing_claims": 1,
            "require_raw_artifacts": True,
        },
        "artifact_policy": {
            "default_retention": "session",
            "allow_provider_payloads": False,
        },
        "confirmation": {
            "confirmed_by": None,
            "confirmed_at": None,
            "card_sha256": None,
            "registry_sha256": None,
            "referenced_records_sha256": None,
        },
    }


def confirmed_medium_contract(
    registry: dict[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    del environ  # Current no-network routes do not require environment keys.
    resolved = copy.deepcopy(load_provider_registry() if registry is None else registry)
    contract = normalize_contract(draft_medium_contract())
    records = referenced_provider_records(contract, resolved)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(resolved),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


def draft_host_led_contract() -> dict[str, Any]:
    contract = draft_medium_contract()
    contract.update(
        {
            "tier": "custom",
            "research_workflow": "host_led_v1",
            "conclusion_author": "host",
            "provider_reports_role": "discovery_only",
            "durability": "canonical_package",
        }
    )
    contract["resource_envelope"]["cost_budget"] = {
        "profile": "standard",
        "deep": 1,
        "search": 15,
        "free": "unlimited",
    }
    return contract


def confirmed_host_led_contract(
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = copy.deepcopy(load_provider_registry() if registry is None else registry)
    contract = normalize_contract(draft_host_led_contract())
    records = referenced_provider_records(contract, resolved)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(resolved),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


def confirmed_contract(
    tier: str = "medium",
    posture: str = "lookup",
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a confirmed host-led fixture contract.

    `tier` is kept only for call-site compatibility with existing fixture
    callers; every contract this builds is the live host-led shape (see
    `draft_medium_contract`), so the value no longer selects contract shape.
    """

    del tier
    resolved = copy.deepcopy(load_provider_registry() if registry is None else registry)
    contract = normalize_contract(draft_medium_contract())
    contract["posture"] = posture
    records = referenced_provider_records(contract, resolved)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(resolved),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


def enabled_registry_copy(provider_id: str) -> dict[str, Any]:
    """Deep-copied registry with one candidate route enabled, for tests only.

    Enabling a v2_request_boundary route needs four fields, not one:
    validate_provider_registry also demands baseline/validated adoption_status,
    non-empty adoption_evidence, and an active lifecycle (an enabled route
    cannot be sunset/deprecated -- see the 2026-08-26 openai-deep sunset).
    This sets all four on the copy without mutating the committed registry.
    Thread the SAME copy through both confirmed_demo_contract(registry=...)
    and new_state(registry=...) so the registry hashes agree.
    """

    registry = copy.deepcopy(load_provider_registry())
    for provider in registry["providers"]:
        if provider["id"] == provider_id:
            provider["enabled"] = True
            provider["adoption_status"] = "baseline"
            provider["adoption_evidence"] = [f"test-override-{provider_id}"]
            provider["lifecycle"] = {"status": "active", "sunset_at": "not_applicable"}
    return registry


def confirmed_demo_contract(
    route: str = "demo-probe",
    request_count: int = 1,
    probe_ceiling: int = 2,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = copy.deepcopy(load_provider_registry() if registry is None else registry)
    contract = draft_medium_contract()
    contract["tier"] = "custom"
    contract["execution"] = "external_managed"
    contract["durability"] = "canonical_package"
    contract["scout_route"] = route
    contract["resource_envelope"]["physical_ceiling"].update(
        {"probe": probe_ceiling, "host_retrieval": 0}
    )
    contract["stage_permit_map"] = [
        {
            "stage": "primary_scout",
            "category": "probe",
            "route": route,
            "invocations": 1,
            "count": request_count,
            "reserved": False,
        },
        {
            "stage": "local_applicability",
            "category": "local",
            "route": "local",
            "invocations": 1,
            "count": 1,
            "reserved": False,
        },
        {
            "stage": "final_inference_review",
            "category": "organizer_pass",
            "route": "host",
            "invocations": 1,
            "count": 1,
            "reserved": True,
        },
    ]
    contract = normalize_contract(contract)
    records = referenced_provider_records(contract, resolved)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(resolved),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


def write_overlay(path: Path, providers: list[dict[str, Any]]) -> Path:
    import json

    path.write_text(
        json.dumps({"schema_version": "1.0", "providers": providers}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def append_valid_test_event_line(session_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    """Append a correctly chained hostile fixture without exporting a production bypass."""

    events_path = Path(session_dir) / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    prepared = copy.deepcopy(event)
    prepared.pop("event_hash", None)
    prepared["seq"] = len(events) + 1
    prepared["prev_hash"] = events[-1]["event_hash"] if events else None
    payload = json.dumps(
        prepared, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    prepared["event_hash"] = hashlib.sha256(payload).hexdigest()
    line = json.dumps(
        prepared, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8") + b"\n"
    fd = os.open(events_path, os.O_WRONLY | os.O_APPEND)
    try:
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)
    return prepared


def _complete_action(session: Path, action_id: str) -> None:
    from research_harness.quota import _record_attempt_status_unlocked
    from research_harness.storage import session_lock

    with session_lock(session):
        _record_attempt_status_unlocked(session, action_id, "attempted", NOW)
        _record_attempt_status_unlocked(session, action_id, "accepted", NOW)
        _record_attempt_status_unlocked(session, action_id, "completed", NOW)


def _fixture_terminal_operations(safe_action: bool = False) -> list[dict[str, Any]]:
    return [
        {"op": "replace", "path": "/summary/status", "value": "PASS"},
        {
            "op": "replace",
            "path": "/summary/decision",
            "value": "Use the bounded reversible implementation.",
        },
        {
            "op": "replace",
            "path": "/summary/load_bearing_claim_ids",
            "value": ["C1"],
        },
        {"op": "replace", "path": "/summary/human_status", "value": "completed"},
        {
            "op": "replace",
            "path": "/summary/human_recommendation",
            "value": "Use the bounded recommendation.",
        },
        {
            "op": "replace",
            "path": "/engineering_handoff/constraints",
            "value": ["Re-evaluate if the authoritative source changes."],
        },
        {
            "op": "replace",
            "path": "/engineering_handoff/safe_actions",
            "value": [
                {
                    "id": "SA1" if safe_action else "SA-CANON",
                    "description": "Run a reversible spike",
                    "reversible": True,
                    "depends_on_claim_ids": [],
                }
            ],
        },
        {
            "op": "replace",
            "path": "/engineering_handoff/acceptance_tests",
            "value": ["rerun validation => package remains valid"],
        },
    ]


def _fixture_verifier(
    claim_record: dict[str, Any], final_deep_action_id: str | None = None
) -> dict[str, Any]:
    verifier = {
        "id": "V4",
        "kind": "verifier",
        "completed": True,
        "context_separated": True,
        "produced_candidate": False,
        "verifier_actor": "context-separated-verifier",
        "candidate_actor": "candidate-organizer",
        "packet_claim_ids": ["C1"],
        "packet_sha256": sha256_hex([claim_record]),
        "verdict": "accept",
        "disposition": "accepted the bounded claim packet",
    }
    if final_deep_action_id is not None:
        verifier["final_deep_action_id"] = final_deep_action_id
    return verifier


def make_complete_pass_session(
    root: Path,
    tier: str = "medium",
    posture: str = "lookup",
    *,
    safe_action: bool = False,
) -> Path:
    """Build a complete, fully-valid host-led PASS session.

    `tier` only names the session directory (kept for call-site
    compatibility); every session this builds is the live host-led shape.
    """

    from research_harness.artifacts import ingest_fetched_source
    from research_harness.quota import acquire_permits
    from research_harness.state import CONTRACT_SEMANTICS_V2, new_state
    from research_harness.storage import apply_state_patch, create_session, load_state

    root = Path(root)
    registry = load_provider_registry()
    contract = confirmed_contract(tier, posture, registry)
    session = root / f"complete-{tier}-{posture}-{uuid.uuid4().hex[:8]}"
    state = new_state(contract, NOW, registry, {})
    state["session"]["contract_semantics"] = CONTRACT_SEMANTICS_V2
    create_session(session, state)

    actions = [
        ("A1", "primary_scout", "host_retrieval", "host-web"),
        ("L1", "local_applicability", "local", "local"),
        ("A2", "anti_lock_in", "host_retrieval", "host-web"),
        ("A3", "verification", "host_retrieval", "host-web"),
    ]
    for action_id, stage, category, route in actions:
        acquire_permits(session, action_id, stage, category, route, 1, NOW)
        _complete_action(session, action_id)

    source_origins = [{"id": "O1", "kind": "primary-authority", "independent": True}]
    source_records = [
        {
            "id": "S1",
            "origin_id": "O1",
            "tier": "T1",
            "title": "Authoritative fixture",
            "url": "https://example.test/authoritative",
            "canonical_source_key": "https://example.test/authoritative",
            "upstream_key": "unknown",
            "direct_fetch": True,
        }
    ]
    evidence_records = [
        {
            "id": "E1",
            "artifact_id": "A1",
            "source_id": "S1",
            "origin_id": "O1",
            "source_tier": "T1",
            "excerpt": "Authoritative bounded finding.\n",
            "excerpt_start": 0,
            "excerpt_end": len(b"Authoritative bounded finding.\n"),
            "entailment": "entailed",
            "applicability": "checked",
            "retrieved_at": NOW,
        }
    ]
    state = load_state(session)
    apply_state_patch(
        session,
        [
            {"op": "add", "path": "/source_origins/-", "value": source_origins[0]},
            {"op": "add", "path": "/sources/-", "value": source_records[0]},
            {
                "op": "add",
                "path": "/retrieval_occurrences/-",
                "value": {
                    "id": "R1",
                    "provider_id": "host-web",
                    "source_id": "S1",
                    "action_id": "A1",
                    "retrieved_at": NOW,
                },
            },
        ],
        state["session"]["revision"],
        NOW,
    )
    source_path = root / f"fixture-{uuid.uuid4().hex[:8]}.txt"
    source_path.write_bytes(b"Authoritative bounded finding.\n")
    ingest_fetched_source(
        session, source_path, "A1", "text/plain", "S1", "R1", "public", "session", False, NOW
    )

    claim_evidence = [item["id"] for item in evidence_records]
    claim_origins = [item["origin_id"] for item in source_records]
    claim_record = {
        "id": "C1",
        "text": "The bounded finding applies to this decision.",
        "scope": "fixture environment",
        "qualifiers": [],
        "load_bearing": True,
        "claim_type": "source-of-record",
        "status": "corroborated",
        "supporting_evidence_ids": claim_evidence,
        "counter_evidence_ids": [],
        "source_origin_ids": claim_origins,
        "applicability": "checked",
        "would_change_if": "the authoritative source changes",
        "engineering_implication_ids": [],
    }
    verification: list[dict[str, Any]] = [
        {"id": "V1", "kind": "primary_check", "completed": True, "action_id": "A3"},
        {
            "id": "VR1",
            "kind": "targeted_reverification",
            "completed": True,
            "checked_claim_ids": ["C1"],
            "corrected_claim_ids": [],
            "unverifiable_claim_ids": [],
            "disposition": "The direct source supports the bounded claim.",
        },
    ]

    operations: list[dict[str, Any]] = []
    operations.extend(
        {"op": "add", "path": "/evidence/-", "value": item}
        for item in evidence_records
    )
    operations.append({"op": "add", "path": "/claims/-", "value": claim_record})
    operations.extend(_fixture_terminal_operations(safe_action))
    operations.extend(
        {"op": "add", "path": "/verification/-", "value": record}
        for record in verification
    )
    if posture == "decision":
        operations.append(
            {
                "op": "add",
                "path": "/inference_joints/-",
                "value": {
                    "id": "J1",
                    "claim_ids": ["C1"],
                    "adversarially_reviewed": True,
                    "weakest_joint": True,
                },
            }
        )
    state = load_state(session)
    apply_state_patch(session, operations, state["session"]["revision"], NOW)
    return session


def make_incomplete_session(
    root: Path,
    tier: str = "medium",
    posture: str = "lookup",
    requested_status: str = "PASS",
) -> Path:
    from research_harness.storage import apply_state_patch, load_state

    session = make_complete_pass_session(root, tier, posture)
    artifact = load_state(session)["artifact_index"][0]
    (session / artifact["relative_path"]).unlink()
    state = load_state(session)
    operations: list[dict[str, Any]] = [
        {"op": "replace", "path": "/summary/status", "value": requested_status}
    ]
    apply_state_patch(session, operations, state["session"]["revision"], NOW)
    return session


def make_partial_session(root: Path, safe_action: bool) -> Path:
    from research_harness.storage import apply_state_patch, load_state

    session = make_complete_pass_session(root, "medium", "lookup", safe_action=safe_action)
    state = load_state(session)
    operations = [
        {"op": "replace", "path": "/summary/status", "value": "PARTIAL"},
        {"op": "replace", "path": "/claims/0/status", "value": "unverified"},
    ]
    if not safe_action:
        operations.append(
            {"op": "replace", "path": "/engineering_handoff/safe_actions", "value": []}
        )
    apply_state_patch(session, operations, state["session"]["revision"], NOW)
    return session


def make_session_with_demo_evidence(root: Path) -> Path:
    from research_harness.boundary import execute_probe
    from research_harness.artifacts import ingest_fetched_source
    from research_harness.state import new_state
    from research_harness.storage import apply_state_patch, create_session, load_state

    root = Path(root)
    registry = load_provider_registry()
    contract = confirmed_demo_contract(registry=registry)
    session = root / f"demo-evidence-{uuid.uuid4().hex[:8]}"
    create_session(session, new_state(contract, NOW, registry, {}))
    execute_probe(session, "D1", "primary_scout", "demo-probe", contract["question"], NOW)
    state = load_state(session)
    apply_state_patch(
        session,
        [
            {"op": "add", "path": "/source_origins/-", "value": {"id": "O1"}},
            {
                "op": "add",
                "path": "/sources/-",
                "value": {"id": "S1", "origin_id": "O1", "tier": "T1", "direct_fetch": True},
            },
            {
                "op": "add",
                "path": "/retrieval_occurrences/-",
                "value": {
                    "id": "R1",
                    "provider_id": "demo-probe",
                    "source_id": "S1",
                    "action_id": "D1",
                },
            },
        ],
        state["session"]["revision"],
        NOW,
    )
    source = root / f"demo-{uuid.uuid4().hex[:8]}.txt"
    source.write_text("demo cannot support evidence\n", encoding="utf-8")
    artifact = ingest_fetched_source(
        session, source, "A1", "text/plain", "S1", "R1", "public", "session", False, NOW
    )
    raw = (session / artifact["relative_path"]).read_bytes()
    state = load_state(session)
    apply_state_patch(
        session,
        [
            {
                "op": "add",
                "path": "/evidence/-",
                "value": {
                    "id": "E1",
                    "artifact_id": "A1",
                    "source_id": "S1",
                    "origin_id": "O1",
                    "source_tier": "T1",
                    "excerpt": raw.decode("utf-8"),
                    "excerpt_start": 0,
                    "excerpt_end": len(raw),
                    "entailment": "entailed",
                    "applicability": "checked",
                },
            },
            {
                "op": "add",
                "path": "/claims/-",
                "value": {
                    "id": "C1",
                    "load_bearing": True,
                    "status": "corroborated",
                    "supporting_evidence_ids": ["E1"],
                    "counter_evidence_ids": [],
                    "source_origin_ids": ["O1"],
                    "applicability": "checked",
                },
            },
            {"op": "replace", "path": "/summary/status", "value": "PASS"},
            {"op": "replace", "path": "/summary/decision", "value": "Invalid demo answer"},
            {
                "op": "replace",
                "path": "/summary/load_bearing_claim_ids",
                "value": ["C1"],
            },
        ],
        state["session"]["revision"],
        NOW,
    )
    return session
