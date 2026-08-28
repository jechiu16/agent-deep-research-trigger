from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from research_harness.artifacts import ArtifactPolicyError, ingest_host_capture
from research_harness.contracts import contract_card_sha256
from research_harness.rendering import finalize_session_result, render_session_result
from research_harness.state import new_state
from research_harness.storage import apply_state_patch, create_session, load_state, read_events
from research_harness.validation import validate_session
from tests.helpers import NOW, confirmed_contract, confirmed_host_led_contract


class HostTierContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.session = self._make_session()

    def test_host_led_delivery_requires_dispositioned_targeted_reverification(self) -> None:
        session = self.root / "host-led-reverification"
        create_session(session, new_state(confirmed_host_led_contract(), NOW, None, {}))
        state = load_state(session)
        apply_state_patch(
            session,
            [
                {"op": "replace", "path": "/summary/status", "value": "BLOCKED"},
                {"op": "replace", "path": "/summary/human_status", "value": "證據不足"},
            ],
            state["session"]["revision"],
            NOW,
        )
        missing = validate_session(session)
        self.assertIn(
            "tier.targeted_reverification_missing",
            {issue.code for issue in missing.warnings},
        )

        state = load_state(session)
        apply_state_patch(
            session,
            [
                {
                    "op": "add",
                    "path": "/verification/-",
                    "value": {
                        "id": "VR-invalid",
                        "kind": "targeted_reverification",
                        "completed": True,
                        "checked_claim_ids": [],
                        "corrected_claim_ids": ["C-not-checked"],
                        "unverifiable_claim_ids": [],
                        "disposition": "References a claim outside the checked packet.",
                    },
                }
            ],
            state["session"]["revision"],
            NOW,
        )
        invalid = validate_session(session)
        self.assertIn(
            "tier.targeted_reverification_missing",
            {issue.code for issue in invalid.warnings},
        )

        state = load_state(session)
        apply_state_patch(
            session,
            [
                {
                    "op": "add",
                    "path": "/verification/-",
                    "value": {
                        "id": "VR-valid",
                        "kind": "targeted_reverification",
                        "completed": True,
                        "checked_claim_ids": [],
                        "corrected_claim_ids": [],
                        "unverifiable_claim_ids": [],
                        "disposition": "No load-bearing claims survived the evidence review.",
                    },
                }
            ],
            state["session"]["revision"],
            NOW,
        )
        complete = validate_session(session)
        self.assertNotIn(
            "tier.targeted_reverification_missing",
            {issue.code for issue in complete.issues},
        )

    def _capture(
        self,
        artifact_id: str,
        source_url: str,
        payload: bytes,
        *,
        source_title: str = "Captured source",
        upstream_key: str = "upstream-1",
        purpose: str = "resolve the named gap",
        fidelity: str = "raw_http",
    ) -> dict:
        return ingest_host_capture(
            self.session,
            artifact_id,
            source_url,
            source_title,
            upstream_key,
            payload,
            fidelity,
            NOW,
            purpose,
        )

    def _link_claim(self, evidence: list[dict]) -> None:
        state = load_state(self.session)
        operations: list[dict] = []
        for item in evidence:
            index = item["id"][1:]
            operations.extend(
                [
                    {
                        "op": "add",
                        "path": "/source_origins/-",
                        "value": {"id": f"O{index}", "kind": "host"},
                    },
                    {
                        "op": "add",
                        "path": "/sources/-",
                        "value": {
                            "id": f"S{index}",
                            "origin_id": f"O{index}",
                            "url": item["source_url"],
                            "title": item.get("source_title", "Captured source"),
                            "canonical_source_key": item["canonical_source_key"],
                            "upstream_key": item.get("upstream_key", "upstream-1"),
                            "direct_fetch": True,
                        },
                    },
                ]
            )
            operations.append(
                {
                    "op": "add",
                    "path": "/evidence/-",
                    "value": {
                        "id": item["id"],
                        "artifact_id": item["artifact_id"],
                        "source_id": f"S{index}",
                        "origin_id": f"O{index}",
                        "excerpt_start": 0,
                        "excerpt_end": len(item["payload"]),
                        "excerpt": item["payload"].decode("utf-8"),
                    },
                }
            )
        claim_record = {
            "id": "C1",
            "text": "Captured finding applies to this bounded decision.",
            "would_change_if": "the captured source changes",
            "load_bearing": True,
            "supporting_evidence_ids": [item["id"] for item in evidence],
        }
        operations.extend(
            [
                {
                    "op": "add",
                    "path": "/claims/-",
                    "value": claim_record,
                },
                {
                    "op": "replace",
                    "path": "/summary/load_bearing_claim_ids",
                    "value": ["C1"],
                },
                {"op": "replace", "path": "/summary/status", "value": "PARTIAL"},
                {"op": "replace", "path": "/summary/human_status", "value": "已完成研究判斷"},
                {"op": "replace", "path": "/summary/human_recommendation", "value": "建議採用"},
                {"op": "replace", "path": "/summary/decision", "value": "採用此有界結論"},
                {
                    "op": "replace",
                    "path": "/engineering_handoff/constraints",
                    "value": ["若來源改變則重新評估"],
                },
                {
                    "op": "replace",
                    "path": "/engineering_handoff/safe_actions",
                    "value": [{"id": "A1", "description": "保留可逆試行", "reversible": True, "depends_on_claim_ids": []}],
                },
                {
                    "op": "replace",
                    "path": "/engineering_handoff/acceptance_tests",
                    "value": ["rerun validation => tier contract remains met"],
                },
                # Host-led delivery requires a completed, dispositioned
                # targeted-reverification record (see
                # _canonical_delivery_tier_contract in validation.py); every
                # session built off confirmed_contract() now carries the
                # live host-led workflow markers, so this is required for
                # tier_contract_met regardless of the (now cosmetic) tier
                # label passed to _make_session.
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
        )
        apply_state_patch(self.session, operations, state["session"]["revision"], NOW)

    def test_host_capture_preserves_bytes_lineage_and_creates_no_transactions(self) -> None:
        payload = b"raw host bytes\x00\xff"
        artifact = self._capture(
            "HC1",
            "https://example.test/source",
            payload,
            upstream_key="HTTPS://Example.COM:443/upstream#fragment",
            fidelity="host_rendered",
        )

        self.assertEqual(artifact["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual((self.session / artifact["relative_path"]).read_bytes(), payload)
        self.assertEqual(artifact["provenance"]["origin_kind"], "host_capture")
        self.assertEqual(artifact["host_capture"]["canonical_source_key"], "https://example.test/source")
        self.assertEqual(artifact["host_capture"]["source_url"], "https://example.test/source")
        self.assertEqual(artifact["host_capture"]["source_title"], "Captured source")
        self.assertEqual(artifact["host_capture"]["upstream_key"], "https://example.com/upstream")
        self.assertEqual(artifact["host_capture"]["fidelity"], "host_rendered")
        self.assertEqual(artifact["host_capture"]["captured_at"], NOW)
        self.assertEqual(artifact["host_capture"]["marginal_purpose"], "resolve the named gap")
        events, errors = read_events(self.session)
        self.assertEqual(errors, [])
        self.assertEqual([event["event"] for event in events], ["session_created", "state_revision"])
        self.assertTrue(validate_session(self.session).integrity_ok)

    def test_host_capture_rejects_non_host_led_external_managed_contract(self) -> None:
        # execution=="external_managed" is necessary but not sufficient:
        # ingest_host_capture also requires the other host-led workflow
        # markers (research_workflow, conclusion_author,
        # provider_reports_role). confirmed_contract() carries all of them
        # by default, so strip just the workflow markers to isolate this.
        contract = confirmed_contract("medium")
        contract.pop("research_workflow", None)
        contract.pop("conclusion_author", None)
        contract.pop("provider_reports_role", None)
        contract["confirmation"]["card_sha256"] = contract_card_sha256(contract)
        self.session = self.root / "non-host-led-session"
        create_session(self.session, new_state(contract, NOW, None, {}))
        with self.assertRaisesRegex(ArtifactPolicyError, "host-led"):
            self._capture("HC1", "https://example.test/source", b"direct finding")

    def test_host_capture_accepts_bound_host_led_contract(self) -> None:
        self.session = self.root / "host-led-capture"
        create_session(self.session, new_state(confirmed_host_led_contract(), NOW, None, {}))

        artifact = self._capture(
            "HC1",
            "https://example.test/source",
            b"direct host finding",
            purpose="targeted re-verification of C1",
        )

        self.assertEqual(artifact["provenance"]["origin_kind"], "host_capture")
        self.assertEqual(
            artifact["host_capture"]["marginal_purpose"],
            "targeted re-verification of C1",
        )
        self.assertTrue(validate_session(self.session).integrity_ok)

    def test_organizer_cannot_patch_contract_semantics_marker(self) -> None:
        from research_harness.storage import ProtectedStatePath

        state = load_state(self.session)
        for operation in (
            {"op": "replace", "path": "/session/contract_semantics", "value": "legacy"},
            {"op": "remove", "path": "/session/contract_semantics"},
            {"op": "add", "path": "/session/contract_semantics", "value": "pure_trigger_v2"},
        ):
            with self.subTest(operation=operation), self.assertRaises(ProtectedStatePath):
                apply_state_patch(
                    self.session,
                    [operation],
                    state["session"]["revision"],
                    NOW,
                )

    def test_host_native_human_completeness_is_a_warning_gate(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        state = load_state(self.session)
        apply_state_patch(
            self.session,
            [{"op": "replace", "path": "/summary/human_recommendation", "value": ""}],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(self.session)
        self.assertFalse(report.tier_contract_met, report.to_dict())
        self.assertFalse(report.errors, report.to_dict())

    def test_each_human_completeness_gap_is_warning_only_and_insufficient(self) -> None:
        missing_fields = (
            ("/summary/human_status", ""),
            ("/summary/human_status", "證據不足"),
            ("/summary/human_status", "EVIDENCE_INSUFFICIENT"),
            ("/summary/human_status", "交付不完整"),
            ("/summary/human_status", "DELIVERY_INCOMPLETE"),
            ("/summary/human_recommendation", ""),
            ("/summary/decision", ""),
            ("/claims/0/text", ""),
            ("/engineering_handoff/constraints", []),
            ("/engineering_handoff/safe_actions", []),
            ("/engineering_handoff/acceptance_tests", []),
            ("/engineering_handoff/acceptance_tests", ["x"]),
        )
        for index, (path, value) in enumerate(missing_fields):
            with self.subTest(path=path):
                self.session = self._make_session(label=str(index))
                artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
                self._link_claim(
                    [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
                )
                state = load_state(self.session)
                operations = [{"op": "replace", "path": path, "value": value}]
                if path == "/engineering_handoff/constraints":
                    operations.extend(
                        [
                            {"op": "replace", "path": "/open_questions", "value": []},
                            {"op": "replace", "path": "/claims/0/would_change_if", "value": ""},
                        ]
                    )
                if path == "/engineering_handoff/safe_actions":
                    operations.append(
                        {"op": "replace", "path": "/summary/status", "value": "BLOCKED"}
                    )
                apply_state_patch(self.session, operations, state["session"]["revision"], NOW)
                report = validate_session(self.session)
                self.assertFalse(report.tier_contract_met, report.to_dict())
                self.assertFalse(report.errors, report.to_dict())
                first_screen = render_session_result(self.session).path.read_text(encoding="utf-8").split('<summary>技術細節</summary>', 1)[0]
                self.assertEqual(report.human_status, "交付不完整")
                self.assertIn("BLOCKED / DELIVERY_INCOMPLETE", first_screen + render_session_result(self.session).path.read_text(encoding="utf-8"))
                self.assertIn("補齊交付要件後重新產生報告", first_screen)
                self.assertNotIn("尚缺足夠的直接來源，結論可能改變", first_screen)

    def test_complete_host_package_has_deliverable_human_surface(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        report = validate_session(self.session)
        self.assertTrue(report.ok, report.to_dict())
        first_screen = render_session_result(self.session).path.read_text(encoding="utf-8").split('<summary>技術細節</summary>', 1)[0]
        for value in ("已完成研究判斷", "建議採用", "採用此有界結論", "Captured source", "若來源改變則重新評估", "A1"):
            self.assertIn(value, first_screen)
        self.assertEqual(first_screen.count('<article class="safe-action">'), 1)

    def test_blank_whitespace_and_non_string_limitations_do_not_pass(self) -> None:
        cases = (
            ("/engineering_handoff/constraints", ["", "  ", 1]),
            ("/open_questions", [{"id": "Q1"}]),
            ("/claims/0/would_change_if", " "),
        )
        for index, (path, value) in enumerate(cases):
            with self.subTest(path=path):
                self.session = self._make_session(label=f"blank-{index}")
                artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
                self._link_claim(
                    [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
                )
                state = load_state(self.session)
                operations = [{"op": "replace", "path": path, "value": value}]
                for other_path in (
                    "/engineering_handoff/constraints",
                    "/open_questions",
                    "/claims/0/would_change_if",
                ):
                    if other_path != path:
                        operations.append({"op": "replace", "path": other_path, "value": [] if other_path != "/claims/0/would_change_if" else ""})
                apply_state_patch(self.session, operations, state["session"]["revision"], NOW)
                report = validate_session(self.session)
                self.assertFalse(report.tier_contract_met, report.to_dict())
                self.assertFalse(report.errors, report.to_dict())

    def test_host_evidence_rejects_source_key_mismatch(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://other.test/source", "canonical_source_key": "https://other.test/source", "payload": b"direct finding"}]
        )

        report = validate_session(self.session)

        self.assertIn("evidence.host_capture_source_key_mismatch", {issue.code for issue in report.errors})
        # A source-key mismatch is an integrity failure, not a tier/profile
        # floor -- the light profile this fixture carries has no extra
        # evidence floor of its own (see _profile_evidence_contract), so
        # tier_contract_met genuinely stays True; report.ok still catches it
        # via integrity_ok.
        self.assertFalse(report.integrity_ok)
        self.assertFalse(report.ok)
        self.assertTrue(report.tier_contract_met)

    def test_in_progress_is_delivery_incomplete_and_finalizer_seals_matching_status(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        state = load_state(self.session)
        apply_state_patch(
            self.session,
            [{"op": "replace", "path": "/summary/status", "value": "IN_PROGRESS"}],
            state["session"]["revision"],
            NOW,
        )

        report = validate_session(self.session)
        self.assertFalse(report.tier_contract_met, report.to_dict())
        self.assertEqual(report.human_status, "交付不完整")
        self.assertIn("tier.terminal_status_missing", {issue.code for issue in report.warnings})

        rendered = finalize_session_result(self.session, NOW)
        sealed = load_state(self.session)
        self.assertEqual(sealed["summary"]["status"], "BLOCKED")
        self.assertEqual(sealed["summary"]["human_status"], "交付不完整")
        self.assertFalse(rendered.validation.tier_contract_met)
        self.assertIn(
            "BLOCKED / DELIVERY_INCOMPLETE", rendered.path.read_text(encoding="utf-8")
        )

    def test_invalid_acceptance_grammar_is_delivery_incomplete(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        for value in ("x", " -> expected", "check -> ", " => expected", "check => "):
            with self.subTest(value=value):
                state = load_state(self.session)
                apply_state_patch(
                    self.session,
                    [
                        {
                            "op": "replace",
                            "path": "/engineering_handoff/acceptance_tests",
                            "value": [value],
                        }
                    ],
                    state["session"]["revision"],
                    NOW,
                )

                report = validate_session(self.session)
                self.assertFalse(report.tier_contract_met, report.to_dict())
                self.assertEqual(report.human_status, "交付不完整")
                self.assertIn(
                    "tier.acceptance_tests_missing",
                    {issue.code for issue in report.warnings},
                )

    def test_any_acceptance_test_with_nonempty_check_and_expected_is_sufficient(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        for value in (" check => expected ", "command -> 65 passed"):
            with self.subTest(value=value):
                state = load_state(self.session)
                apply_state_patch(
                    self.session,
                    [
                        {
                            "op": "replace",
                            "path": "/engineering_handoff/acceptance_tests",
                            "value": ["x", value],
                        }
                    ],
                    state["session"]["revision"],
                    NOW,
                )

                report = validate_session(self.session)
                self.assertTrue(report.tier_contract_met, report.to_dict())
                self.assertNotIn(
                    "tier.acceptance_tests_missing", {issue.code for issue in report.issues}
                )

    def test_finalizer_seals_semantically_invalid_pass_even_when_tier_floor_is_met(self) -> None:
        artifact = self._capture("HC1", "https://example.test/source", b"direct finding")
        self._link_claim(
            [{"id": "E1", "artifact_id": artifact["id"], "source_url": "https://example.test/source", "canonical_source_key": "https://example.test/source", "payload": b"direct finding"}]
        )
        state = load_state(self.session)
        apply_state_patch(
            self.session,
            [{"op": "replace", "path": "/summary/status", "value": "PASS"}],
            state["session"]["revision"],
            NOW,
        )

        before = validate_session(self.session)
        self.assertTrue(before.integrity_ok, before.to_dict())
        self.assertTrue(before.tier_contract_met, before.to_dict())
        self.assertFalse(before.ok, before.to_dict())
        self.assertTrue(before.errors, before.to_dict())

        rendered = finalize_session_result(self.session, NOW)
        sealed = load_state(self.session)
        self.assertEqual(sealed["summary"]["status"], "BLOCKED")
        self.assertEqual(sealed["summary"]["human_status"], "交付不完整")
        self.assertFalse(rendered.validation.tier_contract_met)
        self.assertIn(
            "BLOCKED / DELIVERY_INCOMPLETE", rendered.path.read_text(encoding="utf-8")
        )

    def test_host_capture_lineage_cannot_be_added_by_generic_organizer_patch(self) -> None:
        from research_harness.storage import ProtectedStatePath

        state = load_state(self.session)
        with self.assertRaises(ProtectedStatePath):
            apply_state_patch(
                self.session,
                [{"op": "add", "path": "/artifact_index/-", "value": {"id": "forged"}}],
                state["session"]["revision"],
                NOW,
            )

    def _make_session(self, label: str = "") -> Path:
        # confirmed_contract() already returns the live host-led shape
        # (execution=external_managed, research_workflow=host_led_v1, ...)
        # ingest_host_capture requires; its `tier` argument is cosmetic
        # only (see tests/helpers.py).
        session = self.root / f"session-{label or 'default'}"
        contract = confirmed_contract("medium")
        create_session(session, new_state(contract, NOW, None, {}))
        return session


if __name__ == "__main__":
    unittest.main()
