"""Unit tests for the local-only, no-network provider readiness helpers
added for the openai-deep 404 incident:

- providers.adapter_is_bound (item 2): the pre-confirmation card must not
  overclaim readiness -- SKILL.md forbids any network call before
  confirmation, so the card can only tighten what it verifies locally. This
  checks that the resolved adapter module is actually registered.
- providers.effective_adoption_status (item 4): adoption_status is a
  point-in-time claim (docs_verified_at); this derives a "stale" status once
  that claim is older than ADOPTION_STALE_DAYS, without ever mutating the
  registry record itself.

Both are pure functions with no I/O, so every test here is deterministic and
independent of wall-clock time (each test supplies its own explicit `now`).
"""

from __future__ import annotations

import argparse
import unittest
from datetime import date, datetime, timedelta, timezone

from research_harness.providers import (
    ADOPTION_STALE_DAYS,
    adapter_is_bound,
    effective_adoption_status,
    load_provider_registry,
)
from scripts import research_state


class AdapterIsBoundTests(unittest.TestCase):
    def test_registered_v2_route_is_bound(self) -> None:
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "perplexity-chat-completions",
            "adapter_version": "v1",
        }
        self.assertTrue(adapter_is_bound(provider))

    def test_unregistered_adapter_is_not_bound(self) -> None:
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "does-not-exist",
            "adapter_version": "v99",
        }
        self.assertFalse(adapter_is_bound(provider))

    def test_unregistered_adapter_version_is_not_bound(self) -> None:
        # Same adapter name, wrong/stale version -- a route left pointing at
        # a version that was since renamed or removed from ADAPTERS.
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "openai-deep-responses",
            "adapter_version": "v99",
        }
        self.assertFalse(adapter_is_bound(provider))

    def test_non_v2_bindings_are_trivially_bound(self) -> None:
        # These bindings never look themselves up in ADAPTERS at all (see
        # boundary._bound_route), so there is nothing local to fail here.
        for binding in ("no_network_demo", "host_native_observed", "local", "legacy_unbound"):
            with self.subTest(binding=binding):
                provider = {
                    "execution_binding": binding,
                    "adapter": "unbound",
                    "adapter_version": "unbound",
                }
                self.assertTrue(adapter_is_bound(provider))

    def test_every_enabled_v2_route_in_the_real_registry_is_bound(self) -> None:
        registry = load_provider_registry()
        for provider in registry["providers"]:
            if provider.get("enabled") and provider.get("execution_binding") == "v2_request_boundary":
                with self.subTest(provider=provider["id"]):
                    self.assertTrue(adapter_is_bound(provider))


class EffectiveAdoptionStatusTests(unittest.TestCase):
    def test_fresh_validated_status_is_unchanged(self) -> None:
        provider = {"adoption_status": "validated", "docs_verified_at": "2026-07-01"}
        self.assertEqual(effective_adoption_status(provider, "2026-07-10T00:00:00Z"), "validated")

    def test_fresh_baseline_status_is_unchanged(self) -> None:
        provider = {"adoption_status": "baseline", "docs_verified_at": "2026-07-01"}
        self.assertEqual(effective_adoption_status(provider, "2026-07-10T00:00:00Z"), "baseline")

    def test_status_exactly_at_threshold_is_not_stale(self) -> None:
        verified = date(2026, 1, 1)
        at_threshold = verified + timedelta(days=ADOPTION_STALE_DAYS)
        provider = {"adoption_status": "validated", "docs_verified_at": verified.isoformat()}
        now = f"{at_threshold.isoformat()}T00:00:00Z"
        self.assertEqual(effective_adoption_status(provider, now), "validated")

    def test_status_one_day_past_threshold_is_stale(self) -> None:
        verified = date(2026, 1, 1)
        just_past = verified + timedelta(days=ADOPTION_STALE_DAYS + 1)
        provider = {"adoption_status": "validated", "docs_verified_at": verified.isoformat()}
        now = f"{just_past.isoformat()}T00:00:00Z"
        self.assertEqual(effective_adoption_status(provider, now), "stale")

    def test_status_outside_baseline_or_validated_is_never_marked_stale(self) -> None:
        # Staleness only ever narrows an EXISTING positive adoption claim; it
        # must never invent one for a status like "not_tested".
        provider = {"adoption_status": "not_tested", "docs_verified_at": "2020-01-01"}
        self.assertEqual(effective_adoption_status(provider, "2026-08-26T00:00:00Z"), "not_tested")

    def test_missing_docs_verified_at_is_returned_unchanged(self) -> None:
        provider = {"adoption_status": "validated"}
        self.assertEqual(effective_adoption_status(provider, "2026-08-26T00:00:00Z"), "validated")

    def test_unparseable_docs_verified_at_is_returned_unchanged(self) -> None:
        provider = {"adoption_status": "validated", "docs_verified_at": "not-a-date"}
        self.assertEqual(effective_adoption_status(provider, "2026-08-26T00:00:00Z"), "validated")

    def test_does_not_mutate_the_input_provider(self) -> None:
        provider = {"adoption_status": "validated", "docs_verified_at": "2020-01-01"}
        snapshot = dict(provider)
        effective_adoption_status(provider, "2026-08-26T00:00:00Z")
        self.assertEqual(provider, snapshot)


