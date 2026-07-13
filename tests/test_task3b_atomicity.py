from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from research_harness import boundary
from research_harness.boundary import BoundaryError, RequestSpec, execute_probe
from research_harness.quota import QuotaError, _append_permit_unlocked, acquire_permits
from research_harness.state import new_state, validate_state_document
from research_harness.storage import apply_state_patch, create_session, load_state, read_events, session_lock
from scripts.research_state import build_parser, command_deep_pending
from tests.helpers import (
    NOW,
    append_valid_test_event_line,
    confirmed_demo_contract,
    enabled_registry_copy,
)
from research_harness.validation import validate_session


FIXTURES = Path(__file__).with_name("fixtures")


class Task3bAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.registry = enabled_registry_copy("openalex")
        self.session = Path(self.tempdir.name) / "session"
        contract = confirmed_demo_contract(route="openalex", registry=self.registry, probe_ceiling=2)
        create_session(self.session, new_state(contract, NOW, self.registry, {"OPENALEX_API_KEY": "secret-key"}))
        self.env_patch = mock.patch.dict("os.environ", {"OPENALEX_API_KEY": "secret-key"})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def transport(self, seen: list[object]):
        payload = (FIXTURES / "openalex_success.json").read_bytes()

        def send(spec):
            seen.append(spec)
            return 200, payload

        return send

    def _fresh_probe_session(self, name: str) -> Path:
        session = Path(self.tempdir.name) / name
        state = new_state(
            confirmed_demo_contract(route="openalex", registry=self.registry),
            NOW,
            self.registry,
            {"OPENALEX_API_KEY": "secret-key"},
        )
        create_session(session, state)
        execute_probe(
            session,
            "P1",
            "primary_scout",
            "openalex",
            "adversarial occurrence",
            NOW,
            transport=self.transport([]),
            environ={"OPENALEX_API_KEY": "secret-key"},
        )
        return session

    def _forge_legacy_permit(self, session: Path, action_id: str, category: str) -> None:
        append_valid_test_event_line(
            session,
            {
                "event": "permit_acquired",
                "at": NOW,
                "action_id": action_id,
                "stage": f"legacy_{category}",
                "category": category,
                "route": "host-web" if category == "host_retrieval" else category,
                "invocation_index": 1,
                "count": 1,
            },
        )

    def _session_with_marker(self, marker: str | None) -> Path:
        session = Path(self.tempdir.name) / f"marker-{marker or 'none'}"
        state = new_state(
            confirmed_demo_contract(route="openalex", registry=self.registry),
            NOW,
            self.registry,
            {"OPENALEX_API_KEY": "secret-key"},
        )
        if marker is None:
            state["session"].pop("contract_semantics")
        else:
            state["session"]["contract_semantics"] = marker
        create_session(session, state)
        return session

    def test_public_surfaces_do_not_accept_caller_fingerprint(self) -> None:
        self.assertNotIn("fingerprint", inspect.signature(acquire_permits).parameters)
        self.assertNotIn("--fingerprint", build_parser().format_help())
        subparsers = next(action for action in build_parser()._actions if action.dest == "command")
        permit_parser = subparsers.choices["permit"]
        category = next(action for action in permit_parser._actions if action.dest == "category")
        self.assertEqual(category.choices, ["host_retrieval", "local", "organizer_pass"])
        self.assertIn("non-network/host-managed", permit_parser.description)

    def test_writer_rejects_boundary_fields_on_legacy_permits(self) -> None:
        for field_kwargs in (
            {"fingerprint": "0" * 64},
            {"query_hash": "0" * 64},
            {"initial_status": "attempted"},
        ):
            with self.subTest(field_kwargs=field_kwargs), session_lock(self.session):
                with self.assertRaises(QuotaError):
                    _append_permit_unlocked(
                        self.session,
                        "L1",
                        "local_applicability",
                        "local",
                        "local",
                        1,
                        1,
                        NOW,
                        **field_kwargs,
                    )
        events, errors = read_events(self.session)
        self.assertEqual(errors, [])
        self.assertFalse(any(event.get("event") == "permit_acquired" for event in events))

    def test_new_state_uses_v3_and_unknown_marker_fails_closed(self) -> None:
        state = load_state(self.session)
        self.assertEqual(state["session"]["contract_semantics"], "pure_trigger_v3")
        state["session"]["contract_semantics"] = "pure_trigger_future"
        self.assertIn("session contract_semantics is invalid", validate_state_document(state))

    def test_legacy_markers_do_not_infer_atomic_schema_from_optional_fields(self) -> None:
        for marker in ("pure_trigger_v2", "pure_trigger_v1", None):
            with self.subTest(marker=marker):
                session = self._session_with_marker(marker)
                append_valid_test_event_line(
                    session,
                    {
                        "event": "permit_acquired",
                        "at": NOW,
                        "action_id": "L-probe",
                        "stage": "primary_scout",
                        "category": "probe",
                        "route": "openalex",
                        "invocation_index": 1,
                        "count": 1,
                        "initial_status": "attempted",
                        "fingerprint": "not-a-v3-fingerprint",
                        "query_hash": "not-a-v3-query-hash",
                    },
                )
                append_valid_test_event_line(
                    session,
                    {
                        "event": "attempt_status",
                        "at": NOW,
                        "action_id": "L-probe",
                        "from_status": "acquired",
                        "status": "attempted",
                    },
                )
                codes = {issue.code for issue in validate_session(session, check_report=False).errors}
                self.assertNotIn("quota.boundary_shape", codes)
                self.assertNotIn("quota.boundary_fingerprint", codes)
                self.assertNotIn("quota.deep_query_hash", codes)

    def test_legacy_markers_ignore_v3_terminal_poll_event_hash(self) -> None:
        for marker in ("pure_trigger_v2", "pure_trigger_v1", None):
            with self.subTest(marker=marker):
                session = self._session_with_marker(marker)
                state = load_state(session)
                apply_state_patch(
                    session,
                    [{
                        "op": "add",
                        "path": "/retrieval_occurrences/-",
                        "value": {
                            "id": "R-legacy",
                            "provider_id": "openalex",
                            "action_id": "legacy-action",
                            "terminal_poll_event_hash": "0" * 64,
                        },
                    }],
                    state["session"]["revision"],
                    NOW,
                )
                report = validate_session(session, check_report=False)
                self.assertNotIn(
                    "occurrence.terminal_poll_event_hash",
                    {issue.code for issue in report.errors},
                )

    def test_fingerprint_covers_redaction_metadata_and_binary_body(self) -> None:
        base = RequestSpec(
            "POST",
            "https://example.test/search?safe=1&token=secret#fragment-a",
            {"Authorization": "Bearer one", "X-Trace": "trace-a"},
            b"\x00\xffbody",
            1.0,
            ("token",),
        )
        self.assertEqual(
            boundary._request_fingerprint(
                RequestSpec(
                    base.method,
                    base.url.replace("fragment-a", "fragment-b"),
                    base.headers,
                    base.body,
                    base.timeout_s,
                    ("token",),
                )
            ),
            boundary._request_fingerprint(base),
        )
        self.assertEqual(
            boundary._request_fingerprint(
                RequestSpec(base.method, base.url, {**base.headers, "Authorization": "Bearer two"}, base.body, 1.0, ("token",))
            ),
            boundary._request_fingerprint(base),
        )
        self.assertNotEqual(
            boundary._request_fingerprint(RequestSpec(base.method, base.url, {"X-Trace": "trace-a"}, base.body, 1.0, ("token",))),
            boundary._request_fingerprint(base),
        )
        self.assertNotEqual(
            boundary._request_fingerprint(RequestSpec(base.method, base.url, base.headers, base.body, 2.0, ("token",))),
            boundary._request_fingerprint(base),
        )
        self.assertNotEqual(
            boundary._request_fingerprint(RequestSpec(base.method, base.url, base.headers, base.body, 1.0, ("token", "other"))),
            boundary._request_fingerprint(base),
        )
        self.assertNotEqual(
            boundary._request_fingerprint(RequestSpec(base.method, base.url, base.headers, b"\x00\xfebody", 1.0, ("token",))),
            boundary._request_fingerprint(base),
        )

    def test_validator_rejects_forged_boundary_hash_fields(self) -> None:
        append_valid_test_event_line(
            self.session,
            {
                "event": "permit_acquired",
                "at": NOW,
                "action_id": "P2",
                "stage": "primary_scout",
                "category": "probe",
                "route": "openalex",
                "invocation_index": 1,
                "count": 1,
                "initial_status": "attempted",
                "fingerprint": "not-a-hash",
                "query_hash": "also-not-a-hash",
            },
        )
        codes = {issue.code for issue in validate_session(self.session, check_report=False).errors}
        self.assertIn("quota.boundary_fingerprint", codes)
        self.assertIn("quota.deep_query_hash", codes)

    def test_validator_requires_deep_query_hash(self) -> None:
        append_valid_test_event_line(
            self.session,
            {
                "event": "permit_acquired",
                "at": NOW,
                "action_id": "D2",
                "stage": "investigation",
                "category": "deep",
                "route": "openalex",
                "invocation_index": 1,
                "count": 1,
                "initial_status": "attempted",
                "fingerprint": "0" * 64,
                "query_hash": "0" * 63,
            },
        )
        codes = {issue.code for issue in validate_session(self.session, check_report=False).errors}
        self.assertIn("quota.deep_query_hash", codes)

    def test_boundary_reserves_actual_spec_and_journals_attempted_atomically(self) -> None:
        sent: list[object] = []
        result = execute_probe(
            self.session,
            "P1",
            "primary_scout",
            "openalex",
            "atomic request",
            NOW,
            transport=self.transport(sent),
            environ={"OPENALEX_API_KEY": "secret-key"},
        )
        events, errors = read_events(self.session)
        self.assertEqual(errors, [])
        permit = next(event for event in events if event.get("event") == "permit_acquired")
        self.assertEqual(permit["initial_status"], "attempted")
        self.assertEqual(permit["fingerprint"], boundary._request_fingerprint(sent[0]))
        self.assertEqual(permit["query_hash"], boundary.sha256_hex("atomic request"))
        self.assertEqual([event["event"] for event in events if event.get("action_id") == "P1"], [
            "permit_acquired",
            "attempt_status",
            "attempt_status",
        ])
        serialized = json.dumps(events)
        self.assertNotIn("secret-key", serialized)
        self.assertNotIn("secret-key", (self.session / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("secret-key", result["spool_path"])
        report = validate_session(self.session, check_report=False)
        self.assertEqual(report.errors, ())
        self.assertTrue(report.integrity_ok)

    def test_occurrence_binds_exact_request_action_and_hashes(self) -> None:
        sent: list[object] = []
        result = execute_probe(
            self.session,
            "P1",
            "primary_scout",
            "openalex",
            "bound occurrence",
            NOW,
            transport=self.transport(sent),
            environ={"OPENALEX_API_KEY": "secret-key"},
        )
        occurrence = result["occurrence"]
        self.assertEqual(occurrence["request_action_id"], "P1")
        state = load_state(self.session)
        apply_state_patch(
            self.session,
            [
                {
                    "op": "replace",
                    "path": "/retrieval_occurrences/0/request_action_id",
                    "value": "missing",
                }
            ],
            state["session"]["revision"],
            NOW,
        )
        codes = {issue.code for issue in validate_session(self.session, check_report=False).errors}
        self.assertIn("occurrence.request_action_missing", codes)

    def test_occurrence_rejects_fingerprint_and_query_hash_fallbacks(self) -> None:
        sent: list[object] = []
        execute_probe(
            self.session,
            "P1",
            "primary_scout",
            "openalex",
            "tampered occurrence",
            NOW,
            transport=self.transport(sent),
            environ={"OPENALEX_API_KEY": "secret-key"},
        )
        state = load_state(self.session)
        apply_state_patch(
            self.session,
            [
                {
                    "op": "replace",
                    "path": "/retrieval_occurrences/0/fingerprint",
                    "value": "0" * 64,
                },
                {
                    "op": "replace",
                    "path": "/retrieval_occurrences/0/query_hash",
                    "value": "f" * 64,
                },
            ],
            state["session"]["revision"],
            NOW,
        )
        codes = {issue.code for issue in validate_session(self.session, check_report=False).errors}
        self.assertIn("occurrence.fingerprint", codes)
        self.assertIn("occurrence.query_hash", codes)

    def test_v3_occurrence_lineage_rejects_missing_hash_route_category_lifecycle_and_duplicates(self) -> None:
        mutations = {
            "missing request_action_id": (
                [{"op": "remove", "path": "/retrieval_occurrences/0/request_action_id"}],
                "occurrence.request_action_id",
            ),
            "wrong request_action_id": (
                [{"op": "replace", "path": "/retrieval_occurrences/0/request_action_id", "value": "missing"}],
                "occurrence.request_action_missing",
            ),
            "wrong fingerprint": (
                [{"op": "replace", "path": "/retrieval_occurrences/0/fingerprint", "value": "0" * 64}],
                "occurrence.fingerprint",
            ),
            "wrong query hash": (
                [{"op": "replace", "path": "/retrieval_occurrences/0/query_hash", "value": "f" * 64}],
                "occurrence.query_hash",
            ),
            "wrong route": (
                [{"op": "replace", "path": "/retrieval_occurrences/0/provider_id", "value": "host"}],
                "occurrence.route",
            ),
        }
        for name, (operations, expected_code) in mutations.items():
            with self.subTest(name=name):
                session = self._fresh_probe_session(f"occurrence-{name.replace(' ', '-')}")
                state = load_state(session)
                apply_state_patch(session, operations, state["session"]["revision"], NOW)
                report = validate_session(session, check_report=False)
                self.assertFalse(report.integrity_ok, report.to_dict())
                self.assertIn(expected_code, {issue.code for issue in report.errors})

        for side in ("logical", "request"):
            for category in ("local", "host_retrieval", "organizer_pass"):
                with self.subTest(side=side, category=category):
                    session = self._fresh_probe_session(f"occurrence-{side}-{category}")
                    legacy_id = f"L-{side}-{category}"
                    self._forge_legacy_permit(session, legacy_id, category)
                    path = (
                        "/retrieval_occurrences/0/action_id"
                        if side == "logical"
                        else "/retrieval_occurrences/0/request_action_id"
                    )
                    state = load_state(session)
                    apply_state_patch(
                        session,
                        [{"op": "replace", "path": path, "value": legacy_id}],
                        state["session"]["revision"],
                        NOW,
                    )
                    report = validate_session(session, check_report=False)
                    codes = {issue.code for issue in report.errors}
                    self.assertFalse(report.integrity_ok, report.to_dict())
                    self.assertIn("occurrence.category", codes)

        session = self._fresh_probe_session("occurrence-lifecycle")
        self._forge_legacy_permit(session, "L-lifecycle", "local")
        state = load_state(session)
        apply_state_patch(
            session,
            [{"op": "replace", "path": "/retrieval_occurrences/0/request_action_id", "value": "L-lifecycle"}],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session, check_report=False)
        self.assertFalse(report.integrity_ok, report.to_dict())
        self.assertIn("occurrence.request_lifecycle", {issue.code for issue in report.errors})

        session = self._fresh_probe_session("occurrence-duplicate")
        occurrence = load_state(session)["retrieval_occurrences"][0]
        state = load_state(session)
        apply_state_patch(
            session,
            [{
                "op": "add",
                "path": "/retrieval_occurrences/-",
                "value": {**occurrence, "id": "occ-P1-copy"},
            }],
            state["session"]["revision"],
            NOW,
        )
        report = validate_session(session, check_report=False)
        codes = {issue.code for issue in report.errors}
        self.assertFalse(report.integrity_ok, report.to_dict())
        self.assertIn("occurrence.request_duplicate", codes)
        self.assertIn("occurrence.logical_duplicate", codes)

    def test_deep_pending_help_explains_consumed_unpollable_manual_recovery(self) -> None:
        subparsers = next(action for action in build_parser()._actions if action.dest == "command")
        help_text = " ".join(subparsers.choices["deep-pending"].format_help().lower().split())
        for phrase in ("attempted action with no token", "consumed=true", "pollable=false", "manual inspection"):
            self.assertIn(phrase, help_text)

    def test_submit_transport_crash_is_consumed_and_not_pollable(self) -> None:
        from research_harness.boundary import execute_deep_poll, execute_deep_submit
        from tests.test_async_boundary import _deep_contract

        session = Path(self.tempdir.name) / "async-crash"
        registry = enabled_registry_copy("perplexity")
        contract = _deep_contract(registry)
        perplexity_env = mock.patch.dict("os.environ", {"PERPLEXITY_API_KEY": "secret-key"})
        perplexity_env.start()
        self.addCleanup(perplexity_env.stop)
        state = new_state(contract, NOW, registry, {"PERPLEXITY_API_KEY": "secret-key"})
        create_session(session, state)
        sent: list[object] = []
        payload = (FIXTURES / "perplexity_deep_submit_accept.json").read_bytes()

        def transport(spec):
            sent.append(spec)
            return 200, payload

        def crash_spool(*args, **kwargs):
            raise RuntimeError("crash after transport")

        with mock.patch.object(boundary, "_spool_raw", crash_spool):
            with self.assertRaises(RuntimeError):
                execute_deep_submit(
                    session,
                    "D1",
                    "investigation",
                    "perplexity",
                    "crash after transport",
                    NOW,
                    transport=transport,
                    environ={"PERPLEXITY_API_KEY": "secret-key"},
                )
        pending, code = command_deep_pending(Namespace(session=str(session)))
        self.assertEqual(code, 0)
        self.assertEqual(pending["pending"][0]["status"], "attempted")
        self.assertTrue(pending["pending"][0]["consumed"])
        self.assertFalse(pending["pending"][0]["pollable"])
        self.assertIsNone(pending["pending"][0]["job"])
        with self.assertRaises(BoundaryError):
            execute_deep_submit(
                session,
                "D1",
                "investigation",
                "perplexity",
                "crash after transport",
                NOW,
                transport=transport,
                environ={"PERPLEXITY_API_KEY": "secret-key"},
            )
        with self.assertRaises(BoundaryError):
            execute_deep_poll(
                session,
                "D1",
                "T1",
                "investigation",
                "perplexity",
                NOW,
                transport=transport,
                environ={"PERPLEXITY_API_KEY": "secret-key"},
            )
        self.assertEqual(len(sent), 1)

    def test_duplicate_execute_sends_exactly_once(self) -> None:
        sent: list[object] = []
        execute_probe(
            self.session,
            "P1",
            "primary_scout",
            "openalex",
            "duplicate request",
            NOW,
            transport=self.transport(sent),
            environ={"OPENALEX_API_KEY": "secret-key"},
        )
        with self.assertRaises(BoundaryError):
            execute_probe(
                self.session,
                "P1",
                "primary_scout",
                "openalex",
                "duplicate request",
                NOW,
                transport=self.transport(sent),
                environ={"OPENALEX_API_KEY": "secret-key"},
            )
        self.assertEqual(len(sent), 1)

    def test_crash_after_reservation_consumes_action_without_send_or_retry(self) -> None:
        sent: list[object] = []
        original = boundary._reserve_boundary_action_unlocked

        def crash_after_reservation(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("simulated crash")

        with mock.patch.object(boundary, "_reserve_boundary_action_unlocked", crash_after_reservation):
            with self.assertRaises(RuntimeError):
                execute_probe(
                    self.session,
                    "P1",
                    "primary_scout",
                    "openalex",
                    "crash after reserve",
                    NOW,
                    transport=self.transport(sent),
                    environ={"OPENALEX_API_KEY": "secret-key"},
                )
        with self.assertRaises(BoundaryError):
            execute_probe(
                self.session,
                "P1",
                "primary_scout",
                "openalex",
                "crash after reserve",
                NOW,
                transport=self.transport(sent),
                environ={"OPENALEX_API_KEY": "secret-key"},
            )
        self.assertEqual(sent, [])

    def test_separate_boundary_permit_is_rejected_but_legacy_permit_is_retained(self) -> None:
        for category in ("probe", "deep", "processor", "network_experiment", "transport"):
            with self.subTest(category=category), self.assertRaises(QuotaError):
                acquire_permits(
                    self.session,
                    "P1",
                    "primary_scout",
                    category,
                    "openalex",
                    1,
                    NOW,
                )
        acquire_permits(
            self.session,
            "L1",
            "local_applicability",
            "local",
            "local",
            1,
            NOW,
        )
        events, errors = read_events(self.session)
        self.assertEqual(errors, [])
        legacy = next(event for event in events if event.get("action_id") == "L1")
        self.assertNotIn("fingerprint", legacy)
        self.assertNotIn("initial_status", legacy)

    def test_preexisting_legacy_action_is_rejected_before_transport(self) -> None:
        acquire_permits(
            self.session,
            "P1",
            "local_applicability",
            "local",
            "local",
            1,
            NOW,
        )
        sent: list[object] = []
        with self.assertRaises(BoundaryError):
            execute_probe(
                self.session,
                "P1",
                "primary_scout",
                "openalex",
                "preexisting action",
                NOW,
                transport=self.transport(sent),
                environ={"OPENALEX_API_KEY": "secret-key"},
            )
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
