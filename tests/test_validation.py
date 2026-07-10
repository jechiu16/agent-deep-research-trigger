from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_harness.storage import apply_state_patch, load_state
from research_harness.validation import validate_session
from tests.helpers import (
    NOW,
    append_valid_test_event_line,
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

    def test_no_network_demo_route_can_never_contribute_evidence(self) -> None:
        session = make_session_with_demo_evidence(self.root)
        report = validate_session(session)
        self.assertIn("evidence.demo_route_forbidden", {issue.code for issue in report.errors})

    def test_high_pass_requires_context_separated_verifier(self) -> None:
        session = make_incomplete_session(self.root, "high", "decision", "PASS")
        report = validate_session(session)
        self.assertIn("tier.high_verifier_missing", {issue.code for issue in report.errors})

    def test_complete_medium_lookup_passes_every_gate(self) -> None:
        session = make_complete_pass_session(self.root, "medium", "lookup")
        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())

    def test_complete_high_decision_with_separated_verifier_passes(self) -> None:
        session = make_complete_pass_session(self.root, "high", "decision")
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
