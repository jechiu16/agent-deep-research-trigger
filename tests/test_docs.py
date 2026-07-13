from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_v2_example_init_uses_question_from_contract(self) -> None:
        text = (ROOT / "examples" / "v2" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("--question", text)
        self.assertIn("--contract examples/v2/medium-contract.json", text)

    def test_canonical_trigger_card_is_traditional_chinese_and_kernel_free(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("<!-- PURE_TRIGGER_CARD_START -->")
        end = text.index("<!-- PURE_TRIGGER_CARD_END -->", start)
        card = text[start:end].splitlines()[1:]
        self.assertLessEqual(len(card), 7)
        self.assertTrue(card[0].startswith("問題："))
        self.assertTrue(card[1].startswith("建議："))
        self.assertIn("直接取得至少兩個不同來源", "\n".join(card))
        forbidden = ("hash", "route", "permit", "cli", "schema", "posture")
        self.assertFalse(any(term in "\n".join(card).lower() for term in forbidden))

    def test_codex_binding_points_to_canonical_skill_without_alternate_tier_semantics(self) -> None:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("[SKILL.md](SKILL.md)", text)
        self.assertIn("sole protocol", text.lower())
        self.assertNotIn("PURE_TRIGGER_CARD", text)
        self.assertNotIn("Choosing a tier", text)
        for line in ("Low:", "Medium:", "High:", "Start:"):
            self.assertNotIn(line, text)

    def test_host_protocol_selects_once_and_reports_phase_only_progress(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("choosing a tier is the only confirmation", text)
        self.assertIn("phase-only progress", text)
        self.assertIn("low", text)
        self.assertIn("medium", text)
        self.assertIn("high", text)

    def test_root_skill_is_complete_and_harness_is_optional(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
        self.assertNotIn("Read [HARNESS.md](HARNESS.md)", skill)
        self.assertIn("optional reference", harness.lower())
        self.assertIn("not required", harness.lower())

    def test_protocol_authority_is_unambiguous(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
        self.assertIn("sole default and human protocol", skill.lower())
        self.assertIn("thin binding", (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower())
        self.assertIn("implementation and recovery reference only", harness.lower())
        self.assertNotIn("complete default host interaction protocol", harness.lower())
        self.assertNotIn("executable protocol", harness.lower())

    def test_harness_public_protocol_has_one_tier_confirmation(self) -> None:
        text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
        start = text.index("## Public Protocol")
        end = text.index("## Internal Binding", start)
        protocol = text[start:end]
        normalized = " ".join(protocol.split()).lower()

        self.assertIn("sole public protocol", normalized)
        self.assertIn("literal `/deep`", protocol)
        self.assertIn("kernel-free seven-line card", normalized)
        self.assertIn("exactly one tier", normalized)
        for tier in ("low", "medium", "high"):
            with self.subTest(tier=tier):
                self.assertIn(tier, normalized)
        self.assertIn("adjust", normalized)
        self.assertIn("new card", normalized)
        self.assertIn("only confirmation", normalized)

        for term in ("custom", "posture", "route", "hash", "permit map"):
            with self.subTest(forbidden=term):
                self.assertNotIn(term, normalized)
        for command in ("prepare", "confirm", "init"):
            with self.subTest(command=command):
                self.assertNotRegex(protocol, rf"`{command}`|\b{command}\b")

    def test_harness_keeps_contract_binding_and_semantic_change_boundary_internal(self) -> None:
        text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
        start = text.index("## Internal Binding")
        end = text.index("## Scientific Organizer Loop", start)
        binding = " ".join(text[start:end].split()).lower()

        self.assertIn("derives and binds the canonical contract", binding)
        self.assertIn("after tier selection", binding)
        for operation in ("prepare", "confirm", "init"):
            with self.subTest(operation=operation):
                self.assertIn(f"`{operation}`", binding)
        self.assertIn("external paid-request count", binding)
        self.assertIn("local-data egress semantic change", binding)
        self.assertIn("new card and a new run", binding)

    def test_beta5_changelog_names_the_three_release_areas(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        beta5 = text.split("## 2.0.0b5", 1)[1].split("## 2.0.0b4", 1)[0]
        bullets: list[str] = []
        for line in beta5.splitlines():
            if line.startswith("- "):
                bullets.append(line[2:].lower())
            elif bullets and line.strip():
                bullets[-1] += f" {line.strip().lower()}"

        self.assertTrue(
            any(
                all(term in bullet for term in ("/deep", "low", "medium", "high", "canonical json", "zh-hant-tw", "blocked", "evidence-insufficient"))
                for bullet in bullets
            )
        )
        self.assertTrue(
            any(
                all(term in bullet for term in ("question-bound", "actual-request", "atomic reservation", "v3 occurrence lineage", "legacy-marker"))
                for bullet in bullets
            )
        )
        self.assertTrue(
            any(
                all(term in bullet for term in ("async", "no-token", "terminal-poll", "at-most-once", "resubmission"))
                for bullet in bullets
            )
        )

    def test_progress_uses_natural_traditional_chinese_user_phases(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        phases = ("界定問題", "蒐集資料", "交叉檢查", "形成結論", "交付結果")
        positions = [text.index(phase) for phase in phases]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("user-visible", text.lower())
        self.assertIn("internal", text.lower())

    def test_discovery_wrappers_do_not_define_a_second_protocol(self) -> None:
        for relative in (".claude/skills/deep/SKILL.md", ".agents/skills/deep/SKILL.md"):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertIn("../../../skill.md", text)
            self.assertNotIn("harness.md are the only protocol sources", text)

    def test_package_versions_are_consistent(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        from research_harness import __version__

        declared = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        self.assertIsNotNone(declared)
        self.assertEqual(declared.group(1), "2.0.0b5")
        self.assertEqual(declared.group(1), __version__)

    def test_beta5_release_metadata_is_coherent(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        registry = json.loads(
            (ROOT / "research_harness/provider_registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(changelog.startswith("# Changelog\n"))
        self.assertIn("## 2.0.0b5", changelog.split("## 2.0.0b4", 1)[0])
        self.assertLess(changelog.index("## 2.0.0b5"), changelog.index("## 2.0.0b4"))
        self.assertNotRegex(changelog, r"^## \[Unreleased\]\s*$", re.MULTILINE)
        self.assertNotIn("current package version is the `2.0.0b2`", changelog)
        openai_deep = next(provider for provider in registry["providers"] if provider["id"] == "openai-deep")
        self.assertTrue(openai_deep["enabled"])
        self.assertEqual(openai_deep["adoption_status"], "validated")
        self.assertIn(
            "live-occurrence-2026-07-12-rfc9110-o4-mini-deep-research",
            openai_deep["adoption_evidence"],
        )
        self.assertIn(
            "adoption gate: enabled after the 2026-07-12 live adoption occurrence",
            openai_deep["storage_rights"]["source"],
        )
        self.assertNotIn(
            "not yet enabled pending a live occurrence",
            json.dumps(registry, ensure_ascii=False),
        )

    def test_readmes_put_four_step_happy_path_before_optional_details(self) -> None:
        expected = {
            "README.md": {
                "heading": "## Quickstart",
                "steps": (
                    "1. **Install the skill.**",
                    "2. **Link it to one host.**",
                    "3. **Start a fresh session.**",
                    "4. **Type `/deep` and choose a tier.**",
                ),
                "next": "## Why this exists",
                "no_key": "no provider key",
                "native": "host-native",
                "low": "Chat-only answer with links; no package",
                "medium": "Adaptive research that always delivers the canonical package",
                "high": "Multiple direct sources that always deliver the canonical package",
            },
            "README.zh-TW.md": {
                "heading": "## 快速開始",
                "steps": (
                    "1. **安裝 skill。**",
                    "2. **連結到一個 host。**",
                    "3. **開啟新的 session。**",
                    "4. **輸入 `/deep` 並選擇 tier。**",
                ),
                "next": "## 為什麼需要它",
                "no_key": "不需要 provider key",
                "native": "Host-native",
                "low": "只在 chat 中回答並附上連結；不建立 package",
                "medium": "Adaptive research 一律交付包含 JSON 與",
                "high": "取得多個直接來源，一律交付包含 JSON 與",
            },
        }
        for relative, values in expected.items():
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                start = text.index(values["heading"])
                end = text.index(values["next"], start)
                quickstart = text[start:end]
                positions = [quickstart.index(step) for step in values["steps"]]
                self.assertEqual(positions, sorted(positions))
                self.assertIn(values["no_key"], quickstart)
                self.assertIn(values["native"], quickstart)
                self.assertIn(values["low"], quickstart)
                self.assertIn(values["medium"], quickstart)
                self.assertIn(values["high"], quickstart)

                self.assertIn('ln -s "$PWD" "$HOME/.claude/skills/deep"', quickstart)
                self.assertIn('ln -s "$PWD" "$HOME/.agents/skills/deep"', quickstart)
                self.assertNotIn(
                    'mkdir -p "$HOME/.claude/skills" "$HOME/.agents/skills"',
                    quickstart,
                )

    def test_current_public_docs_do_not_teach_first_use_ceremony(self) -> None:
        forbidden = (
            "hash-bound",
            "binding hash",
            "contract card",
            "custom request envelope",
            "custom envelope",
            "route-record hash",
            "before spend",
            "exact contract confirmation",
            "permit per physical request",
            "separate paid `permit` command",
        )
        for relative in (
            "README.md",
            "README.zh-TW.md",
            "SCENARIOS.md",
            "CONTRIBUTING.md",
        ):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").lower()
                for phrase in forbidden:
                    with self.subTest(phrase=phrase):
                        self.assertNotIn(phrase, text)

    def test_docs_preserve_delivery_adapter_and_async_recovery_semantics(self) -> None:
        readmes = {
            "README.md": "Medium and High always deliver the canonical package",
            "README.zh-TW.md": "Medium 與 High 一律交付 canonical package",
        }
        for relative, delivery_phrase in readmes.items():
            with self.subTest(document=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(delivery_phrase, " ".join(text.split()))
                self.assertIn("evidence-insufficient", text)
                self.assertNotIn("no report", text.lower())
                self.assertNotIn("擋下（不出報告）", text)
                self.assertIn("request-boundary provider adapters", text)
                self.assertNotIn("Permit-bound provider adapters", text)

        scenarios = (ROOT / "SCENARIOS.md").read_text(encoding="utf-8")
        for phrase in (
            "accepted or uncertain job has a provider token",
            "new poll action",
            "attempted job without a token is consumed",
            "non-pollable",
            "manual inspection",
            "must never be resubmitted",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, scenarios)

    def test_bindings_use_posture_and_tier(self) -> None:
        for relative in ("SKILL.md", "AGENTS.md", "HARNESS.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("posture", text.lower())
                self.assertIn("tier", text.lower())
                self.assertNotIn("depth x independence x strictness", text.lower())

    def test_readmes_reference_v2_cli(self) -> None:
        for relative in ("README.md", "README.zh-TW.md"):
            with self.subTest(path=relative):
                self.assertIn(
                    "scripts/research_state.py",
                    (ROOT / relative).read_text(encoding="utf-8"),
                )

    def test_product_identity_is_host_neutral(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "agent-deep-research-trigger"', pyproject)
        for relative in ("README.md", "README.zh-TW.md", "SKILL.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("Agent Deep Research Trigger", text)
                self.assertIn("Claude Code", text)
                self.assertIn("Codex", text)

    def test_both_hosts_have_project_skill_discovery_wrappers(self) -> None:
        wrappers = (
            ".claude/skills/deep/SKILL.md",
            ".agents/skills/deep/SKILL.md",
        )
        canonical = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for relative in wrappers:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("../../../SKILL.md", text)
                self.assertIn("name: deep", text)
                self.assertIn("description:", text)
        self.assertIn("shared by\nClaude Code and OpenAI Codex", canonical)

    def test_readmes_use_official_host_skill_locations(self) -> None:
        combined = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in ("README.md", "README.zh-TW.md")
        )
        self.assertIn("$HOME/.claude/skills/deep", combined)
        self.assertIn("$HOME/.agents/skills/deep", combined)

    def test_source_distribution_includes_agent_skill_files(self) -> None:
        manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        for required in (
            "SKILL.md",
            "AGENTS.md",
            "HARNESS.md",
            ".claude",
            ".agents",
        ):
            with self.subTest(path=required):
                self.assertIn(required, manifest)

    def test_current_scenarios_use_v2_contract_vocabulary(self) -> None:
        scenarios = (ROOT / "SCENARIOS.md").read_text(encoding="utf-8").lower()
        self.assertIn("posture", scenarios)
        self.assertIn("tier", scenarios)
        for legacy in ("three-axis", "preset: fast", "preset: standard"):
            with self.subTest(term=legacy):
                self.assertNotIn(legacy, scenarios)

    def test_readme_front_matter_is_searchable_and_focused(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        opening = "\n".join(readme.splitlines()[:20]).lower()
        for phrase in (
            "agent deep research trigger",
            "deep research",
            "agent skill",
            "claude code",
            "openai codex",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, opening)
        self.assertLessEqual(len(readme.splitlines()), 260)

    def test_active_identity_files_do_not_use_retired_brand(self) -> None:
        for relative in (
            "README.md",
            "README.zh-TW.md",
            "SKILL.md",
            "AGENTS.md",
            "HARNESS.md",
            "pyproject.toml",
        ):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").lower()
                self.assertNotIn("claude-research-cascade", text)

    def test_runtime_docs_name_registry_and_provider_portfolio(self) -> None:
        for relative in ("README.md", "README.zh-TW.md", "HARNESS.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").lower()
                self.assertIn("provider", text)
                self.assertIn("registry", text)

    def test_foundation_discloses_external_routes_are_not_v2_bound(self) -> None:
        for relative in ("README.md", "README.zh-TW.md", "HARNESS.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").lower()
                self.assertIn("external", text)
                self.assertIn("disabled", text)
                self.assertIn("worker", text)

    def test_runtime_docs_require_confirmation_validation_and_render(self) -> None:
        for relative in ("SKILL.md", "AGENTS.md", "HARNESS.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").lower()
                self.assertIn("confirm", text)
                self.assertIn("validate", text)
                self.assertIn("render", text)

    def test_docs_do_not_claim_key_readiness_is_execution_readiness(self) -> None:
        combined = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8").lower()
            for relative in ("README.md", "README.zh-TW.md", "HARNESS.md")
        )
        self.assertIn("credential", combined)
        self.assertIn("execution readiness", combined)

    def test_organizer_docs_define_traditional_chinese_report_boundary(self) -> None:
        for relative in ("SKILL.md", "AGENTS.md", "HARNESS.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("Traditional Chinese", text)
                self.assertIn("exact evidence excerpts", text)
                self.assertIn("source titles", text)
        for relative in ("README.md", "README.zh-TW.md"):
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("zh-Hant-TW", text)


if __name__ == "__main__":
    unittest.main()
