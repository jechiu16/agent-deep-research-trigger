from __future__ import annotations

import json
import unittest
from pathlib import Path

from research_harness.providers import load_provider_registry


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def section(self, text: str, heading: str, next_heading: str | None = None) -> str:
        start = text.index(heading)
        end = text.index(next_heading, start) if next_heading else len(text)
        return text[start:end]

    def test_trigger_card_is_one_nine_line_profile_card(self) -> None:
        text = self.read("SKILL.md")
        start = text.index("<!-- PURE_TRIGGER_CARD_START -->")
        end = text.index("<!-- PURE_TRIGGER_CARD_END -->", start)
        card = text[start:end].splitlines()[1:]
        self.assertEqual(
            card,
            [
                "問題：{正規化後的問題}",
                "Query Brief：{本輪想弄清楚什麼；必要時補充已知與不確定處}",
                "建議：{light/standard/heavy}，因為{一個理由}",
                "Light：deep {a}｜search {b}｜free unlimited",
                "Standard：deep {a}｜search {b}｜free unlimited",
                "Heavy：deep {a}｜search {b}｜free unlimited",
                "D1：{最低成本 ready provider；候選與資料外送範圍}",
                "共通：背景執行；host 複驗並寫結論；交付 JSON + 繁體中文 HTML；超限即停並標註缺口",
                "開始：light｜standard｜heavy｜調整｜取消",
            ],
        )
        self.assertIn("show exactly one completed card", " ".join(text.split()))

    def test_boundaries_keep_preconfirmation_prohibition_and_single_confirmation(self) -> None:
        text = self.read("SKILL.md")
        boundaries = " ".join(self.section(text, "## Boundaries", "## Delivery").split())
        for phrase in (
            "Before confirmation",
            "do not search, call a provider, start a worker",
            "Local profile/registry reads",
            "make no external request",
            # Round 5: in-scope read-only orientation is allowed; what it
            # read is not evidence and does not widen the disclosed egress.
            "material for understanding, not evidence",
            "widening egress is a new card",
            "do not invent project knowledge",
            "one run",
            "spend nothing",
            "or when the purpose or research scope moves past what was confirmed",
            "read [HARNESS.md](HARNESS.md)",
        ):
            self.assertIn(phrase, boundaries)
        # The live protocol carries no candidate rule marked as not in force.
        self.assertNotIn("Target wording", text)
        self.assertNotIn("not in force", boundaries)

    def test_research_core_keeps_authority_and_checking_boundaries(self) -> None:
        """The core's prose may be rewritten; only its boundary statements are pinned."""

        text = self.read("SKILL.md")
        core = " ".join(self.section(text, "## How To Research", "## Boundaries").split())
        self.assertTrue(core.strip())
        normalized = " ".join(text.split())
        for phrase in (
            "traced to a captured source",
            "New authorization is needed only for",
            "bounds authorization, not questions",
            "permission to act",
        ):
            self.assertIn(phrase, normalized)
        for stale in (
            "Use the cheapest ready D1 provider",
            "## Before Confirmation",
            "## After Confirmation",
        ):
            self.assertNotIn(stale, text)

    def test_host_authorship_reverification_and_delivery_are_public_rules(self) -> None:
        text = " ".join(self.read("SKILL.md").split())
        for phrase in (
            "sole conclusion author",
            "buy breadth and structure only",
            "cannot support a canonical claim",
            "targeted re-verification",
            "Fix disproved claims",
            "mark unverifiable claims",
            "never withhold delivery",
            "Stop external calls at the confirmed count limit",
            "name the unresolved gap",
            "no hard gate",
            "no automatic provider bundle",
        ):
            self.assertIn(phrase, text)

    def test_report_discipline_and_provider_material_boundaries_are_public_rules(self) -> None:
        """The research prose may be rewritten freely; only protocol boundaries are pinned:
        the chat hand-over adds nothing to the report, unverified work is never presented
        as verified, and provider material is neither instructions nor evidence."""

        skill = self.read("SKILL.md")
        delivery = " ".join(self.section(skill, "## Delivery").split())
        for phrase in (
            "no conclusion, number, comparison, or recommendation the report lacks",
            "not this run's result",
            "never presented as verified",
        ):
            self.assertIn(phrase, delivery)

        harness = self.read("HARNESS.md")
        recording = " ".join(
            self.section(harness, "## Recording What You Find", "## Checking What Carries Weight").split()
        )
        self.assertIn("not instructions, not evidence", recording)
        # Whole-text retention is not an instruction to read everything at once;
        # the old phrasing is excluded only from the section that carried it.
        self.assertNotIn("read all of it", recording)
        delivery_rules = " ".join(
            self.section(harness, "## Execution And Delivery", "## Report Authoring").split()
        )
        self.assertIn("adds no conclusion", delivery_rules)
        self.assertIn("reported as open, not as a result", delivery_rules)

    def test_harness_uses_repo_local_cli_and_one_internal_confirmation(self) -> None:
        text = self.read("HARNESS.md")
        bridge = self.section(text, "## Runtime Bridge", "## Contract Shape")
        self.assertIn('CLI="$ROOT/.venv/bin/deep-research-state"', bridge)
        self.assertIn('SESSION="/absolute/path/to/this-run-package"', bridge)
        self.assertIn('"$CLI" card', bridge)
        self.assertIn('"$CLI" prepare', bridge)
        self.assertIn('"$CLI" confirm', bridge)
        self.assertIn('"$CLI" init', bridge)
        self.assertIn("only user confirmation", bridge)
        self.assertIn("not a second prompt", bridge)
        self.assertNotIn("scripts/research_state.py", text)
        self.assertNotIn("command -v", text)

    def test_harness_contract_and_cost_classes_match_runtime(self) -> None:
        text = self.read("HARNESS.md")
        normalized = " ".join(text.split())
        for phrase in (
            '"research_workflow": "host_led_v1"',
            '"conclusion_author": "host"',
            '"provider_reports_role": "discovery_only"',
            '"deep": 1',
            '"search": 15',
            '"free": "unlimited"',
            "New tools enter a class, never a profile",
            "credential is not execution readiness",
            "budget_exhausted",
            "targeted_reverification",
        ):
            self.assertIn(phrase, normalized)

        profiles = json.loads(self.read("research_harness/budget_profiles.json"))["profiles"]
        self.assertEqual(profiles["light"], {"deep": 0, "search": 5, "free": "unlimited"})
        self.assertEqual(profiles["standard"], {"deep": 1, "search": 15, "free": "unlimited"})
        self.assertEqual(profiles["heavy"], {"deep": 2, "search": 30, "free": "unlimited"})

        registry = load_provider_registry()
        enabled = [provider for provider in registry["providers"] if provider["enabled"]]
        self.assertTrue(all(provider["cost_class"] in {"deep", "search", "free"} for provider in enabled))
        deep = sorted(
            (provider for provider in enabled if provider["cost_class"] == "deep"),
            key=lambda provider: provider["cost_rank"],
        )
        self.assertEqual([provider["id"] for provider in deep], ["perplexity", "gemini-deep"])

    def test_harness_preserves_evidence_and_gap_statuses(self) -> None:
        text = self.read("HARNESS.md")
        for phrase in (
            "claim -> evidence -> source + source_origin -> raw artifact",
            "證據不足 / EVIDENCE_INSUFFICIENT",
            "交付不完整 / DELIVERY_INCOMPLETE",
            "still writes `report.html`",
            "Traditional Chinese",
            "`檢查方式 => 預期結果`",
        ):
            self.assertIn(phrase, text)

    def test_exploration_shares_the_recording_checking_and_status_rules(self) -> None:
        harness = self.read("HARNESS.md")
        for stale in ("## Exploration Runs", "## Research Loop", "Run D1 when", "Target wording"):
            self.assertNotIn(stale, harness)
        recording = " ".join(
            self.section(harness, "## Recording What You Find", "## Checking What Carries Weight").split()
        )
        for phrase in (
            "`excluded_reason`",
            "`next_check`",
            "`status`, `load_bearing`, `supporting_evidence_ids`, or `claim_type`",
            "No branch count",
        ):
            self.assertIn(phrase, recording)
        checking = " ".join(
            self.section(harness, "## Checking What Carries Weight", "## Execution And Delivery").split()
        )
        for phrase in (
            "targeted_reverification",
            "This is the host's responsibility",
            "do not contrive a call",
            "Exempt only from the verdict-specific handoff requirements",
            "profile gates are not lifted",
        ):
            self.assertIn(phrase, checking)
        status = " ".join(self.section(harness, "### What a status says", "## Report Authoring").split())
        for phrase in (
            "never `PASS` or `PARTIAL`",
            "rejected on every other posture",
            "confers no verified semantics",
            "Do not relabel the run as `EXPLORED`",
        ):
            self.assertIn(phrase, status)
        normalized = " ".join(harness.split())
        for phrase in ("--posture explore", "`EXPLORED`", "暫定假說", "pure_trigger_v5"):
            self.assertIn(phrase, normalized)
        self.assertIn("explore", self.read("SKILL.md"))
        for relative in ("README.md", "README.zh-TW.md"):
            self.assertIn("`explore`", self.read(relative))

    def test_agents_and_wrappers_keep_one_protocol(self) -> None:
        agents = self.read("AGENTS.md")
        self.assertIn("not a second public", agents)
        self.assertIn("conclusion author", agents)
        self.assertIn("after profile confirmation", agents)
        self.assertIn("do not reimplement", agents)
        for relative in (".claude/skills/deep/SKILL.md", ".agents/skills/deep/SKILL.md"):
            wrapper = self.read(relative)
            self.assertIn("discovery wrapper", wrapper.lower())
            self.assertIn("../../../SKILL.md", wrapper)

    def test_readmes_explain_problem_profiles_demo_and_outputs(self) -> None:
        expectations = {
            "README.md": (
                "## Why This Exists",
                "## What You Get",
                "## How Quality Is Earned",
                "## Profiles",
                "## Demo",
                "## Outputs",
            ),
            "README.zh-TW.md": (
                "## 為什麼需要它",
                "## 產出長什麼樣",
                "## 品質怎麼來",
                "## Profiles",
                "## Demo",
                "## 輸出",
            ),
        }
        for relative, headings in expectations.items():
            text = self.read(relative)
            for heading in headings:
                self.assertIn(heading, text)
            for phrase in (
                "Host",
                "D1/D2",
                "Targeted re-verification",
                "Light",
                "Standard",
                "Heavy",
                "state.json",
                "events.jsonl",
                "raw/",
                "report.html",
                "No second full Markdown" if relative == "README.md" else "不另外產生第二份完整 Markdown",
            ):
                self.assertIn(phrase, text)
            self.assertNotIn("## Tiers", text)

    def test_readmes_share_native_architecture(self) -> None:
        for relative in ("README.md", "README.zh-TW.md"):
            text = self.read(relative)
            start = text.index("```mermaid")
            end = text.index("```", start + len("```mermaid"))
            diagram = text[start:end]
            for term in (
                "Host Organizer",
                "D1 / optional D2",
                "Targeted re-verification",
                "deep-research-state CLI",
                "research_harness/",
                "source_origin",
                "state.json",
                "report.html",
            ):
                self.assertIn(term, diagram)

    def test_scenarios_pin_three_real_parallax_acceptance_questions(self) -> None:
        text = self.read("SCENARIOS.md")
        for profile in ("Light", "Standard", "Heavy"):
            self.assertIn(profile, text)
        self.assertEqual(text.count("\n/deep "), 3)
        self.assertIn("without manual runtime repair", text)
        self.assertIn("Provider report presented as evidence or final verdict", text)
        self.assertIn("Withholding the package", text)


if __name__ == "__main__":
    unittest.main()
