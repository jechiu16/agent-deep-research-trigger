from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from research_harness.rendering import render_html, render_session_result
from research_harness.state import state_sha256
from research_harness.storage import apply_state_patch, load_state, read_events
from research_harness.validation import validate_session
from tests.helpers import NOW, make_complete_pass_session


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.session = make_complete_pass_session(self.root)
        self.state = load_state(self.session)
        self.report = validate_session(self.session)

    def test_same_state_renders_identical_bytes(self) -> None:
        first = render_session_result(self.session).path.read_bytes()
        second = render_session_result(self.session).path.read_bytes()
        self.assertEqual(first, second)

    def test_untrusted_content_is_escaped(self) -> None:
        state = copy.deepcopy(self.state)
        state["summary"]["decision"] = '<script>alert("x")</script>'
        document = render_html(state, self.report)
        self.assertNotIn("<script>", document)
        self.assertIn("&lt;script&gt;", document)

    def test_html_embeds_current_state_hash(self) -> None:
        document = render_html(self.state, self.report)
        self.assertIn(state_sha256(self.state), document)

    def test_state_change_makes_existing_report_stale(self) -> None:
        render_session_result(self.session)
        revision = load_state(self.session)["session"]["revision"]
        apply_state_patch(
            self.session,
            [{"op": "replace", "path": "/summary/decision", "value": "changed"}],
            revision,
            NOW,
        )
        self.assertIn(
            "report.stale", {issue.code for issue in validate_session(self.session).errors}
        )

    def test_render_records_hash_bound_report_event(self) -> None:
        path = render_session_result(self.session).path
        event = read_events(self.session)[0][-1]
        self.assertEqual(event["event"], "report_generated")
        self.assertEqual(event["state_sha256"], state_sha256(load_state(self.session)))
        self.assertEqual(event["report_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_render_result_returns_exact_validation_and_hashes(self) -> None:
        result = render_session_result(self.session)
        self.assertTrue(result.validation.ok, result.validation.to_dict())
        self.assertEqual(result.state_sha256, state_sha256(load_state(self.session)))
        self.assertEqual(result.report_sha256, hashlib.sha256(result.path.read_bytes()).hexdigest())

    def test_report_has_no_script_or_external_assets(self) -> None:
        document = render_html(self.state, self.report)
        self.assertNotIn("<script", document.lower())
        self.assertNotIn("<link", document.lower())
        self.assertNotIn("@import", document.lower())

    def test_invalid_session_is_rendered_with_explicit_invalid_label(self) -> None:
        state = load_state(self.session)
        path = self.session / state["artifact_index"][0]["relative_path"]
        path.write_bytes(b"tampered")
        result = render_session_result(self.session)
        self.assertFalse(result.validation.ok)
        self.assertIn("INVALID", result.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
