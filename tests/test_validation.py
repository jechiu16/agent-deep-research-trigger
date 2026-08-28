from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_harness.artifacts import ingest_fetched_source, ingest_host_capture
from research_harness.contracts import contract_card_sha256, draft_host_led_contract
from research_harness.providers import (
    load_provider_registry,
    provider_records_sha256,
    provider_registry_sha256,
    referenced_provider_records,
)
from research_harness.rendering import finalize_session_result
from research_harness.state import new_state
from research_harness.storage import apply_state_patch, create_session, load_state
from research_harness.validation import (
    _validate_evidence,
    validate_session,
)
from tests.helpers import (
    NOW,
    append_valid_test_event_line,
    confirmed_medium_contract,
    make_complete_pass_session,
    make_incomplete_session,
    make_partial_session,
    make_session_with_demo_evidence,
)


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_pass_rejects_missing_load_bearing_raw_artifact(self) -> None:
        session = make_incomplete_session(self.root, "medium", "lookup", "PASS")
        report = validate_session(session)
        self.assertIn("claim.raw_missing", {issue.code for issue in report.errors})

    def test_pass_cannot_succeed_vacuously_with_empty_answer_or_claim_set(self) -> None:
        session = make_incomplete_session(self.root, "medium", "lookup", "PASS")
        state = load_state(session)
        apply_state_patch(
            session,
            [
                {"op": "replace", "path": "/summary/decision", "value": ""},
                {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": []},
                {"op": "replace", "path": "/claims/0/load_bearing", "value": False},
            ],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session)
        codes = {issue.code for issue in report.errors}
        self.assertIn("status.pass_answer_missing", codes)
        self.assertIn("status.pass_claim_set_empty", codes)

    def test_quota_overrun_in_manual_event_fails_validation(self) -> None:
        session = make_complete_pass_session(self.root)
        append_valid_test_event_line(
            session,
            {
                "event": "permit_acquired",
                "at": NOW,
                "action_id": "OVER",
                "stage": "primary_scout",
                "category": "host_retrieval",
                "route": "host-web",
                "invocation_index": 2,
                "count": 99,
                "fingerprint": "sha256:hostile",
            },
        )
        report = validate_session(session)
        self.assertIn("quota.exceeded", {issue.code for issue in report.errors})

    def test_attempt_lifecycle_is_clean_on_writer_built_session(self) -> None:
        session = make_complete_pass_session(self.root)
        report = validate_session(session)
        attempt_codes = {
            issue.code for issue in report.errors if issue.code.startswith("attempt.")
        }
        self.assertEqual(attempt_codes, set())

    def test_attempt_status_for_unknown_action_fails_validation(self) -> None:
        session = make_complete_pass_session(self.root)
        append_valid_test_event_line(
            session,
            {
                "event": "attempt_status",
                "at": NOW,
                "action_id": "GHOST",
                "from_status": "acquired",
                "status": "attempted",
            },
        )
        report = validate_session(session)
        self.assertIn("attempt.unknown_action", {issue.code for issue in report.errors})

    def test_attempt_transition_out_of_terminal_state_fails_validation(self) -> None:
        # A1 ends its writer-built lifecycle at "completed"; a forged extra
        # transition out of a terminal state must be flagged even though the
        # event line itself is correctly hash-chained.
        session = make_complete_pass_session(self.root)
        append_valid_test_event_line(
            session,
            {
                "event": "attempt_status",
                "at": NOW,
                "action_id": "A1",
                "from_status": "completed",
                "status": "attempted",
            },
        )
        report = validate_session(session)
        self.assertIn("attempt.transition", {issue.code for issue in report.errors})

    def test_attempt_forged_from_status_fails_validation(self) -> None:
        session = make_complete_pass_session(self.root)
        append_valid_test_event_line(
            session,
            {
                "event": "attempt_status",
                "at": NOW,
                "action_id": "A1",
                "from_status": "acquired",
                "status": "attempted",
            },
        )
        report = validate_session(session)
        self.assertIn("attempt.from_status", {issue.code for issue in report.errors})

    def test_no_network_demo_route_can_never_contribute_evidence(self) -> None:
        session = make_session_with_demo_evidence(self.root)
        report = validate_session(session)
        self.assertIn("evidence.demo_route_forbidden", {issue.code for issue in report.errors})

    def test_discovery_only_provider_payload_cannot_support_evidence(self) -> None:
        state = {
            "evidence": [
                {
                    "id": "E1",
                    "artifact_id": "A1",
                    "source_id": "S1",
                    "origin_id": "O1",
                    "excerpt_start": 0,
                    "excerpt_end": 7,
                    "excerpt": "finding",
                }
            ],
            "sources": [{"id": "S1", "origin_id": "O1"}],
            "source_origins": [{"id": "O1"}],
            "retrieval_occurrences": [],
            "capabilities": {
                "providers": [
                    {
                        "id": "openalex",
                        "evidence_capabilities": {"can_support_claims": False},
                    }
                ]
            },
        }
        artifacts = {
            "A1": {
                "availability": "available",
                "provenance": {
                    "origin_kind": "provider_payload",
                    "provider_id": "openalex",
                },
            }
        }
        issues = []

        _validate_evidence(state, artifacts, {"A1": b"finding"}, issues)

        self.assertIn("evidence.provider_claims_forbidden", {issue.code for issue in issues})

    def test_complete_medium_lookup_passes_every_gate(self) -> None:
        session = make_complete_pass_session(self.root, "medium", "lookup")
        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())
        state = load_state(session)
        self.assertEqual(state["contract"]["execution"], "external_managed")
        self.assertEqual(state["summary"]["status"], "PASS")

    def test_fresh_external_medium_finalizes_as_delivery_incomplete(self) -> None:
        session = self.root / "fresh-external-medium"
        create_session(session, new_state(confirmed_medium_contract(), NOW, None, {}))

        report = validate_session(session)
        self.assertFalse(report.tier_contract_met, report.to_dict())
        self.assertEqual(report.human_status, "交付不完整")
        self.assertIn("tier.terminal_status_missing", {issue.code for issue in report.warnings})

        rendered = finalize_session_result(session, NOW)
        state = load_state(session)
        self.assertEqual(state["summary"]["status"], "BLOCKED")
        self.assertEqual(state["summary"]["human_status"], "交付不完整")
        self.assertFalse(rendered.validation.tier_contract_met)
        self.assertIn(
            "BLOCKED / DELIVERY_INCOMPLETE", rendered.path.read_text(encoding="utf-8")
        )

    def test_terminal_blocked_external_package_without_claims_is_evidence_shortfall(self) -> None:
        session = self.root / "blocked-external-medium"
        create_session(session, new_state(confirmed_medium_contract(), NOW, None, {}))
        state = load_state(session)
        apply_state_patch(
            session,
            [{"op": "replace", "path": "/summary/status", "value": "BLOCKED"}],
            state["session"]["revision"],
            NOW,
        )

        report = validate_session(session)
        self.assertFalse(report.tier_contract_met, report.to_dict())
        self.assertEqual(report.human_status, "證據不足")
        self.assertIn(
            "tier.load_bearing_claims_missing", {issue.code for issue in report.warnings}
        )

    def test_complete_decision_posture_passes_without_reinforcement(self) -> None:
        # "high"/"decision" here: tier is cosmetic (see confirmed_contract),
        # and decision posture at the light profile this fixture carries has
        # no anti-lock-in or coverage-audit floor of its own -- that floor
        # only binds at the heavy profile (see test_profile_gates.py).
        session = make_complete_pass_session(self.root, "high", "decision")
        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())

    def test_synthesis_heavy_pass_requires_coverage_audit(self) -> None:
        # synthesis's posture promise IS a coverage/omissions declaration, so
        # it shares the heavy coverage-audit gate with scientific/decision
        # even though it has no anti-lock-in requirement of its own. This
        # only binds at the heavy profile, so build a real heavy host-led
        # contract via draft_host_led_contract rather than
        # make_complete_pass_session (which is pinned to a light profile).
        registry = load_provider_registry()
        environ = {"PERPLEXITY_API_KEY": "test-key"}
        contract = draft_host_led_contract(
            "Choose a cache", "synthesis", "heavy", registry, environ, search_routes=[]
        )
        records = referenced_provider_records(contract, registry)
        contract["confirmation"] = {
            "confirmed_by": "user",
            "confirmed_at": NOW,
            "card_sha256": contract_card_sha256(contract),
            "registry_sha256": provider_registry_sha256(registry),
            "referenced_records_sha256": provider_records_sha256(records),
        }
        session = self.root / "heavy-synthesis"
        create_session(session, new_state(contract, NOW, registry, environ))

        # Heavy's evidence floor requires two load-bearing claims (see
        # draft_host_led_contract's evidence_floor); each needs two captures
        # from distinct upstreams to satisfy profile.heavy_capture_diversity.
        hc1 = ingest_host_capture(
            session, "HC1", "https://example.test/a", "Source A", "noaa.gov",
            b"finding A", "raw_http", NOW, "resolve gap A",
        )
        hc2 = ingest_host_capture(
            session, "HC2", "https://example.test/b", "Source B", "usno.gov",
            b"finding B", "raw_http", NOW, "resolve gap B",
        )
        hc3 = ingest_host_capture(
            session, "HC3", "https://example.test/c", "Source C", "navy.mil",
            b"finding C", "raw_http", NOW, "resolve gap C",
        )
        hc4 = ingest_host_capture(
            session, "HC4", "https://example.test/d", "Source D", "nps.gov",
            b"finding D", "raw_http", NOW, "resolve gap D",
        )
        operations = [
            {"op": "add", "path": "/source_origins/-", "value": {"id": "O1", "kind": "official-documentation", "independent": True}},
            {"op": "add", "path": "/source_origins/-", "value": {"id": "O2", "kind": "official-documentation", "independent": True}},
            {
                "op": "add", "path": "/sources/-",
                "value": {
                    "id": "S1", "origin_id": "O1", "tier": "T1",
                    "title": hc1["host_capture"]["source_title"], "url": hc1["host_capture"]["source_url"],
                    "canonical_source_key": hc1["host_capture"]["canonical_source_key"],
                    "upstream_key": hc1["host_capture"]["upstream_key"], "direct_fetch": True,
                },
            },
            {
                "op": "add", "path": "/sources/-",
                "value": {
                    "id": "S2", "origin_id": "O1", "tier": "T1",
                    "title": hc2["host_capture"]["source_title"], "url": hc2["host_capture"]["source_url"],
                    "canonical_source_key": hc2["host_capture"]["canonical_source_key"],
                    "upstream_key": hc2["host_capture"]["upstream_key"], "direct_fetch": True,
                },
            },
            {
                "op": "add", "path": "/sources/-",
                "value": {
                    "id": "S3", "origin_id": "O2", "tier": "T1",
                    "title": hc3["host_capture"]["source_title"], "url": hc3["host_capture"]["source_url"],
                    "canonical_source_key": hc3["host_capture"]["canonical_source_key"],
                    "upstream_key": hc3["host_capture"]["upstream_key"], "direct_fetch": True,
                },
            },
            {
                "op": "add", "path": "/sources/-",
                "value": {
                    "id": "S4", "origin_id": "O2", "tier": "T1",
                    "title": hc4["host_capture"]["source_title"], "url": hc4["host_capture"]["source_url"],
                    "canonical_source_key": hc4["host_capture"]["canonical_source_key"],
                    "upstream_key": hc4["host_capture"]["upstream_key"], "direct_fetch": True,
                },
            },
            {
                "op": "add", "path": "/evidence/-",
                "value": {
                    "id": "E1", "artifact_id": "HC1", "source_id": "S1", "origin_id": "O1", "source_tier": "T1",
                    "excerpt": "finding A", "excerpt_start": 0, "excerpt_end": len(b"finding A"),
                    "entailment": "entailed", "applicability": "checked", "retrieved_at": NOW,
                },
            },
            {
                "op": "add", "path": "/evidence/-",
                "value": {
                    "id": "E2", "artifact_id": "HC2", "source_id": "S2", "origin_id": "O1", "source_tier": "T1",
                    "excerpt": "finding B", "excerpt_start": 0, "excerpt_end": len(b"finding B"),
                    "entailment": "entailed", "applicability": "checked", "retrieved_at": NOW,
                },
            },
            {
                "op": "add", "path": "/evidence/-",
                "value": {
                    "id": "E3", "artifact_id": "HC3", "source_id": "S3", "origin_id": "O2", "source_tier": "T1",
                    "excerpt": "finding C", "excerpt_start": 0, "excerpt_end": len(b"finding C"),
                    "entailment": "entailed", "applicability": "checked", "retrieved_at": NOW,
                },
            },
            {
                "op": "add", "path": "/evidence/-",
                "value": {
                    "id": "E4", "artifact_id": "HC4", "source_id": "S4", "origin_id": "O2", "source_tier": "T1",
                    "excerpt": "finding D", "excerpt_start": 0, "excerpt_end": len(b"finding D"),
                    "entailment": "entailed", "applicability": "checked", "retrieved_at": NOW,
                },
            },
            {
                "op": "add", "path": "/claims/-",
                "value": {
                    "id": "C1", "text": "Claim resting on the first pair of diverse upstream captures.", "scope": "fixture",
                    "qualifiers": [], "load_bearing": True, "claim_type": "source-of-record", "status": "corroborated",
                    "supporting_evidence_ids": ["E1", "E2"], "counter_evidence_ids": [], "source_origin_ids": ["O1"],
                    "applicability": "checked", "would_change_if": "the cited normals are superseded",
                    "engineering_implication_ids": [],
                },
            },
            {
                "op": "add", "path": "/claims/-",
                "value": {
                    "id": "C2", "text": "Claim resting on the second pair of diverse upstream captures.", "scope": "fixture",
                    "qualifiers": [], "load_bearing": True, "claim_type": "source-of-record", "status": "corroborated",
                    "supporting_evidence_ids": ["E3", "E4"], "counter_evidence_ids": [], "source_origin_ids": ["O2"],
                    "applicability": "checked", "would_change_if": "the cited normals are superseded",
                    "engineering_implication_ids": [],
                },
            },
            {"op": "replace", "path": "/summary/status", "value": "PASS"},
            {"op": "replace", "path": "/summary/decision", "value": "Bounded fixture decision."},
            {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": ["C1", "C2"]},
            {"op": "replace", "path": "/summary/human_status", "value": "已完成研究判斷"},
            {"op": "replace", "path": "/summary/human_recommendation", "value": "採用此有界結論"},
            {"op": "replace", "path": "/engineering_handoff/constraints", "value": ["未涵蓋費用"]},
            {
                "op": "replace", "path": "/engineering_handoff/safe_actions",
                "value": [{"id": "SA1", "description": "先做可逆試行", "reversible": True, "depends_on_claim_ids": []}],
            },
            {
                "op": "replace", "path": "/engineering_handoff/acceptance_tests",
                "value": ["rerun validation => package remains valid"],
            },
            {
                "op": "add", "path": "/verification/-",
                "value": {
                    "id": "VR1", "kind": "targeted_reverification", "completed": True,
                    "checked_claim_ids": ["C1", "C2"], "corrected_claim_ids": [], "unverifiable_claim_ids": [],
                    "disposition": "直接來源支持 C1 與 C2。",
                },
            },
        ]
        state = load_state(session)
        apply_state_patch(session, operations, state["session"]["revision"], NOW)

        report = validate_session(session)
        codes = {issue.code for issue in report.errors}
        self.assertIn("tier.coverage_audit_missing", codes)
        self.assertNotIn("tier.anti_lock_in_missing", codes)

        state = load_state(session)
        apply_state_patch(
            session,
            [
                {
                    "op": "add",
                    "path": "/verification/-",
                    "value": {
                        "id": "CA1",
                        "kind": "coverage_audit",
                        "completed": True,
                        "candidate_omissions_dispositioned": True,
                        "disposition": "本次涵蓋問題全部範圍，無未處理缺口。",
                    },
                }
            ],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session)
        self.assertNotIn("tier.coverage_audit_missing", {issue.code for issue in report.errors})
        self.assertTrue(report.ok, report.to_dict())

    def test_empirical_load_bearing_claim_needs_two_independent_origins(self) -> None:
        session = make_complete_pass_session(self.root, "high", "decision")
        state = load_state(session)
        apply_state_patch(
            session,
            [{"op": "replace", "path": "/claims/0/claim_type", "value": "empirical"}],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session)
        self.assertIn("claim.origin_independence", {issue.code for issue in report.errors})

    def test_empirical_claim_with_two_independent_raw_origins_passes(self) -> None:
        session = make_complete_pass_session(self.root, "high", "decision")
        state = load_state(session)
        apply_state_patch(
            session,
            [
                {
                    "op": "add",
                    "path": "/source_origins/-",
                    "value": {"id": "O2", "kind": "independent-study", "independent": True},
                },
                {
                    "op": "add",
                    "path": "/sources/-",
                    "value": {
                        "id": "S2",
                        "origin_id": "O2",
                        "tier": "T1",
                        "title": "Independent fixture",
                        "direct_fetch": True,
                    },
                },
                {
                    "op": "add",
                    "path": "/retrieval_occurrences/-",
                    "value": {
                        "id": "R2",
                        "provider_id": "host-web",
                        "source_id": "S2",
                        "action_id": "A2",
                    },
                },
            ],
            state["session"]["revision"],
            NOW,
        )
        payload = b"Independent empirical finding.\n"
        source = self.root / "independent.txt"
        source.write_bytes(payload)
        ingest_fetched_source(
            session,
            source,
            "A2",
            "text/plain",
            "S2",
            "R2",
            "public",
            "session",
            False,
            NOW,
        )
        state = load_state(session)
        claim = dict(state["claims"][0])
        claim.update(
            {
                "claim_type": "empirical",
                "supporting_evidence_ids": ["E1", "E2"],
                "source_origin_ids": ["O1", "O2"],
            }
        )
        apply_state_patch(
            session,
            [
                {
                    "op": "add",
                    "path": "/evidence/-",
                    "value": {
                        "id": "E2",
                        "artifact_id": "A2",
                        "source_id": "S2",
                        "origin_id": "O2",
                        "source_tier": "T1",
                        "excerpt": payload.decode("utf-8"),
                        "excerpt_start": 0,
                        "excerpt_end": len(payload),
                        "entailment": "entailed",
                        "applicability": "checked",
                        "retrieved_at": NOW,
                    },
                },
                {
                    "op": "replace",
                    "path": "/claims/0",
                    "value": claim,
                },
            ],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())

    def test_existing_html_with_old_state_hash_fails_validation(self) -> None:
        session = make_complete_pass_session(self.root, "medium", "lookup")
        (session / "report.html").write_text(
            '<meta data-state-sha256="stale">', encoding="utf-8"
        )
        report = validate_session(session)
        self.assertIn("report.stale", {issue.code for issue in report.errors})

    def test_partial_requires_safe_reversible_action_independent_of_gap(self) -> None:
        session = make_partial_session(self.root, safe_action=False)
        report = validate_session(session)
        self.assertIn("status.partial_safe_action_missing", {issue.code for issue in report.errors})

    def test_partial_with_independent_safe_reversible_action_passes(self) -> None:
        session = make_partial_session(self.root, safe_action=True)
        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())

    def test_mutated_artifact_and_invented_excerpt_fail_integrity(self) -> None:
        session = make_complete_pass_session(self.root)
        state = load_state(session)
        path = session / state["artifact_index"][0]["relative_path"]
        payload = bytearray(path.read_bytes())
        payload[0] = ord("X")
        path.write_bytes(payload)
        report = validate_session(session)
        codes = {issue.code for issue in report.errors}
        self.assertIn("artifact.integrity", codes)
        self.assertIn("evidence.excerpt_mismatch", codes)

    def test_unindexed_raw_file_fails_validation(self) -> None:
        session = make_complete_pass_session(self.root)
        (session / "raw" / "unindexed.txt").write_text("orphan", encoding="utf-8")
        report = validate_session(session)
        self.assertIn("artifact.unindexed", {issue.code for issue in report.errors})


if __name__ == "__main__":
    unittest.main()
