"""explore posture: a direction map delivered as EXPLORED, not a verdict.

Covers the acceptance scenarios in
docs/superpowers/specs/2026-09-07-exploration-first-mvp.md:

  A  a package holding only tentative directions delivers through the
     public CLI (draft -> prepare -> confirm -> init -> patch -> finalize ->
     render) with no fabricated claim or handoff;
  B  Heavy is a ceiling, not a claim quota: no D1/D2, second source, or
     extra claim is demanded of an exploration;
  C  a direction excluded mid-run keeps its reason and the rest survives;
  D  finishing as EXPLORED confers no verified semantics -- hypotheses
     cannot borrow claim vocabulary, claims presented as verified still
     clear the full evidence chain, and explore cannot end PASS/PARTIAL;
  E  raw-artifact integrity and quota rejection are unchanged;
  F  the new posture/status exist only under pure_trigger_v5 -- older
     packages keep their recorded verdict vocabulary;
  G  the shipped offline example reads the same from state.json and
     report.html.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from research_harness.artifacts import ingest_host_capture
from research_harness.contracts import (
    contract_card_sha256,
    draft_host_led_contract,
    validate_contract,
)
from research_harness.providers import (
    load_provider_registry,
    provider_records_sha256,
    provider_registry_sha256,
    referenced_provider_records,
)
from research_harness.quota import QuotaExceeded, acquire_permits, cost_usage
from research_harness.rendering import finalize_session_result, render_session_result
from research_harness.state import CONTRACT_SEMANTICS_V4, CONTRACT_SEMANTICS_V5, new_state
from research_harness.storage import StateValidationError, apply_state_patch, create_session, load_state
from research_harness.validation import validate_session
from tests.helpers import NOW


ROOT = Path(__file__).resolve().parents[1]
ENVIRON = {"PERPLEXITY_API_KEY": "test-key"}
QUESTION = "除了繼續加 provider，這個框架還有哪些值得探索的演進方向？"
H1_TEXT = "保留薄 skill，可能比新增獨立 runner 更符合日常專案探索。"
H2_TEXT = "同一 session 內從 explore 升格為 decision 合約。"
H3_TEXT = "讓下一個 host 只讀 state.json 就能接手探索。"
Q1_TEXT = "另一個 host 接手探索結果的成本要怎麼量測？"
P1_TEXT = "只讀 state.json，讓第二個 host 指出下一步。"
EXCLUDED_REASON = "本輪範圍明確排除同 session 合約切換；留待正式 decision 合約。"
EXAMPLE_SESSION = ROOT / "examples" / "explore" / "01-framework-evolution-directions" / "session"


def _confirmed_contract(posture: str, profile: str, registry: dict[str, Any]) -> dict[str, Any]:
    contract = draft_host_led_contract(
        QUESTION, posture, profile, registry, ENVIRON, search_routes=[]
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


def _direction_map_operations(status: str = "EXPLORED") -> list[dict[str, Any]]:
    """The smallest useful exploration: two leads, one unknown, one next check."""

    return [
        {
            "op": "add",
            "path": "/hypotheses/-",
            "value": {
                "id": "H1",
                "text": H1_TEXT,
                "basis": "暫定假說；尚未測試跨 host 接手成本。",
                "next_check": "用同一份研究資料測試另一個 host 能否找到下一步。",
            },
        },
        {"op": "add", "path": "/hypotheses/-", "value": {"id": "H2", "text": H2_TEXT}},
        {"op": "add", "path": "/open_questions/-", "value": {"id": "Q1", "question": Q1_TEXT}},
        {
            "op": "add",
            "path": "/planned_checks/-",
            "value": {"id": "P1", "text": P1_TEXT, "hypothesis_ids": ["H1"]},
        },
        {"op": "replace", "path": "/summary/status", "value": status},
        {"op": "replace", "path": "/summary/human_status", "value": "探索完成，方向仍待驗證"},
        {
            "op": "replace",
            "path": "/summary/human_recommendation",
            "value": "先做 P1 的跨 host 接手測試，再決定要不要進入選型。",
        },
    ]


def _codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues}


def _gate_codes(report: Any) -> set[str]:
    """Delivery/evidence gate codes only -- platform durability warnings are not gates."""

    return {code for code in _codes(report) if not code.startswith("session.")}


class ExploreContractTests(unittest.TestCase):
    def test_explore_is_accepted_at_every_profile_with_no_claim_floor(self) -> None:
        registry = load_provider_registry()
        for profile in ("light", "standard", "heavy"):
            with self.subTest(profile=profile):
                contract = _confirmed_contract("explore", profile, registry)
                self.assertEqual(contract["evidence_floor"]["minimum_load_bearing_claims"], 0)
                self.assertEqual(validate_contract(contract, registry), [])

    def test_other_postures_keep_their_positive_floor(self) -> None:
        registry = load_provider_registry()
        contract = _confirmed_contract("decision", "heavy", registry)
        self.assertEqual(contract["evidence_floor"]["minimum_load_bearing_claims"], 2)
        contract["evidence_floor"]["minimum_load_bearing_claims"] = 0
        contract["confirmation"]["card_sha256"] = contract_card_sha256(contract)
        self.assertIn(
            "evidence floor must require at least one load-bearing claim",
            validate_contract(contract, registry),
        )


class ExploreDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.registry = load_provider_registry()

    def _session(self, profile: str, label: str, *, posture: str = "explore", semantics: str | None = None) -> Path:
        session = self.root / f"{posture}-{profile}-{label}"
        state = new_state(_confirmed_contract(posture, profile, self.registry), NOW, self.registry, ENVIRON)
        if semantics is not None:
            state["session"]["contract_semantics"] = semantics
        create_session(session, state)
        return session

    def _patch(self, session: Path, operations: list[dict[str, Any]]) -> None:
        state = load_state(session)
        apply_state_patch(session, operations, state["session"]["revision"], NOW)

    # --- A -------------------------------------------------------------
    def test_tentative_directions_deliver_explored_without_claims_or_handoff(self) -> None:
        session = self._session("light", "a")
        self._patch(session, _direction_map_operations())

        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())
        self.assertTrue(report.tier_contract_met)
        self.assertEqual(_gate_codes(report), set())
        self.assertEqual(report.human_status, "探索完成，方向仍待驗證")

        rendered = finalize_session_result(session, NOW)
        sealed = load_state(session)
        self.assertEqual(sealed["summary"]["status"], "EXPLORED")
        self.assertEqual(sealed["summary"]["human_status"], "探索完成，方向仍待驗證")
        self.assertEqual(sealed["summary"]["load_bearing_claim_ids"], [])
        self.assertEqual(sealed["claims"], [])
        self.assertEqual(
            sealed["engineering_handoff"],
            {"constraints": [], "safe_actions": [], "acceptance_tests": []},
        )
        self.assertTrue(rendered.validation.ok)

        html = rendered.path.read_text(encoding="utf-8")
        first_screen = html.split("<summary>技術細節</summary>", 1)[0]
        for text in ("探索完成，方向仍待驗證", "暫定假說", H1_TEXT, H2_TEXT, Q1_TEXT, P1_TEXT,
                     "本輪仍不知道的事", "最值得做的下一個檢查", "用同一份研究資料測試另一個 host"):
            self.assertIn(text, first_screen)
        self.assertIn("EXPLORED", html)
        for text in ("BLOCKED", "工程交接", "驗收測試", "關鍵主張下限", "尚未記錄正式主張",
                     "尚未納入證據紀錄", "核心理由", "安全行動", "已驗證", "corroborated"):
            self.assertNotIn(text, html)
        self.assertIn("本輪為探索型交付，不做出有界結論。", html)

    def test_public_cli_flow_delivers_an_explore_package(self) -> None:
        cli = ROOT / "scripts" / "research_state.py"
        session = self.root / "cli-explore"

        def run(*args: str) -> str:
            result = subprocess.run(
                [sys.executable, str(cli), *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
                env={**os.environ, "PERPLEXITY_API_KEY": ""},
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{args[0]} failed:\n{result.stderr}\n{result.stdout}")
            return result.stdout

        card = run("card", "--question", QUESTION, "--posture", "explore")
        self.assertIn("研究模式：explore", card)
        self.assertIn("探索：", card)

        draft = json.loads(run("draft", "--question", QUESTION, "--posture", "explore", "--profile", "light", "--json"))
        self.assertEqual(draft["posture"], "explore")
        self.assertEqual(draft["evidence_floor"]["minimum_load_bearing_claims"], 0)
        draft_path = self.root / "draft.json"
        draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        prepared = json.loads(run("prepare", "--contract", str(draft_path), "--json"))
        prepared_path = self.root / "prepared.json"
        prepared_path.write_text(json.dumps(prepared, ensure_ascii=False), encoding="utf-8")
        binding = prepared["binding"]
        confirmed = json.loads(
            run(
                "confirm", "--prepared", str(prepared_path),
                "--card-sha256", binding["card_sha256"],
                "--registry-sha256", binding["registry_sha256"],
                "--referenced-records-sha256", binding["referenced_records_sha256"],
                "--confirmed-at", NOW, "--confirmed-by", "user", "--json",
            )
        )
        confirmed_path = self.root / "confirmed.json"
        confirmed_path.write_text(json.dumps(confirmed, ensure_ascii=False), encoding="utf-8")
        run("init", str(session), "--contract", str(confirmed_path), "--now", NOW, "--json")

        patch_path = self.root / "patch.json"
        patch_path.write_text(json.dumps(_direction_map_operations(), ensure_ascii=False), encoding="utf-8")
        run("patch", str(session), "--patch", str(patch_path), "--now", NOW, "--json")

        validated = json.loads(run("validate", str(session), "--json"))
        self.assertTrue(validated["ok"], validated)
        status = json.loads(run("status", str(session), "--json"))
        self.assertEqual(status["summary"]["status"], "EXPLORED")
        self.assertEqual(status["cost_usage"], {"deep": 0, "search": 0, "free": 0})
        sealed = json.loads(run("finalize", str(session), "--now", NOW, "--json"))
        self.assertTrue(sealed["validation"]["ok"], sealed)
        rendered = json.loads(run("render", str(session), "--now", NOW, "--json"))
        self.assertEqual(rendered["state_sha256"], sealed["state_sha256"])
        state = json.loads((session / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["summary"]["status"], "EXPLORED")
        self.assertEqual(state["session"]["contract_semantics"], CONTRACT_SEMANTICS_V5)
        self.assertIn("暫定假說", (session / "report.html").read_text(encoding="utf-8"))

    # --- B -------------------------------------------------------------
    def test_heavy_explore_is_a_ceiling_not_a_claim_quota(self) -> None:
        session = self._session("heavy", "b")
        self._patch(session, _direction_map_operations())

        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(_gate_codes(report), set())
        self.assertEqual(cost_usage(session), {"deep": 0, "search": 0, "free": 0})
        contract = load_state(session)["contract"]
        self.assertEqual(contract["resource_envelope"]["cost_budget"]["deep"], 2)
        self.assertEqual(contract["evidence_floor"]["minimum_load_bearing_claims"], 0)

    # --- C -------------------------------------------------------------
    def test_excluding_a_direction_mid_run_keeps_the_rest(self) -> None:
        session = self._session("light", "c")
        self._patch(session, _direction_map_operations())
        self._patch(
            session,
            [
                {"op": "add", "path": "/hypotheses/1/excluded_reason", "value": EXCLUDED_REASON},
                {"op": "add", "path": "/hypotheses/-", "value": {"id": "H3", "text": H3_TEXT, "source_ids": []}},
            ],
        )

        report = validate_session(session)
        self.assertTrue(report.ok, report.to_dict())
        state = load_state(session)
        self.assertEqual([item["id"] for item in state["hypotheses"]], ["H1", "H2", "H3"])
        html = render_session_result(session).path.read_text(encoding="utf-8")
        kept, excluded = html.split("<h3>已排除的方向</h3>", 1)
        self.assertIn(H1_TEXT, kept)
        self.assertIn(H3_TEXT, kept)
        self.assertIn(H2_TEXT, excluded)
        self.assertIn(EXCLUDED_REASON, excluded)
        self.assertIn("已排除", excluded)

    def test_hypothesis_pointers_must_resolve(self) -> None:
        session = self._session("light", "c-refs")
        with self.assertRaises(StateValidationError):
            self._patch(
                session,
                [{"op": "add", "path": "/hypotheses/-", "value": {"id": "H1", "text": H1_TEXT, "source_ids": ["S-missing"]}}],
            )

    # --- D -------------------------------------------------------------
    def test_hypothesis_cannot_borrow_claim_vocabulary(self) -> None:
        session = self._session("light", "d-vocab")
        for field, value in (("status", "corroborated"), ("load_bearing", True), ("supporting_evidence_ids", []), ("claim_type", "empirical")):
            with self.subTest(field=field), self.assertRaises(StateValidationError):
                self._patch(
                    session,
                    [{"op": "add", "path": "/hypotheses/-", "value": {"id": "H1", "text": H1_TEXT, field: value}}],
                )

    def test_explored_still_checks_claims_presented_as_verified(self) -> None:
        session = self._session("light", "d-claim")
        self._patch(
            session,
            _direction_map_operations()
            + [
                {
                    "op": "add",
                    "path": "/claims/-",
                    "value": {
                        "id": "C1",
                        "text": "未經查核就被當成決策前提的線索。",
                        "load_bearing": True,
                        "status": "corroborated",
                        "supporting_evidence_ids": [],
                    },
                },
                {"op": "replace", "path": "/summary/load_bearing_claim_ids", "value": ["C1"]},
            ],
        )

        report = validate_session(session)
        self.assertFalse(report.ok, report.to_dict())
        self.assertTrue(report.integrity_ok)
        self.assertIn("claim.evidence_missing", {issue.code for issue in report.errors})

        rendered = finalize_session_result(session, NOW)
        sealed = load_state(session)
        self.assertEqual(sealed["summary"]["status"], "BLOCKED")
        self.assertIn("BLOCKED", rendered.path.read_text(encoding="utf-8"))

    def test_explore_posture_cannot_finish_as_pass_or_partial(self) -> None:
        for status in ("PASS", "PARTIAL"):
            with self.subTest(status=status):
                session = self._session("light", f"d-{status.lower()}")
                self._patch(session, _direction_map_operations(status))
                report = validate_session(session)
                self.assertFalse(report.ok)
                self.assertIn("status.explore_verdict_forbidden", {issue.code for issue in report.errors})
                finalize_session_result(session, NOW)
                self.assertEqual(load_state(session)["summary"]["status"], "BLOCKED")

    def test_explored_is_rejected_on_a_decision_contract(self) -> None:
        session = self._session("light", "d-decision", posture="decision")
        self._patch(session, _direction_map_operations())
        report = validate_session(session)
        self.assertFalse(report.ok)
        self.assertIn("status.explored_posture_mismatch", {issue.code for issue in report.errors})

    # --- E -------------------------------------------------------------
    def test_explore_keeps_raw_integrity_and_quota_enforcement(self) -> None:
        session = self._session("light", "e")
        artifact = ingest_host_capture(
            session, "HC1", "https://example.test/source", "Captured source", "example.test",
            b"direct finding", "raw_http", NOW, "record a pointer for H1",
        )
        self._patch(
            session,
            _direction_map_operations()
            + [{"op": "add", "path": "/hypotheses/0/artifact_ids", "value": [artifact["id"]]}],
        )
        self.assertTrue(validate_session(session).ok)

        acquire_permits(session, "L1", "local_applicability", "local", "local", 1, NOW)
        with self.assertRaises(QuotaExceeded):
            acquire_permits(session, "L2", "local_applicability", "local", "local", 1, NOW)
        with self.assertRaises(QuotaExceeded):
            acquire_permits(session, "P1", "verification", "probe", "host-web", 1, NOW)

        raw_path = session / artifact["relative_path"]
        raw_path.write_bytes(b"tampered finding")
        report = validate_session(session)
        self.assertFalse(report.integrity_ok)
        self.assertIn("artifact.integrity", {issue.code for issue in report.errors})

    def test_blank_explore_package_is_sealed_delivery_incomplete(self) -> None:
        session = self._session("light", "blank")
        self._patch(session, _direction_map_operations()[4:])

        report = validate_session(session)
        self.assertFalse(report.tier_contract_met)
        self.assertFalse(report.errors)
        self.assertIn("explore.findings_missing", {issue.code for issue in report.warnings})
        self.assertEqual(report.human_status, "交付不完整")

        rendered = finalize_session_result(session, NOW)
        sealed = load_state(session)
        self.assertEqual(sealed["summary"]["status"], "BLOCKED")
        self.assertEqual(sealed["summary"]["human_status"], "交付不完整")
        html = rendered.path.read_text(encoding="utf-8")
        self.assertIn("BLOCKED / DELIVERY_INCOMPLETE", html)
        self.assertIn("補齊探索成果後重新產生報告", html)

    # --- F -------------------------------------------------------------
    def test_explore_vocabulary_exists_only_under_current_semantics(self) -> None:
        with self.assertRaises(StateValidationError):
            self._session("light", "f-posture", semantics=CONTRACT_SEMANTICS_V4)

        session = self._session("light", "f-status", posture="decision", semantics=CONTRACT_SEMANTICS_V4)
        self._patch(session, _direction_map_operations())
        report = validate_session(session)
        self.assertIn("status.explored_semantics", {issue.code for issue in report.errors})

    def test_older_semantics_do_not_gain_the_hypothesis_shape_rules(self) -> None:
        session = self._session("light", "f-hypothesis", posture="decision", semantics=CONTRACT_SEMANTICS_V4)
        self._patch(
            session,
            [{"op": "add", "path": "/hypotheses/-", "value": {"id": "H1", "text": H1_TEXT, "status": "open"}}],
        )
        self.assertEqual(load_state(session)["hypotheses"][0]["status"], "open")


class ExploreExampleTests(unittest.TestCase):
    """G: the shipped offline example is readable from JSON alone and matches its report."""

    def test_offline_example_validates_and_reads_as_tentative(self) -> None:
        self.assertTrue(EXAMPLE_SESSION.is_dir(), EXAMPLE_SESSION)
        report = validate_session(EXAMPLE_SESSION)
        self.assertTrue(report.ok, report.to_dict())
        state = json.loads((EXAMPLE_SESSION / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["contract"]["posture"], "explore")
        self.assertEqual(state["session"]["contract_semantics"], CONTRACT_SEMANTICS_V5)
        self.assertEqual(state["summary"]["status"], "EXPLORED")
        self.assertEqual(state["claims"], [])
        self.assertEqual(state["summary"]["load_bearing_claim_ids"], [])
        self.assertIn("示範", state["summary"]["decision"])

        hypotheses = state["hypotheses"]
        self.assertTrue(any(item.get("excluded_reason") for item in hypotheses))
        self.assertTrue(any(item.get("next_check") for item in hypotheses))
        self.assertTrue(state["open_questions"])
        self.assertTrue(state["planned_checks"])

        html = (EXAMPLE_SESSION / "report.html").read_text(encoding="utf-8")
        self.assertIn(report.state_sha256, html)
        for item in hypotheses:
            self.assertIn(item["text"], html)
        for item in state["open_questions"]:
            self.assertIn(item["question"], html)
        self.assertIn("暫定假說", html)
        self.assertIn("已排除", html)
        self.assertIn("示範", html)
        self.assertNotIn("工程交接", html)


if __name__ == "__main__":
    unittest.main()
