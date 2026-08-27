"""Live-vocabulary (profile/posture) quality gates for host-led packages.

`contract.tier` is pinned to "custom" for every host-led draft (see
`contracts.draft_host_led_contract`), so the legacy Medium/High/Ultra branches
of the quality gates in `research_harness/validation.py` can never fire for a
real /deep package no matter what a host does or omits. These tests build
host-led packages the same way the production CLI does (via
`draft_host_led_contract` + `new_state`) and check the profile/posture-keyed
gates added alongside the legacy tier system.

The regression case (`test_heavy_decision_single_upstream_package_fails_...`)
reproduces the real failure documented in this task: a Heavy, decision-posture
package whose load-bearing claims each rest on a single upstream, and which
never recorded an anti-lock-in checkpoint or a coverage audit, validated
`ok: true` because every relevant gate was keyed on a tier value host-led
packages can never carry.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from research_harness.artifacts import ingest_host_capture
from research_harness.contracts import contract_card_sha256, draft_host_led_contract
from research_harness.providers import (
    load_provider_registry,
    provider_records_sha256,
    provider_registry_sha256,
    referenced_provider_records,
)
from research_harness.state import new_state
from research_harness.storage import apply_state_patch, create_session, load_state
from research_harness.validation import validate_session
from tests.helpers import NOW


ENVIRON = {"PERPLEXITY_API_KEY": "test-key"}


def _confirmed_contract(posture: str, profile: str, registry: dict[str, Any]) -> dict[str, Any]:
    """Build a real, confirmed host-led contract the way the public CLI does."""

    contract = draft_host_led_contract(
        "Regression fixture question", posture, profile, registry, ENVIRON, search_routes=[]
    )
    records = referenced_provider_records(contract, registry)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(registry),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


def _capture(session: Path, artifact_id: str, url: str, upstream_key: str, payload: bytes) -> dict[str, Any]:
    return ingest_host_capture(
        session,
        artifact_id,
        url,
        f"Captured source {artifact_id}",
        upstream_key,
        payload,
        "raw_http",
        NOW,
        f"resolve the gap checked by {artifact_id}",
    )


def _source_and_evidence(
    capture: dict[str, Any], evidence_id: str, source_id: str, origin_id: str, payload: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = {
        "id": source_id,
        "origin_id": origin_id,
        "tier": "T1",
        "title": capture["host_capture"]["source_title"],
        "url": capture["host_capture"]["source_url"],
        "canonical_source_key": capture["host_capture"]["canonical_source_key"],
        "upstream_key": capture["host_capture"]["upstream_key"],
        "direct_fetch": True,
    }
    evidence = {
        "id": evidence_id,
        "artifact_id": capture["id"],
        "source_id": source_id,
        "origin_id": origin_id,
        "source_tier": "T1",
        "excerpt": payload.decode("utf-8"),
        "excerpt_start": 0,
        "excerpt_end": len(payload),
        "entailment": "entailed",
        "applicability": "checked",
        "retrieved_at": NOW,
    }
    return source, evidence


def _build_heavy_decision_package(
    root: Path, *, diverse_upstreams: bool, with_reinforcement: bool, label: str
) -> Path:
    """A Heavy, decision-posture host-led package with two load-bearing claims.

    `diverse_upstreams=False` reproduces the real defect: each claim's two
    captures share one upstream (C1 -> noaa.gov twice, C2 -> navy.mil
    twice). `with_reinforcement=False` omits the anti_lock_in and
    coverage_audit verification records a Heavy decision run must now show.
    """

    registry = load_provider_registry()
    contract = _confirmed_contract("decision", "heavy", registry)
    session = root / f"heavy-decision-{label}"
    state = new_state(contract, NOW, registry, ENVIRON)
    create_session(session, state)

    c1_second_upstream = "usno.gov" if diverse_upstreams else "noaa.gov"
    c2_second_upstream = "nps.gov" if diverse_upstreams else "navy.mil"
    hc1 = _capture(session, "HC1", "https://example.test/noaa/station-a", "noaa.gov", b"station A normals")
    hc2 = _capture(session, "HC2", "https://example.test/noaa/station-b", c1_second_upstream, b"station B normals")
    hc3 = _capture(session, "HC3", "https://example.test/navy/rise-a", "navy.mil", b"rise and set A")
    hc4 = _capture(session, "HC4", "https://example.test/navy/rise-b", c2_second_upstream, b"rise and set B")

    s1, e1 = _source_and_evidence(hc1, "E1", "S1", "O1", b"station A normals")
    s2, e2 = _source_and_evidence(hc2, "E2", "S2", "O1", b"station B normals")
    s3, e3 = _source_and_evidence(hc3, "E3", "S3", "O2", b"rise and set A")
    s4, e4 = _source_and_evidence(hc4, "E4", "S4", "O2", b"rise and set B")

    claim1 = {
        "id": "C1",
        "text": "Claim resting on the first pair of captures.",
        "scope": "fixture",
        "qualifiers": [],
        "load_bearing": True,
        "claim_type": "source-of-record",
        "status": "corroborated",
        "supporting_evidence_ids": ["E1", "E2"],
        "counter_evidence_ids": [],
        "source_origin_ids": ["O1"],
        "applicability": "checked",
        "would_change_if": "the cited normals are superseded",
        "engineering_implication_ids": [],
    }
    claim2 = {
        "id": "C2",
        "text": "Claim resting on the second pair of captures.",
        "scope": "fixture",
        "qualifiers": [],
        "load_bearing": True,
        "claim_type": "source-of-record",
        "status": "corroborated",
        "supporting_evidence_ids": ["E3", "E4"],
        "counter_evidence_ids": [],
        "source_origin_ids": ["O2"],
        "applicability": "checked",
        "would_change_if": "the astronomical inputs change",
        "engineering_implication_ids": [],
    }

    operations: list[dict[str, Any]] = [
        {"op": "add", "path": "/source_origins/-", "value": {"id": "O1", "kind": "official-documentation", "independent": True}},
        {"op": "add", "path": "/source_origins/-", "value": {"id": "O2", "kind": "official-documentation", "independent": True}},
        {"op": "add", "path": "/sources/-", "value": s1},
        {"op": "add", "path": "/sources/-", "value": s2},
        {"op": "add", "path": "/sources/-", "value": s3},
        {"op": "add", "path": "/sources/-", "value": s4},
        {"op": "add", "path": "/evidence/-", "value": e1},
        {"op": "add", "path": "/evidence/-", "value": e2},
        {"op": "add", "path": "/evidence/-", "value": e3},
        {"op": "add", "path": "/evidence/-", "value": e4},
        {"op": "add", "path": "/claims/-", "value": claim1},
        {"op": "add", "path": "/claims/-", "value": claim2},
        {"op": "replace", "path": "/summary/status", "value": "PASS"},
        {"op": "replace", "path": "/summary/decision", "value": "Bounded fixture decision."},
        {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": ["C1", "C2"]},
        {"op": "replace", "path": "/summary/human_status", "value": "已完成研究判斷"},
        {"op": "replace", "path": "/summary/human_recommendation", "value": "採用此有界結論"},
        {"op": "replace", "path": "/engineering_handoff/constraints", "value": ["未涵蓋費用與訂位可得性"]},
        {
            "op": "replace",
            "path": "/engineering_handoff/safe_actions",
            "value": [{"id": "SA1", "description": "先做可逆試行", "reversible": True, "depends_on_claim_ids": []}],
        },
        {
            "op": "replace",
            "path": "/engineering_handoff/acceptance_tests",
            "value": ["rerun validation => package remains valid"],
        },
        {
            "op": "add",
            "path": "/inference_joints/-",
            "value": {"id": "J1", "claim_ids": ["C1", "C2"], "adversarially_reviewed": True, "weakest_joint": True},
        },
        {
            "op": "add",
            "path": "/verification/-",
            "value": {
                "id": "VR1",
                "kind": "targeted_reverification",
                "completed": True,
                "checked_claim_ids": ["C1", "C2"],
                "corrected_claim_ids": [],
                "unverifiable_claim_ids": [],
                "disposition": "直接來源支持 C1 與 C2。",
            },
        },
    ]
    if with_reinforcement:
        operations.append(
            {
                "op": "add",
                "path": "/verification/-",
                "value": {
                    "id": "AL1",
                    "kind": "anti_lock_in",
                    "completed": True,
                    "disposition": "D2 提出獨立角度並經 host 覆核，未推翻既有結論。",
                },
            }
        )
        operations.append(
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
        )
    state = load_state(session)
    apply_state_patch(session, operations, state["session"]["revision"], NOW)
    return session


class ProfileGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_heavy_decision_single_upstream_package_without_coverage_audit_fails(self) -> None:
        """Reproduces the real Heavy-run defect and checks the specific fix codes."""

        session = _build_heavy_decision_package(
            self.root, diverse_upstreams=False, with_reinforcement=False, label="defect"
        )
        report = validate_session(session)

        self.assertFalse(report.ok, report.to_dict())
        codes = {issue.code for issue in report.issues}
        self.assertIn("profile.heavy_capture_diversity", codes)
        self.assertIn("tier.anti_lock_in_missing", codes)
        self.assertIn("tier.coverage_audit_missing", codes)
        # The base evidence floor is satisfied (real captures exist); only
        # the cross-upstream corroboration a Heavy run buys is missing.
        self.assertNotIn("profile.direct_evidence_missing", codes)

    def test_heavy_decision_diverse_upstream_package_with_reinforcement_passes(self) -> None:
        """The positive control: same shape, but earns what Heavy pays for."""

        session = _build_heavy_decision_package(
            self.root, diverse_upstreams=True, with_reinforcement=True, label="compliant"
        )
        report = validate_session(session)

        self.assertTrue(report.ok, report.to_dict())
        codes = {issue.code for issue in report.issues}
        self.assertNotIn("profile.heavy_capture_diversity", codes)
        self.assertNotIn("tier.anti_lock_in_missing", codes)
        self.assertNotIn("tier.coverage_audit_missing", codes)

    def test_heavy_diversity_alone_blocks_even_with_reinforcement_present(self) -> None:
        """Isolates the diversity gate: reinforcement present, upstreams are not."""

        session = _build_heavy_decision_package(
            self.root, diverse_upstreams=False, with_reinforcement=True, label="diversity-only"
        )
        report = validate_session(session)

        self.assertFalse(report.ok, report.to_dict())
        codes = {issue.code for issue in report.issues}
        self.assertIn("profile.heavy_capture_diversity", codes)
        self.assertNotIn("tier.anti_lock_in_missing", codes)
        self.assertNotIn("tier.coverage_audit_missing", codes)

    def test_decision_posture_missing_coverage_audit_is_a_warning_at_light_and_standard(self) -> None:
        """'Regardless of profile' is satisfied as visibility, not as a hard block.

        Light and Standard decision packages that skip the coverage audit
        stay `ok: true` -- otherwise the four already-shipped packages under
        examples/field/ (all light/standard, all decision, all predating
        this convention) would stop validating, which this task explicitly
        forbids. The gap is still surfaced as a WARNING.
        """

        for profile in ("light", "standard"):
            with self.subTest(profile=profile):
                registry = load_provider_registry()
                contract = _confirmed_contract("decision", profile, registry)
                session = self.root / f"{profile}-decision-no-coverage-audit"
                state = new_state(contract, NOW, registry, ENVIRON)
                create_session(session, state)

                hc1 = _capture(session, "HC1", "https://example.test/source", "example.gov", b"direct finding")
                s1, e1 = _source_and_evidence(hc1, "E1", "S1", "O1", b"direct finding")
                claim = {
                    "id": "C1",
                    "text": "Single-source fixture claim.",
                    "scope": "fixture",
                    "qualifiers": [],
                    "load_bearing": True,
                    "claim_type": "source-of-record",
                    "status": "corroborated",
                    "supporting_evidence_ids": ["E1"],
                    "counter_evidence_ids": [],
                    "source_origin_ids": ["O1"],
                    "applicability": "checked",
                    "would_change_if": "the cited source changes",
                    "engineering_implication_ids": [],
                }
                operations = [
                    {"op": "add", "path": "/source_origins/-", "value": {"id": "O1", "kind": "official-documentation", "independent": True}},
                    {"op": "add", "path": "/sources/-", "value": s1},
                    {"op": "add", "path": "/evidence/-", "value": e1},
                    {"op": "add", "path": "/claims/-", "value": claim},
                    {"op": "replace", "path": "/summary/status", "value": "PASS"},
                    {"op": "replace", "path": "/summary/decision", "value": "Bounded fixture decision."},
                    {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": ["C1"]},
                    {"op": "replace", "path": "/summary/human_status", "value": "已完成研究判斷"},
                    {"op": "replace", "path": "/summary/human_recommendation", "value": "採用此有界結論"},
                    {"op": "replace", "path": "/engineering_handoff/constraints", "value": ["未涵蓋費用"]},
                    {
                        "op": "replace",
                        "path": "/engineering_handoff/safe_actions",
                        "value": [{"id": "SA1", "description": "先做可逆試行", "reversible": True, "depends_on_claim_ids": []}],
                    },
                    {
                        "op": "replace",
                        "path": "/engineering_handoff/acceptance_tests",
                        "value": ["rerun validation => package remains valid"],
                    },
                    {
                        "op": "add",
                        "path": "/inference_joints/-",
                        "value": {"id": "J1", "claim_ids": ["C1"], "adversarially_reviewed": True, "weakest_joint": True},
                    },
                    {
                        "op": "add",
                        "path": "/verification/-",
                        "value": {
                            "id": "VR1",
                            "kind": "targeted_reverification",
                            "completed": True,
                            "checked_claim_ids": ["C1"],
                            "corrected_claim_ids": [],
                            "unverifiable_claim_ids": [],
                            "disposition": "直接來源支持 C1。",
                        },
                    },
                ]
                state = load_state(session)
                apply_state_patch(session, operations, state["session"]["revision"], NOW)

                report = validate_session(session)
                self.assertTrue(report.ok, report.to_dict())
                self.assertIn(
                    "posture.coverage_audit_recommended",
                    {issue.code for issue in report.warnings},
                )

    def test_draft_evidence_floor_scales_with_profile(self) -> None:
        registry = load_provider_registry()
        for profile, expected in (("light", 1), ("standard", 1), ("heavy", 2)):
            with self.subTest(profile=profile):
                contract = draft_host_led_contract(
                    "Choose a cache", "decision", profile, registry, ENVIRON, search_routes=[]
                )
                self.assertEqual(
                    contract["evidence_floor"]["minimum_load_bearing_claims"], expected
                )


class FieldExamplesStillValidateTests(unittest.TestCase):
    """Guards the explicit instruction not to silently re-tighten shipped packages."""

    def test_all_four_field_examples_still_validate_ok(self) -> None:
        root = Path(__file__).resolve().parents[1] / "examples" / "field"
        sessions = sorted(root.glob("*/session"))
        self.assertEqual(len(sessions), 4, sessions)
        for session in sessions:
            with self.subTest(session=str(session)):
                report = validate_session(session, check_report=False)
                self.assertTrue(report.ok, report.to_dict())


if __name__ == "__main__":
    unittest.main()
