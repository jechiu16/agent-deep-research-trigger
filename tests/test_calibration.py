from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import calibration_report as cr


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _minimal_state(
    *,
    session_id: str = "deep-test",
    question: str = "What year was RFC 9110 published?",
    status: str = "PASS",
    load_bearing_claim_ids: list[str] | None = None,
    claims: list[dict[str, object]] | None = None,
    verification: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Only the fields calibration_report.py actually reads — not a full v2 schema document."""
    return {
        "schema_version": "2.0",
        "session": {"id": session_id},
        "framing": {"question": question},
        "summary": {
            "status": status,
            "load_bearing_claim_ids": load_bearing_claim_ids if load_bearing_claim_ids is not None else ["C1"],
        },
        "claims": claims if claims is not None else [{"id": "C1", "status": "corroborated"}],
        "verification": verification if verification is not None else [],
    }


class SessionExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_extracts_expected_fields_from_a_pass_session(self) -> None:
        session = self.root / "session-a"
        session.mkdir()
        _write_json(session / "state.json", _minimal_state())

        row, warnings = cr.extract_session(session)

        self.assertEqual(warnings, [])
        assert row is not None
        self.assertEqual(row["session_id"], "deep-test")
        self.assertEqual(row["question"], "What year was RFC 9110 published?")
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["load_bearing_claims"], 1)
        self.assertEqual(row["verification_yield"], 0)  # the one claim is corroborated
        self.assertTrue(row["verification_yield_is_proxy"])
        self.assertIsNone(row["total_cost_usd"])  # no provider_spool dir at all
        self.assertIsNone(row["ground_truth_verdict"])

    def test_question_longer_than_80_chars_is_truncated(self) -> None:
        session = self.root / "session-long-question"
        session.mkdir()
        long_question = "x" * 200
        _write_json(session / "state.json", _minimal_state(question=long_question))

        row, _warnings = cr.extract_session(session)

        assert row is not None
        self.assertLessEqual(len(row["question"]), 80)
        self.assertTrue(row["question"].endswith("…"))

    def test_cjk_question_is_truncated_by_character_not_by_byte(self) -> None:
        # "80 字" means 80 characters; a naive byte-length truncation would
        # cut a CJK question far too short (each character is multiple UTF-8
        # bytes) and could even split a multi-byte character in half.
        session = self.root / "session-cjk-question"
        session.mkdir()
        cjk_question = "如何完成一個agent-deep-research-trigger的校準評估" * 3
        _write_json(session / "state.json", _minimal_state(question=cjk_question))

        row, _warnings = cr.extract_session(session)

        assert row is not None
        self.assertLessEqual(len(row["question"]), 80)
        self.assertTrue(row["question"].startswith("如何完成一個"))
        self.assertTrue(row["question"].endswith("…"))

    def test_verification_yield_proxy_counts_non_corroborated_claims(self) -> None:
        session = self.root / "session-mixed-claims"
        session.mkdir()
        _write_json(
            session / "state.json",
            _minimal_state(
                claims=[
                    {"id": "C1", "status": "corroborated"},
                    {"id": "C2", "status": "unresolved"},
                    {"id": "C3", "status": "contested"},
                ]
            ),
        )

        row, _warnings = cr.extract_session(session)

        assert row is not None
        self.assertEqual(row["verification_yield"], 2)
        self.assertTrue(row["verification_yield_is_proxy"])

    def test_produced_candidate_false_on_a_clean_high_verifier_does_not_count_as_yield(self) -> None:
        """Regression guard: produced_candidate=False on a legitimate High-tier
        verifier means the verifier IS independent (a good thing), not that
        nothing was found. The proxy must stay claims-based and must not
        treat this field as a correction signal in either direction.
        """
        session = self.root / "session-high-verifier"
        session.mkdir()
        _write_json(
            session / "state.json",
            _minimal_state(
                claims=[{"id": "C1", "status": "corroborated"}],
                verification=[
                    {
                        "id": "V1",
                        "kind": "verifier",
                        "completed": True,
                        "context_separated": True,
                        "produced_candidate": False,
                        "action_id": "O1",
                    }
                ],
            ),
        )

        row, _warnings = cr.extract_session(session)

        assert row is not None
        self.assertEqual(row["verification_yield"], 0)

    def test_missing_state_json_is_a_warning_not_a_crash(self) -> None:
        session = self.root / "session-empty"
        session.mkdir()

        row, warnings = cr.extract_session(session)

        self.assertIsNone(row)
        self.assertEqual(len(warnings), 1)
        self.assertIn("cannot read file", warnings[0])

    def test_malformed_json_is_a_warning_not_a_crash(self) -> None:
        session = self.root / "session-bad-json"
        session.mkdir()
        (session / "state.json").write_text("{not valid json", encoding="utf-8")

        row, warnings = cr.extract_session(session)

        self.assertIsNone(row)
        self.assertEqual(len(warnings), 1)
        self.assertIn("invalid JSON", warnings[0])

    def test_state_json_that_is_not_an_object_is_a_warning_not_a_crash(self) -> None:
        session = self.root / "session-list-json"
        session.mkdir()
        _write_json(session / "state.json", ["not", "an", "object"])

        row, warnings = cr.extract_session(session)

        self.assertIsNone(row)
        self.assertEqual(len(warnings), 1)
        self.assertIn("not a JSON object", warnings[0])


class FindSessionDirsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_finds_a_flat_session_dir_passed_directly(self) -> None:
        session = self.root / "flat-session"
        session.mkdir()
        _write_json(session / "state.json", _minimal_state())

        dirs, warnings = cr.find_session_dirs([str(session)])

        self.assertEqual(dirs, [session.resolve()])
        self.assertEqual(warnings, [])

    def test_finds_a_nested_session_dir_under_a_root(self) -> None:
        # Mirrors real research_harness layouts where the CLI writes to
        # <root>/session/state.json rather than <root>/state.json directly.
        nested = self.root / "outer" / "session"
        nested.mkdir(parents=True)
        _write_json(nested / "state.json", _minimal_state())

        dirs, warnings = cr.find_session_dirs([str(self.root / "outer")])

        self.assertEqual(dirs, [nested.resolve()])
        self.assertEqual(warnings, [])

    def test_finds_multiple_sessions_at_mixed_depths_under_one_root(self) -> None:
        flat = self.root / "flat-session"
        flat.mkdir()
        _write_json(flat / "state.json", _minimal_state(session_id="flat"))
        nested = self.root / "outer" / "session"
        nested.mkdir(parents=True)
        _write_json(nested / "state.json", _minimal_state(session_id="nested"))

        dirs, warnings = cr.find_session_dirs([str(self.root)])

        self.assertEqual(dirs, sorted([flat.resolve(), nested.resolve()]))
        self.assertEqual(warnings, [])

    def test_accepts_a_direct_state_json_file_path(self) -> None:
        session = self.root / "session-via-file-arg"
        session.mkdir()
        state_path = session / "state.json"
        _write_json(state_path, _minimal_state())

        dirs, warnings = cr.find_session_dirs([str(state_path)])

        self.assertEqual(dirs, [session.resolve()])
        self.assertEqual(warnings, [])

    def test_nonexistent_path_is_a_warning_not_a_crash(self) -> None:
        dirs, warnings = cr.find_session_dirs([str(self.root / "does-not-exist")])

        self.assertEqual(dirs, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("does not exist", warnings[0])

    def test_root_with_no_state_json_anywhere_is_a_warning_not_a_crash(self) -> None:
        empty = self.root / "empty-root"
        empty.mkdir()

        dirs, warnings = cr.find_session_dirs([str(empty)])

        self.assertEqual(dirs, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("no state.json found", warnings[0])

    def test_overlapping_arguments_are_deduplicated(self) -> None:
        session = self.root / "shared-session"
        session.mkdir()
        _write_json(session / "state.json", _minimal_state())

        # Passing both the root and the session dir it contains should not
        # double-count the same session.
        dirs, warnings = cr.find_session_dirs([str(self.root), str(session)])

        self.assertEqual(dirs, [session.resolve()])
        self.assertEqual(warnings, [])


class CostExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_no_provider_spool_dir_means_unknown_cost_not_zero(self) -> None:
        session = self.root / "session-no-spool"
        session.mkdir()

        cost, warnings = cr._extract_cost_usd(session)

        self.assertIsNone(cost)
        self.assertEqual(warnings, [])

    def test_empty_provider_spool_dir_means_zero_cost(self) -> None:
        session = self.root / "session-empty-spool"
        (session / "provider_spool").mkdir(parents=True)

        cost, warnings = cr._extract_cost_usd(session)

        self.assertEqual(cost, 0.0)
        self.assertEqual(warnings, [])

    def test_sums_async_deep_shape_nested_under_response(self) -> None:
        session = self.root / "session-deep-cost"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(
            spool / "A1.raw.json",
            {"status": "COMPLETED", "response": {"usage": {"cost": {"total_cost": 0.62606}}}},
        )

        cost, warnings = cr._extract_cost_usd(session)

        self.assertAlmostEqual(cost, 0.62606)
        self.assertEqual(warnings, [])

    def test_sums_sync_shape_with_usage_at_top_level(self) -> None:
        session = self.root / "session-sync-cost"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(spool / "A1.raw.json", {"usage": {"cost": {"total_cost": 0.01217}}})

        cost, warnings = cr._extract_cost_usd(session)

        self.assertAlmostEqual(cost, 0.01217)
        self.assertEqual(warnings, [])

    def test_sums_exa_cost_dollars_total_shape(self) -> None:
        session = self.root / "session-exa-cost"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(
            spool / "A1.raw.json",
            {"costDollars": {"search": {"neural": 0.007}, "total": 0.007}, "results": []},
        )

        cost, warnings = cr._extract_cost_usd(session)

        self.assertAlmostEqual(cost, 0.007)
        self.assertEqual(warnings, [])

    def test_sums_openalex_meta_cost_usd_shape(self) -> None:
        session = self.root / "session-openalex-cost"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(spool / "A1.raw.json", {"meta": {"count": 42, "cost_usd": 0.0005}, "results": []})

        cost, warnings = cr._extract_cost_usd(session)

        self.assertAlmostEqual(cost, 0.0005)
        self.assertEqual(warnings, [])

    def test_sums_across_multiple_raw_files_and_shapes(self) -> None:
        session = self.root / "session-multi-cost"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(spool / "A1.raw.json", {"usage": {"cost": {"total_cost": 0.01}}})
        _write_json(
            spool / "A2.raw.json",
            {"status": "COMPLETED", "response": {"usage": {"cost": {"total_cost": 0.02}}}},
        )

        cost, warnings = cr._extract_cost_usd(session)

        self.assertAlmostEqual(cost, 0.03)
        self.assertEqual(warnings, [])

    def test_provider_payload_without_usage_contributes_zero(self) -> None:
        session = self.root / "session-no-usage"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        _write_json(spool / "A1.raw.json", {"demo": True, "query": "no usage field here"})

        cost, warnings = cr._extract_cost_usd(session)

        self.assertEqual(cost, 0.0)
        self.assertEqual(warnings, [])

    def test_malformed_raw_json_is_a_warning_and_contributes_zero(self) -> None:
        session = self.root / "session-bad-spool-file"
        spool = session / "provider_spool"
        spool.mkdir(parents=True)
        (spool / "A1.raw.json").write_text("{not valid", encoding="utf-8")

        cost, warnings = cr._extract_cost_usd(session)

        self.assertEqual(cost, 0.0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("invalid JSON", warnings[0])


class AnnotationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def test_loads_valid_annotation_lines_keyed_by_resolved_session_dir(self) -> None:
        session = self.root / "session-a"
        session.mkdir()
        annotations_path = self.root / "annotations.jsonl"
        annotations_path.write_text(
            json.dumps(
                {
                    "session_dir": str(session),
                    "question_id": "q1",
                    "ground_truth_verdict": "correct",
                    "notes": "matches expected_key_facts",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        by_dir, warnings = cr.load_annotations(annotations_path)

        self.assertEqual(warnings, [])
        self.assertEqual(by_dir[session.resolve()]["ground_truth_verdict"], "correct")

    def test_invalid_verdict_is_a_warning_not_a_crash(self) -> None:
        annotations_path = self.root / "annotations.jsonl"
        annotations_path.write_text(
            json.dumps({"session_dir": "/nonexistent", "ground_truth_verdict": "maybe"}) + "\n",
            encoding="utf-8",
        )

        by_dir, warnings = cr.load_annotations(annotations_path)

        self.assertEqual(by_dir, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn("ground_truth_verdict must be one of", warnings[0])

    def test_blank_lines_are_skipped_silently(self) -> None:
        annotations_path = self.root / "annotations.jsonl"
        annotations_path.write_text("\n\n   \n", encoding="utf-8")

        by_dir, warnings = cr.load_annotations(annotations_path)

        self.assertEqual(by_dir, {})
        self.assertEqual(warnings, [])

    def test_malformed_json_line_is_a_warning_not_a_crash(self) -> None:
        annotations_path = self.root / "annotations.jsonl"
        annotations_path.write_text("{not valid json\n", encoding="utf-8")

        by_dir, warnings = cr.load_annotations(annotations_path)

        self.assertEqual(by_dir, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn("invalid JSON", warnings[0])

    def test_missing_annotations_file_is_a_warning_not_a_crash(self) -> None:
        by_dir, warnings = cr.load_annotations(self.root / "does-not-exist.jsonl")

        self.assertEqual(by_dir, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn("cannot read annotations file", warnings[0])


class AggregationAndEndToEndTests(unittest.TestCase):
    """The brief's named scenario: 2-3 synthetic sessions (PASS/correct,
    PASS/incorrect, one broken directory) run through the full CLI path.
    """

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

        self.session_correct = self.root / "session-correct"
        self.session_correct.mkdir()
        _write_json(
            self.session_correct / "state.json",
            _minimal_state(session_id="deep-correct", status="PASS"),
        )

        self.session_incorrect = self.root / "session-incorrect"
        self.session_incorrect.mkdir()
        _write_json(
            self.session_incorrect / "state.json",
            _minimal_state(session_id="deep-incorrect", status="PASS"),
        )

        self.session_broken = self.root / "session-broken"
        self.session_broken.mkdir()
        (self.session_broken / "state.json").write_text("{not valid json", encoding="utf-8")

        self.annotations_path = self.root / "annotations.jsonl"
        self.annotations_path.write_text(
            "\n".join(
                json.dumps(record)
                for record in (
                    {
                        "session_dir": str(self.session_correct),
                        "question_id": "q1",
                        "ground_truth_verdict": "correct",
                        "notes": "",
                    },
                    {
                        "session_dir": str(self.session_incorrect),
                        "question_id": "q2",
                        "ground_truth_verdict": "incorrect",
                        "notes": "",
                    },
                )
            )
            + "\n",
            encoding="utf-8",
        )

    def test_run_aggregates_correctly_and_the_broken_session_only_warns(self) -> None:
        rows, summary, warnings = cr.run([str(self.root)], str(self.annotations_path))

        # Only the two well-formed sessions make it into rows; the broken
        # one is dropped with a warning, not raised as an exception.
        self.assertEqual(len(rows), 2)
        self.assertTrue(any("session-broken" in warning for warning in warnings))

        self.assertEqual(summary["sessions_scanned"], 2)
        self.assertEqual(summary["pass_count"], 2)
        self.assertEqual(summary["pass_annotated_count"], 2)
        # Accuracy formula: 1 correct out of 2 annotated PASS sessions.
        self.assertAlmostEqual(summary["pass_correct_rate"], 0.5)

    def test_pass_correct_rate_is_none_without_annotations(self) -> None:
        _rows, summary, _warnings = cr.run([str(self.root)], None)

        self.assertIsNone(summary["pass_correct_rate"])
        self.assertEqual(summary["pass_annotated_count"], 0)

    def test_markdown_render_does_not_crash_and_mentions_warnings(self) -> None:
        rows, summary, warnings = cr.run([str(self.root)], str(self.annotations_path))

        rendered = cr.render_markdown(rows, summary, warnings)

        self.assertIn("Calibration report", rendered)
        self.assertIn("PASS correct rate: 50.0%", rendered)
        self.assertIn("Warnings", rendered)

    def test_cli_json_output_is_parseable_and_matches_run(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.calibration_report", str(self.root), "--annotations", str(self.annotations_path), "--json"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )

        payload = json.loads(completed.stdout)

        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(payload["sessions"]), 2)
        self.assertEqual(payload["summary"]["pass_correct_rate"], 0.5)
        self.assertTrue(any("session-broken" in warning for warning in payload["warnings"]))

    def test_cli_with_no_matching_sessions_still_exits_zero(self) -> None:
        empty_root = self.root / "nothing-here"
        empty_root.mkdir()
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.calibration_report", str(empty_root), "--json"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["summary"]["sessions_scanned"], 0)


if __name__ == "__main__":
    unittest.main()
