"""Fixture-replay and live-adoption tests for Gemini Deep Research."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research_harness.adapters import gemini_deep
from research_harness.boundary import (
    AdapterParseError,
    AdapterTerminalFailure,
    BoundaryError,
    execute_deep_poll,
    execute_deep_submit,
)
from research_harness.contracts import contract_card_sha256, normalize_contract
from research_harness.providers import (
    load_provider_registry,
    provider_records_sha256,
    provider_registry_sha256,
    referenced_provider_records,
    validate_provider_registry,
)
from research_harness.state import new_state
from research_harness.storage import create_session, load_state, read_events
from tests.helpers import NOW, enabled_registry_copy


FIXTURES = Path(__file__).with_name("fixtures")
TEST_ENV = {"GEMINI_API_KEY": "test-key"}


def fixture_transport(name: str, status: int = 200):
    payload = (FIXTURES / name).read_bytes()

    def transport(spec):
        return status, payload

    return transport


def _deep_contract(registry: dict, deep_route: str = "gemini-deep") -> dict:
    contract = {
        "question": "gemini-deep adapter test",
        "posture": "lookup",
        "tier": "custom",
        "execution": "external_managed",
        "durability": "canonical_package",
        "scout_route": "demo-probe",
        "resource_envelope": {
            "physical_ceiling": {
                "probe": 1,
                "deep": 1,
                "processor": 0,
                "network_experiment": 0,
                "transport": 20,
                "host_retrieval": 0,
                "local": 0,
                "organizer_pass": 0,
            },
            "external": {
                "metered_ceiling": {
                    "probe": 0,
                    "deep": 1,
                    "processor": 0,
                    "network_experiment": 0,
                    "transport": 0,
                },
                "max_wall_time_seconds": 1200,
                "allowed_endpoint_classes": [],
                "local_file_egress": False,
                "network_experiment_endpoints": [],
                "estimated_spend_usd": {"minimum": 0.0, "maximum": 3.0, "hard_cap": False},
                "raw_storage_bytes": 10 * 1024 * 1024,
            },
            "host": {"context_class": "lean", "admitted_characters": 8000, "estimated_tokens": 2000},
            "local": {"admitted_output_characters": 0, "max_wall_time_seconds": 60, "network_egress": False},
        },
        "stage_permit_map": [
            {
                "stage": "primary_scout",
                "category": "probe",
                "route": "demo-probe",
                "invocations": 1,
                "count": 1,
                "reserved": False,
            },
            {
                "stage": "investigation",
                "category": "deep",
                "route": deep_route,
                "invocations": 1,
                "count": 1,
                "reserved": False,
            },
            {
                "stage": "investigation",
                "category": "transport",
                "route": deep_route,
                "invocations": 20,
                "count": 20,
                "reserved": False,
            },
        ],
        "evidence_floor": {"minimum_load_bearing_claims": 1, "require_raw_artifacts": True},
        "artifact_policy": {"default_retention": "session", "allow_provider_payloads": False},
    }
    contract = normalize_contract(contract)
    records = referenced_provider_records(contract, registry)
    contract["confirmation"] = {
        "confirmed_by": "user",
        "confirmed_at": NOW,
        "card_sha256": contract_card_sha256(contract),
        "registry_sha256": provider_registry_sha256(registry),
        "referenced_records_sha256": provider_records_sha256(records),
    }
    return contract


class GeminiDeepAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        self.registry = enabled_registry_copy("gemini-deep")
        self.contract = _deep_contract(self.registry)
        self.session = Path(self._tempdir.name) / "session"
        create_session(self.session, new_state(self.contract, NOW, self.registry, TEST_ENV))
        self._env_patcher = mock.patch.dict(os.environ, TEST_ENV)
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)

    def attempt_statuses(self, action_id: str) -> list[str]:
        events, errors = read_events(self.session)
        self.assertEqual(errors, [])
        return [
            event.get("initial_status")
            for event in events
            if event.get("event") == "permit_acquired"
            and event.get("action_id") == action_id
            and event.get("initial_status")
        ] + [
            event["status"]
            for event in events
            if event.get("event") == "attempt_status" and event.get("action_id") == action_id
        ]

    def _submit(self, action_id: str = "D1") -> dict:
        return execute_deep_submit(
            self.session,
            action_id,
            "investigation",
            "gemini-deep",
            "what changed in the bounded research task",
            NOW,
            transport=fixture_transport("gemini_deep_submit_accept.json"),
            environ=TEST_ENV,
        )

    def test_submit_request_shape_and_secret_boundary(self) -> None:
        spec = gemini_deep.submit("research question", TEST_ENV)
        body = json.loads(spec.body)
        self.assertEqual(spec.method, "POST")
        self.assertEqual(spec.url, "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(spec.headers["x-goog-api-key"], "test-key")
        self.assertEqual(body["agent"], "deep-research-preview-04-2026")
        self.assertTrue(body["background"])
        self.assertTrue(body["store"])
        self.assertEqual(
            body["agent_config"],
            {
                "type": "deep-research",
                "thinking_summaries": "none",
                "visualization": "off",
                "collaborative_planning": False,
            },
        )
        with self.assertRaises(BoundaryError):
            gemini_deep.submit("research question", {})

    def test_poll_and_job_token_shape(self) -> None:
        accept = (FIXTURES / "gemini_deep_submit_accept.json").read_bytes()
        token = gemini_deep.job_token(accept)
        spec = gemini_deep.poll(token, TEST_ENV)
        self.assertEqual(token, "gemini-interaction-fixture-001")
        self.assertEqual(spec.method, "GET")
        self.assertEqual(spec.url.rsplit("/", 1)[-1], token)
        self.assertEqual(spec.headers["x-goog-api-key"], "test-key")

    def test_extract_success_sanitizes_citations_and_keeps_live_usage_shape(self) -> None:
        fixture = json.loads((FIXTURES / "gemini_deep_poll_terminal_success.json").read_text())
        result = gemini_deep.extract(json.dumps(fixture).encode())
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(
            result.synthesis_text,
            "Sanitized live Gemini Deep Research output excerpt.\n\nAdditional sanitized live report text.",
        )
        self.assertEqual(
            [item["url"] for item in result.citations],
            [
                "https://example.test/live-gemini-wrapper-a",
                "https://example.test/live-gemini-wrapper-b",
            ],
        )
        self.assertEqual(result.usage, {"total_tokens": 1094159})
        self.assertEqual(result.model, fixture["agent"])
        self.assertIsNone(result.cost_usd)
        self.assertEqual(result.kind, "search_synthesis")

    def test_status_table_distinguishes_running_terminal_interactive_and_malformed(self) -> None:
        cases = (
            ("running", json.loads((FIXTURES / "gemini_deep_poll_running.json").read_text()), None),
            ("failed", {"status": "failed", "error": {"message": "failed detail"}}, AdapterTerminalFailure),
            ("cancelled", {"status": "cancelled", "error": {"message": "cancelled detail"}}, AdapterTerminalFailure),
            ("incomplete", {"status": "incomplete", "error": {"message": "incomplete detail"}}, AdapterTerminalFailure),
            ("requires_action", json.loads((FIXTURES / "gemini_deep_poll_requires_action.json").read_text()), AdapterParseError),
            ("malformed", json.loads((FIXTURES / "gemini_deep_poll_malformed_completed.json").read_text()), AdapterParseError),
        )
        for status, payload, expected in cases:
            with self.subTest(status=status):
                if expected is None:
                    self.assertIsNone(gemini_deep.extract(json.dumps(payload).encode()))
                else:
                    with self.assertRaises(expected) as raised:
                        gemini_deep.extract(json.dumps(payload).encode())
                    if expected is AdapterTerminalFailure:
                        self.assertIn(status, str(raised.exception))
                    elif status == "requires_action":
                        self.assertIn("unsupported interactive state", str(raised.exception))

    def test_boundary_success_records_occurrence_citations_spool_and_attempts(self) -> None:
        accepted = self._submit()
        self.assertEqual(accepted["job"], "gemini-deep:gemini-interaction-fixture-001")
        self.assertEqual(self.attempt_statuses("D1"), ["attempted", "accepted"])
        self.assertTrue(Path(accepted["spool_path"]).exists())

        running = execute_deep_poll(
            self.session,
            "D1",
            "T1",
            "investigation",
            "gemini-deep",
            NOW,
            transport=fixture_transport("gemini_deep_poll_running.json"),
            environ=TEST_ENV,
        )
        self.assertEqual(running["status"], "running")
        completed = execute_deep_poll(
            self.session,
            "D1",
            "T2",
            "investigation",
            "gemini-deep",
            NOW,
            transport=fixture_transport("gemini_deep_poll_terminal_success.json"),
            environ=TEST_ENV,
        )
        occurrence = completed["occurrence"]
        self.assertEqual(occurrence["provider_id"], "gemini-deep")
        self.assertEqual(occurrence["action_id"], "D1")
        self.assertEqual(occurrence["request_action_id"], "T2")
        self.assertEqual(occurrence["citation_count"], 2)
        self.assertEqual(occurrence["kind"], "search_synthesis")
        self.assertIsNone(occurrence["cost_usd"])
        self.assertIn("Sanitized live Gemini", occurrence["synthesis_excerpt"])
        self.assertEqual(self.attempt_statuses("D1"), ["attempted", "accepted", "completed"])
        self.assertEqual(self.attempt_statuses("T1"), ["attempted", "accepted", "completed"])
        self.assertEqual(self.attempt_statuses("T2"), ["attempted", "accepted", "completed"])
        state = load_state(self.session)
        self.assertEqual(len(state["retrieval_occurrences"]), 1)
        self.assertNotIn("test-key", (self.session / "provider_spool" / "T2.raw.json").read_text())

    def test_boundary_terminal_failure_consumes_deep_and_poll_actions(self) -> None:
        self._submit()
        with self.assertRaises(BoundaryError):
            execute_deep_poll(
                self.session,
                "D1",
                "T1",
                "investigation",
                "gemini-deep",
                NOW,
                transport=fixture_transport("gemini_deep_poll_terminal_failure.json"),
                environ=TEST_ENV,
            )
        self.assertEqual(self.attempt_statuses("D1"), ["attempted", "accepted", "failed"])
        self.assertEqual(self.attempt_statuses("T1"), ["attempted", "accepted", "completed"])
        self.assertEqual(load_state(self.session)["retrieval_occurrences"], [])

    def test_boundary_requires_action_is_spooled_harvestable_and_cannot_resubmit(self) -> None:
        self._submit()
        with self.assertRaisesRegex(AdapterParseError, "unsupported interactive state"):
            execute_deep_poll(
                self.session,
                "D1",
                "T1",
                "investigation",
                "gemini-deep",
                NOW,
                transport=fixture_transport("gemini_deep_poll_requires_action.json"),
                environ=TEST_ENV,
            )
        self.assertEqual(self.attempt_statuses("D1"), ["attempted", "accepted"])
        self.assertEqual(self.attempt_statuses("T1"), ["attempted", "accepted", "failed"])
        self.assertTrue((self.session / "provider_spool" / "T1.raw.json").exists())
        with self.assertRaisesRegex(BoundaryError, "never.*resubmit"):
            self._submit()

    def test_registry_live_adoption_binds_enabled_gemini_route(self) -> None:
        base = load_provider_registry()
        candidate = next(provider for provider in base["providers"] if provider["id"] == "gemini-deep")
        self.assertTrue(candidate["enabled"])
        self.assertEqual(candidate["adoption_status"], "validated")
        self.assertEqual(candidate["adapter"], "gemini-interactions-deep")
        self.assertEqual(candidate["adapter_version"], "v1")
        self.assertEqual(candidate["action_categories"], ["deep", "transport"])
        self.assertEqual(candidate["stage_capabilities"], ["investigation", "anti_lock_in"])
        self.assertEqual(candidate["request_multiplicity"], {"deep": 1, "transport": 1})
        self.assertEqual(candidate["evidence_capabilities"], {"can_support_claims": False})
        self.assertEqual(candidate["required_env"], ["GEMINI_API_KEY"])
        self.assertFalse(candidate["privacy"]["local_file_egress"])
        self.assertFalse(candidate["privacy"]["zdr"])
        self.assertTrue(candidate["adoption_evidence"])
        self.assertFalse(any("max" in provider["id"] for provider in base["providers"]))
        self.assertIn("paid projects 55 days, free projects 1 day", candidate["storage_rights"]["source"])
        self.assertIn("store=true", candidate["storage_rights"]["source"])
        self.assertEqual(validate_provider_registry(base), [])

    def test_gemini_fixtures_contain_no_credentials(self) -> None:
        for path in FIXTURES.glob("gemini_deep_*.json"):
            text = path.read_text()
            self.assertNotIn("GEMINI_API_KEY", text)
            self.assertNotIn("test-key", text)
            self.assertNotIn("secret", text.lower())


if __name__ == "__main__":
    unittest.main()