class CardProviderStateTests(unittest.TestCase):
    """research_state._card_provider_state is the exact function behind the
    incident's misleading `openai-deep[rank=3, ready]` card label. A real
    registry overlay cannot construct an "unbound" scenario for an enabled
    route (adapter/adapter_version are immutable-for-enabled-providers
    overlay fields -- see providers._merge_overlay), so this exercises the
    pure function directly with a synthetic record instead."""

    def test_missing_credential_takes_priority(self) -> None:
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "does-not-exist",
            "adapter_version": "v1",
        }
        self.assertEqual(
            research_state._card_provider_state(provider, ["SOME_API_KEY"]), "missing-key"
        )

    def test_unregistered_adapter_is_unbound_not_ready(self) -> None:
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "does-not-exist",
            "adapter_version": "v1",
        }
        self.assertEqual(research_state._card_provider_state(provider, []), "unbound")

    def test_bound_and_credentialed_is_locally_verified(self) -> None:
        provider = {
            "execution_binding": "v2_request_boundary",
            "adapter": "openai-deep-responses",
            "adapter_version": "v1",
        }
        self.assertEqual(research_state._card_provider_state(provider, []), "locally-verified")

    def test_real_card_never_prints_the_overclaiming_ready_label(self) -> None:
        # The literal regression: the card must never again claim "ready" --
        # a word this incident showed readers interpret as "will work".
        payload, code = research_state.command_card(
            argparse.Namespace(
                question="regression check",
                posture="decision",
                profiles=None,
                registry_overlay=None,
            )
        )
        self.assertEqual(code, 0)
        states = {item["state"] for item in payload["d1_candidates"] + payload["search_candidates"]}
        self.assertNotIn("ready", states)
        self.assertTrue(states <= {"locally-verified", "missing-key", "unbound"})


class ProvidersCommandWiringTests(unittest.TestCase):
    """Light integration check that command_providers actually calls
    effective_adoption_status for its new field, rather than a hardcoded
    date-dependent expectation (which would be flaky as real time passes)."""

    def test_adoption_status_effective_field_matches_the_pure_function(self) -> None:
        payload, code = research_state.command_providers(argparse.Namespace(registry_overlay=None))
        self.assertEqual(code, 0)
        registry = load_provider_registry()
        by_id = {provider["id"]: provider for provider in registry["providers"]}
        for item in payload["providers"]:
            provider = by_id[item["id"]]
            self.assertIn("adoption_status_effective", item)
            self.assertIn("docs_verified_at", item)
            # Recomputed with a `now` sourced the same way command_providers
            # sources it (real wall clock) -- accepting the same
            # vanishingly-small midnight-boundary race any wall-clock-based
            # test has, rather than hardcoding an expected stale/not-stale
            # verdict that would silently go wrong as real time passes.
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            self.assertEqual(
                item["adoption_status_effective"],
                effective_adoption_status(provider, now),
            )


if __name__ == "__main__":
    unittest.main()
