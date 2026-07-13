"""v2 request boundary: build and reserve one physical request atomically.

Schema status: LOCKED v1 (2026-07-11). The occurrence shape and the adapter
protocol (sync build/parse; async submit/job_token/poll/extract) below are
stable — they have been exercised by three request shapes (sync GET, sync
POST, async submit/poll) across 12 live routes with fail-closed validators
and typed failure modes. Breaking changes require a version bump and a
migration note, not a silent field-list edit.

Design rules (from the v2 decisions ledger):

- One boundary action, one physical request. A failed or uncertain attempt
  consumes the boundary action/request count; nothing here refunds anything.
- Raw provider output is preserved verbatim in the session's provider spool
  before any parsing — parse failures never destroy paid bytes.
- The boundary writes retrieval occurrences itself (code provenance). Search
  occurrences are not canonical sources and never support claims directly; the
  Organizer promotes and fetches sources separately.
- Credentials never enter state, events, spool filenames, or fingerprints.
"""

from __future__ import annotations

import json
import os
import socket
import hashlib
import urllib.error
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from ._canon import sha256_hex
from .quota import QuotaError, _record_attempt_status_unlocked, _reserve_boundary_action_unlocked
from .storage import (
    _apply_boundary_patch_unlocked,
    _atomic_write_bytes_unlocked,
    _load_state_unlocked,
    _read_events_unlocked,
    _recover_session_unlocked,
    session_lock,
)

SPOOL_DIR = "provider_spool"
SYNTHESIS_EXCERPT_LIMIT = 4000
CITATION_LIMIT = 40


class BoundaryError(RuntimeError):
    """The boundary refused or failed to execute a physical request."""


class AdapterParseError(BoundaryError):
    """The provider responded, but the payload does not match the adapter contract."""


class AdapterTerminalFailure(BoundaryError):
    """An async job reached a well-formed provider-reported terminal failure.

    Distinct from AdapterParseError: the payload is NOT malformed (the
    provider clearly says the job failed), so the boundary can confidently
    fail the deep action instead of leaving it harvestable.
    """


@dataclass(frozen=True)
class RequestSpec:
    method: str
    url: str
    headers: dict[str, str]
    body: bytes
    timeout_s: float
    sensitive_query_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedResult:
    synthesis_text: str
    citations: list[dict[str, Any]]
    cost_usd: Optional[float]
    usage: dict[str, Any]
    model: str
    kind: str = "search_synthesis"  # search_synthesis / result_listing / paper_listing / record_fetch


def _adapters() -> dict[str, dict[str, Any]]:
    # Function-level import: adapter modules import RequestSpec/ParsedResult
    # from this module, so the registry loads lazily to break the cycle.
    from .adapters import ADAPTERS

    return ADAPTERS


# ── Transport ────────────────────────────────────────────────────────────────

Transport = Callable[[RequestSpec], tuple[int, bytes]]


def _request_fingerprint(spec: RequestSpec) -> str:
    """Hash the actual request while excluding credential-bearing values."""

    parsed = urllib.parse.urlsplit(spec.url)
    sensitive = {key.casefold() for key in spec.sensitive_query_keys}
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_query = urllib.parse.urlencode(
        [(key, "[REDACTED]" if key.casefold() in sensitive else value) for key, value in pairs]
    )
    redacted_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, redacted_query, "")
    )

    def is_secret_header(name: str) -> bool:
        lowered = name.casefold()
        return (
            lowered == "authorization"
            or lowered in {"cookie", "set-cookie", "proxy-authorization"}
            or "api-key" in lowered
            or lowered.endswith("-token")
            or lowered.endswith("_token")
        )

    headers = {
        name.casefold(): "[REDACTED]" if is_secret_header(name) else value
        for name, value in sorted(spec.headers.items(), key=lambda item: item[0].casefold())
    }

    return sha256_hex(
        {
            "method": spec.method.upper(),
            "url": redacted_url,
            "headers": headers,
            "timeout_s": spec.timeout_s,
            "sensitive_query_keys": sorted(sensitive),
            "body_sha256": hashlib.sha256(spec.body).hexdigest(),
        }
    )


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _urllib_transport(spec: RequestSpec) -> tuple[int, bytes]:
    # body=b"" means "no body": pass None so a GET stays truly bodyless
    # (data=b"" would still attach Content-Length/Content-Type headers).
    request = urllib.request.Request(
        spec.url, data=spec.body or None, headers=spec.headers, method=spec.method
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    with opener.open(request, timeout=spec.timeout_s) as response:
        return response.status, response.read()


# ── Execution ────────────────────────────────────────────────────────────────


def _spool_raw(session_dir: Path, action_id: str, payload: bytes) -> Path:
    spool = session_dir / SPOOL_DIR
    if spool.exists():
        if spool.is_symlink() or not spool.is_dir():
            raise BoundaryError("provider spool path is not a safe directory")
    else:
        spool.mkdir(mode=0o700)
    path = spool / f"{action_id}.raw.json"
    _atomic_write_bytes_unlocked(path, payload)
    return path


def _deep_action_lookup(events: list[dict[str, Any]], action_id: str) -> tuple[dict[str, Any], str]:
    """Look up an already-submitted deep action and its current attempt status.

    This requires the action to already be marked attempted (it must have gone
    through execute_deep_submit), and returns the latest status instead of
    refusing a re-visit. A deep action is legitimately revisited by every poll
    and by deep-timeout.
    """

    permits = [
        event
        for event in events
        if event.get("event") == "permit_acquired" and event.get("action_id") == action_id
    ]
    if len(permits) != 1:
        raise BoundaryError(f"action {action_id} has no unique acquired permit")
    statuses = [
        event["status"]
        for event in events
        if event.get("event") == "attempt_status" and event.get("action_id") == action_id
    ]
    permit = permits[0]
    current = statuses[-1] if statuses else permit.get("initial_status", "acquired")
    if current == "acquired":
        raise BoundaryError(
            f"deep action {action_id} has not been submitted; "
            "no poll request count was consumed; do not resubmit the deep action"
        )
    if current == "attempted":
        raise BoundaryError(
            f"deep action {action_id} consumed=true; request count={permit.get('count')}; "
            "pollable=false; no token; manual inspection required; "
            "never retry or resubmit the same action"
        )
    return permit, current


def _job_token_for(events: list[dict[str, Any]], action_id: str) -> str:
    """Recover the bare provider-native job token from the ORIGINAL submit's
    accepted event (details {"job": "provider:token"}). A resume's accepted
    event carries {"resume": true} instead of "job", so the first match here
    is always the original submission regardless of how many times the
    action has since been resumed."""

    for event in events:
        if (
            event.get("event") == "attempt_status"
            and event.get("action_id") == action_id
            and event.get("status") == "accepted"
        ):
            details = event.get("details") or {}
            job = details.get("job")
            if isinstance(job, str) and ":" in job:
                return job.partition(":")[2]
    raise BoundaryError(
        f"deep action {action_id} has no recorded job token; no poll request count was consumed; "
        "manual inspection required; never resubmit the same deep action"
    )


def _deep_query_hash(events: list[dict[str, Any]], action_id: str) -> str:
    """Recover the query hash journaled at submit time (the "attempted" event
    happens exactly once per deep action, so this is unambiguous)."""

    for event in events:
        if (
            event.get("event") == "permit_acquired"
            and event.get("action_id") == action_id
            and event.get("initial_status") == "attempted"
        ):
            query_hash = event.get("query_hash")
            if isinstance(query_hash, str) and query_hash:
                return query_hash
    raise BoundaryError(f"deep action {action_id} has no recorded query hash")


def _first_status_at(events: list[dict[str, Any]], action_id: str, status: str) -> str:
    for event in events:
        if (
            event.get("event") == "attempt_status"
            and event.get("action_id") == action_id
            and event.get("status") == status
        ):
            at = event.get("at")
            if isinstance(at, str) and at:
                return at
    raise BoundaryError(f"action {action_id} has no {status} event")


def _parse_timestamp(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise BoundaryError(f"timestamp is not ISO-8601: {value!r}") from exc


def _elapsed_seconds(earlier: str, later: str) -> float:
    return (_parse_timestamp(later) - _parse_timestamp(earlier)).total_seconds()


def _bound_route(state: dict[str, Any], route: str, *, mode: str) -> dict[str, Any]:
    """Resolve and bind a route, refusing any transport-mode mismatch.

    `mode` is "sync" for execute_probe or "async" for the deep submit/poll
    path. A route whose registry transport.mode disagrees is refused here —
    this is the one place that keeps the sync and async boundaries from
    silently cross-wiring (an async-only adapter used as if it returned a
    result inline, or vice versa).
    """

    provider = next(
        (item for item in state["capabilities"]["providers"] if item.get("id") == route),
        None,
    )
    if provider is None or provider.get("enabled") is not True:
        raise BoundaryError(f"route {route} is not enabled in the capability snapshot")
    binding = provider.get("execution_binding")
    if binding not in {"v2_request_boundary", "no_network_demo"}:
        raise BoundaryError(f"route {route} is not bound to the v2 request boundary")
    transport_mode = provider.get("transport", {}).get("mode")
    if transport_mode != mode:
        raise BoundaryError(
            f"route {route} transport mode is {transport_mode!r}; this path requires {mode!r}"
        )
    preflight = next(
        (item for item in state["capabilities"]["preflight"] if item.get("provider_id") == route),
        None,
    )
    if preflight is None or preflight.get("ready") is not True:
        raise BoundaryError(f"route {route} preflight is not ready")
    if binding == "no_network_demo":
        return {**provider, "_adapter_key": None}
    adapter_key = f"{provider.get('adapter')}@{provider.get('adapter_version')}"
    if adapter_key not in _adapters():
        raise BoundaryError(f"no bound adapter for {adapter_key}")
    return {**provider, "_adapter_key": adapter_key}


def _ensure_new_action(events: list[dict[str, Any]], action_id: str) -> None:
    if any(
        event.get("event") == "permit_acquired" and event.get("action_id") == action_id
        for event in events
    ):
        permit = next(
            event for event in events
            if event.get("event") == "permit_acquired" and event.get("action_id") == action_id
        )
        raise BoundaryError(
            f"boundary action {action_id} already exists; consumed=true; "
            f"request count={permit.get('count')}; same action must never be retried or resubmitted"
        )


def _failure_message(
    phase: str,
    action_id: str,
    count: int,
    outcome: str,
    recovery: str,
    detail: str = "",
) -> str:
    suffix = f"; detail: {detail}" if detail else ""
    return (
        f"{phase} {outcome}; boundary action {action_id} consumed=true; "
        f"request count={count}; same action must never be retried or resubmitted; "
        f"recovery: {recovery}{suffix}"
    )


def _reserve_request(
    session_dir: Path,
    action_id: str,
    stage: str,
    category: str,
    route: str,
    spec: RequestSpec,
    count: int,
    now: str,
    *,
    query_hash: Optional[str] = None,
) -> str:
    fingerprint = _request_fingerprint(spec)
    try:
        _reserve_boundary_action_unlocked(
            session_dir,
            action_id,
            stage,
            category,
            route,
            count,
            fingerprint,
            now,
            query_hash=query_hash,
        )
    except QuotaError as exc:
        raise BoundaryError(str(exc)) from exc
    return fingerprint


def _demo_result(query: str) -> ParsedResult:
    """Deterministic no-network result: exercises the full lifecycle honestly.

    Demo occurrences are real occurrences (permits, journal, spool, state
    patch), but the registry bars demo routes from ever supporting claims —
    this is the harness demonstrating itself, not producing evidence.
    """

    text = (
        "Demo probe result (no network, no cost).\n"
        f"query: {query}\n"
        "This deterministic payload proves the permit -> attempt -> spool -> "
        "occurrence -> validate -> render loop end to end."
    )
    return ParsedResult(
        synthesis_text=text,
        citations=[],
        cost_usd=0.0,
        usage={"demo": True},
        model="demo-local",
        kind="demo_probe",
    )


def execute_probe(
    session_dir: Path,
    action_id: str,
    stage: str,
    route: str,
    query: str,
    now: str,
    transport: Optional[Transport] = None,
    environ: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Build, reserve, and execute one probe request atomically.

    Lifecycle written to the event journal: attempted, then exactly one of
    completed (occurrence recorded), failed (terminal, boundary action consumed), or
    uncertain (timeout after send — the provider may have processed it).
    """

    session_dir = Path(session_dir)
    if not isinstance(query, str) or not query.strip():
        raise BoundaryError("query must be a non-empty string")
    transport = transport or _urllib_transport
    env = dict(os.environ if environ is None else environ)

    with session_lock(session_dir):
        _recover_session_unlocked(session_dir)
        state = _load_state_unlocked(session_dir)
        events, errors = _read_events_unlocked(session_dir)
        if errors:
            raise BoundaryError("event history is malformed")
        _ensure_new_action(events, action_id)
        provider = _bound_route(state, route, mode="sync")
        count = provider.get("request_multiplicity", {}).get("probe")
        if not isinstance(count, int) or count <= 0:
            raise BoundaryError(f"route {route} has invalid probe multiplicity")

        if provider["_adapter_key"] is None:  # no_network_demo route
            spec = RequestSpec(
                "DEMO",
                f"demo://{route}/probe",
                {"X-Research-Mode": "no-network"},
                query.encode("utf-8"),
                0.0,
            )
            fingerprint = _reserve_request(
                session_dir,
                action_id,
                stage,
                "probe",
                route,
                spec,
                count,
                now,
                query_hash=sha256_hex(query.strip()),
            )
            parsed = _demo_result(query.strip())
            payload = json.dumps(
                {"demo": True, "query": query.strip(), "model": parsed.model},
                ensure_ascii=False,
            ).encode("utf-8")
            spool_path = _spool_raw(session_dir, action_id, payload)
            _record_attempt_status_unlocked(
                session_dir, action_id, "accepted", now, {"demo": True, "spool": spool_path.name}
            )
            return _record_occurrence(
                session_dir, state, provider, action_id, action_id, sha256_hex(query.strip()),
                fingerprint, parsed, spool_path, now,
            )

        adapter = _adapters()[provider["_adapter_key"]]

        spec = adapter["build"](query.strip(), env)
        wall_cap = state["contract"]["resource_envelope"]["external"].get("max_wall_time_seconds")
        timeout = min(spec.timeout_s, wall_cap) if isinstance(wall_cap, int) else spec.timeout_s
        spec = RequestSpec(
            spec.method,
            spec.url,
            spec.headers,
            spec.body,
            float(timeout),
            spec.sensitive_query_keys,
        )
        fingerprint = _reserve_request(
            session_dir,
            action_id,
            stage,
            "probe",
            route,
            spec,
            count,
            now,
            query_hash=sha256_hex(query.strip()),
        )
        try:
            status, payload = transport(spec)
        except (socket.timeout, TimeoutError) as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "uncertain", now,
                {"error": f"timeout after send: {exc}"},
            )
            raise BoundaryError(
                _failure_message(
                    "sync request", action_id, count, "timed out and is uncertain",
                    "inspect the recorded lifecycle and provider outcome; do not replay this action",
                    str(exc),
                )
            ) from exc
        except urllib.error.HTTPError as exc:  # response with error status
            status, payload = exc.code, exc.read()
        except (urllib.error.URLError, OSError) as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "failed", now, {"error": f"transport: {exc}"}
            )
            raise BoundaryError(
                _failure_message(
                    "sync request", action_id, count, "transport failed",
                    "inspect the recorded lifecycle; do not replay this action",
                    str(exc),
                )
            ) from exc

        spool_path = _spool_raw(session_dir, action_id, payload)
        _record_attempt_status_unlocked(
            session_dir, action_id, "accepted", now,
            {"http_status": status, "spool": spool_path.name},
        )
        if status != 200:
            _record_attempt_status_unlocked(
                session_dir, action_id, "failed", now,
                {"http_status": status, "spool": spool_path.name},
            )
            raise BoundaryError(
                _failure_message(
                    "sync request", action_id, count, f"returned HTTP {status}",
                    f"inspect provider spool {spool_path.name}; do not replay this action",
                )
            )
        try:
            parsed = adapter["parse"](payload)
        except AdapterParseError as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "failed", now,
                {"error": str(exc)[:300], "spool": spool_path.name},
            )
            raise AdapterParseError(
                _failure_message(
                    "sync response", action_id, count, "parse failed",
                    f"inspect provider spool {spool_path.name}; do not replay this action",
                    str(exc),
                )
            ) from exc

        return _record_occurrence(
            session_dir, state, provider, action_id, action_id, sha256_hex(query.strip()),
            fingerprint, parsed, spool_path, now,
        )


# ── Async deep-engine boundary ──────────────────────────────────────────────
#
# submit is the paid POST: this boundary owns the `deep` reservation and is
# NEVER retried. poll is one physical GET per call, with this boundary owning
# each `transport` reservation — the caller (Organizer/CLI) drives the backoff
# cadence between calls, since the session lock must never be held across a
# sleep. deep-timeout is a free,
# no-network wall-clock check that moves a stuck `accepted` action to
# `uncertain`; the next poll call journals a resume and continues.


def execute_deep_submit(
    session_dir: Path,
    action_id: str,
    stage: str,
    route: str,
    query: str,
    now: str,
    transport: Optional[Transport] = None,
    environ: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Build, reserve, and submit one deep-research job atomically. The paid POST is sent
    at most once: on any ambiguity after the bytes go out (timeout) this
    records `uncertain` and raises rather than retrying.

    Lifecycle written to the event journal: attempted, then exactly one of
    accepted (details include the provider job token), failed (terminal HTTP
    error or malformed accept body; boundary action consumed), or uncertain (timeout
    after send).
    """

    session_dir = Path(session_dir)
    if not isinstance(query, str) or not query.strip():
        raise BoundaryError("query must be a non-empty string")
    query = query.strip()
    transport = transport or _urllib_transport
    env = dict(os.environ if environ is None else environ)

    with session_lock(session_dir):
        _recover_session_unlocked(session_dir)
        state = _load_state_unlocked(session_dir)
        events, errors = _read_events_unlocked(session_dir)
        if errors:
            raise BoundaryError("event history is malformed")
        _ensure_new_action(events, action_id)
        provider = _bound_route(state, route, mode="async")
        count = provider.get("request_multiplicity", {}).get("deep")
        if not isinstance(count, int) or count <= 0:
            raise BoundaryError(f"route {route} has invalid deep multiplicity")
        adapter = _adapters()[provider["_adapter_key"]]

        spec = adapter["submit"](query, env)
        query_hash = sha256_hex(query)
        _reserve_request(
            session_dir, action_id, stage, "deep", route, spec, count, now,
            query_hash=query_hash,
        )
        try:
            status, payload = transport(spec)
        except (socket.timeout, TimeoutError) as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "uncertain", now,
                {"error": f"timeout after send: {exc}"},
            )
            raise BoundaryError(
                _failure_message(
                    "deep submit", action_id, count, "timed out and is uncertain",
                    "run deep-pending; with no token, perform manual inspection; do not resubmit",
                    str(exc),
                )
            ) from exc
        except urllib.error.HTTPError as exc:  # response with error status
            status, payload = exc.code, exc.read()
        except (urllib.error.URLError, OSError) as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "failed", now, {"error": f"transport: {exc}"}
            )
            raise BoundaryError(
                _failure_message(
                    "deep submit", action_id, count, "transport failed",
                    "inspect the provider outcome manually; do not resubmit",
                    str(exc),
                )
            ) from exc

        # Raw accept payload spooled before any parsing: a malformed accept
        # body never loses the paid bytes.
        spool_path = _spool_raw(session_dir, action_id, payload)

        if status != 200:
            _record_attempt_status_unlocked(
                session_dir, action_id, "failed", now,
                {"http_status": status, "spool": spool_path.name},
            )
            raise BoundaryError(
                _failure_message(
                    "deep submit", action_id, count, f"returned HTTP {status}",
                    f"inspect provider spool {spool_path.name} and the provider outcome manually; do not resubmit",
                )
            )

        try:
            token = adapter["job_token"](payload)
        except AdapterParseError as exc:
            _record_attempt_status_unlocked(
                session_dir, action_id, "uncertain", now,
                {"error": str(exc)[:300], "spool": spool_path.name},
            )
            raise AdapterParseError(
                _failure_message(
                    "deep submit response", action_id, count, "job-token parse failed; no token recorded",
                    "run deep-pending; because no token is available, perform manual inspection; do not resubmit",
                    str(exc),
                )
            ) from exc

        job_ref = f"{provider['id']}:{token}"
        _record_attempt_status_unlocked(
            session_dir, action_id, "accepted", now,
            {"job": job_ref, "http_status": status, "spool": spool_path.name},
        )
        return {
            "action_id": action_id,
            "job": job_ref,
            "status": "accepted",
            "spool_path": str(spool_path),
        }


def execute_deep_poll(
    session_dir: Path,
    deep_action_id: str,
    poll_action_id: str,
    stage: str,
    route: str,
    now: str,
    transport: Optional[Transport] = None,
    environ: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Execute exactly ONE physical poll GET against an accepted or uncertain
    deep action, reserving the transport action inside this boundary.

    Outcomes:
    - still running: the poll action's own attempt completes (details
      {"job_status": "running"}); the deep action is left untouched.
    - terminal success: the poll action completes; an occurrence is recorded
      against the DEEP action and its attempt transitions to completed.
    - terminal failure (well-formed provider FAILED status): the poll action
      completes (it did its job); the deep action's attempt transitions to
      failed.
    - malformed terminal: the poll action's attempt fails and AdapterParseError
      propagates; the deep action is left untouched (still accepted),
      harvestable by a later poll at zero marginal cost.

    Calling this on an `uncertain` deep action first journals a resume
    transition (uncertain -> accepted, details {"resume": true}) before the
    physical poll — this IS the "harvest after uncertain" path; there is no
    separate resume verb.
    """

    session_dir = Path(session_dir)
    transport = transport or _urllib_transport
    env = dict(os.environ if environ is None else environ)

    with session_lock(session_dir):
        _recover_session_unlocked(session_dir)
        state = _load_state_unlocked(session_dir)
        events, errors = _read_events_unlocked(session_dir)
        if errors:
            raise BoundaryError("event history is malformed")

        deep_permit, deep_status = _deep_action_lookup(events, deep_action_id)
        if deep_permit.get("category") != "deep":
            raise BoundaryError("execute_deep_poll deep_action_id must be a deep action")
        if deep_permit.get("route") != route:
            raise BoundaryError("poll route must match the deep action's route")
        if deep_permit.get("stage") != stage:
            raise BoundaryError("poll stage must match the deep action's stage")
        if deep_status not in {"accepted", "uncertain"}:
            raise BoundaryError(
                f"deep action {deep_action_id} is not pollable from status {deep_status!r}"
            )

        _ensure_new_action(events, poll_action_id)
        provider = _bound_route(state, route, mode="async")
        count = provider.get("request_multiplicity", {}).get("transport")
        if not isinstance(count, int) or count <= 0:
            raise BoundaryError(f"route {route} has invalid transport multiplicity")
        adapter = _adapters()[provider["_adapter_key"]]

        token = _job_token_for(events, deep_action_id)
        spec = adapter["poll"](token, env)
        poll_fingerprint = _reserve_request(
            session_dir, poll_action_id, stage, "transport", route, spec, count, now,
        )
        if deep_status == "uncertain":
            _record_attempt_status_unlocked(
                session_dir, deep_action_id, "accepted", now, {"resume": True}
            )
        try:
            status, payload = transport(spec)
        except (socket.timeout, TimeoutError) as exc:
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "uncertain", now,
                {"error": f"timeout after send: {exc}"},
            )
            raise BoundaryError(
                _failure_message(
                    "deep poll", poll_action_id, count, "timed out and is uncertain",
                    "run deep-pending to confirm the token, then use a new deep-poll action",
                    str(exc),
                )
            ) from exc
        except urllib.error.HTTPError as exc:
            status, payload = exc.code, exc.read()
        except (urllib.error.URLError, OSError) as exc:
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "failed", now, {"error": f"transport: {exc}"}
            )
            raise BoundaryError(
                _failure_message(
                    "deep poll", poll_action_id, count, "transport failed",
                    "run deep-pending to confirm the token, then use a new deep-poll action",
                    str(exc),
                )
            ) from exc

        poll_spool_path = _spool_raw(session_dir, poll_action_id, payload)
        _record_attempt_status_unlocked(
            session_dir, poll_action_id, "accepted", now,
            {"http_status": status, "spool": poll_spool_path.name},
        )

        if status != 200:
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "failed", now,
                {"http_status": status, "spool": poll_spool_path.name},
            )
            raise BoundaryError(
                _failure_message(
                    "deep poll", poll_action_id, count, f"returned HTTP {status}",
                    f"inspect provider spool {poll_spool_path.name}, run deep-pending, then use a new deep-poll action",
                )
            )

        try:
            parsed = adapter["extract"](payload)
        except AdapterTerminalFailure as exc:
            # The poll itself succeeded (it correctly learned the job failed).
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "completed", now,
                {"job_status": "failed", "spool": poll_spool_path.name},
            )
            _record_attempt_status_unlocked(
                session_dir, deep_action_id, "failed", now,
                {"error": str(exc)[:300], "spool": poll_spool_path.name},
            )
            terminal_status = "failed"
            try:
                terminal_payload = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                terminal_payload = {}
            if isinstance(terminal_payload, dict) and isinstance(terminal_payload.get("status"), str):
                terminal_status = terminal_payload["status"].lower()
            raise BoundaryError(
                _failure_message(
                    "deep poll",
                    poll_action_id,
                    count,
                    f"terminal failure (deep status={terminal_status})",
                    f"inspect provider spool {poll_spool_path.name}; "
                    "start a fresh /deep run if the research must be repeated",
                    str(exc),
                )
            ) from exc
        except AdapterParseError as exc:
            # Genuinely unreadable payload: the poll attempt itself failed.
            # The deep action is deliberately left untouched (still accepted
            # or freshly resumed) so a later poll can harvest at zero cost.
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "failed", now,
                {"error": "malformed terminal payload", "spool": poll_spool_path.name},
            )
            raise AdapterParseError(
                _failure_message(
                    "deep poll response", poll_action_id, count, "parse failed",
                    f"inspect provider spool {poll_spool_path.name}, run deep-pending, then use a new deep-poll action",
                    str(exc),
                )
            ) from exc

        if parsed is None:
            _record_attempt_status_unlocked(
                session_dir, poll_action_id, "completed", now, {"job_status": "running"}
            )
            return {
                "deep_action_id": deep_action_id,
                "poll_action_id": poll_action_id,
                "status": "running",
                "poll_spool_path": str(poll_spool_path),
            }

        terminal_poll_event = _record_attempt_status_unlocked(
            session_dir, poll_action_id, "completed", now,
            {"job_status": "completed", "spool": poll_spool_path.name},
        )
        query_hash = _deep_query_hash(events, deep_action_id)
        result = _record_occurrence(
            session_dir, state, provider, deep_action_id, poll_action_id, query_hash,
            poll_fingerprint, parsed, poll_spool_path, now,
            terminal_poll_event_hash=terminal_poll_event["event_hash"],
        )
        result["status"] = "completed"
        result["poll_action_id"] = poll_action_id
        return result


def execute_deep_timeout(session_dir: Path, action_id: str, now: str) -> dict[str, Any]:
    """Free, no-network wall-clock check: move an `accepted` deep action to
    `uncertain` once the contract's external.max_wall_time_seconds has
    elapsed since the ORIGINAL submission (the first accepted event's `at` —
    a later resume never pushes this deadline out).

    Idempotent and side-effect-free when there is nothing to do: an action
    that is not `accepted`, or has not yet timed out, returns
    {"transitioned": False, ...} rather than raising, so a monitoring loop
    can call this indiscriminately over every deep action in a session.
    """

    session_dir = Path(session_dir)
    with session_lock(session_dir):
        _recover_session_unlocked(session_dir)
        state = _load_state_unlocked(session_dir)
        events, errors = _read_events_unlocked(session_dir)
        if errors:
            raise BoundaryError("event history is malformed")
        permit, status = _deep_action_lookup(events, action_id)
        if permit.get("category") != "deep":
            raise BoundaryError("execute_deep_timeout only handles deep actions")
        if status != "accepted":
            return {"action_id": action_id, "transitioned": False, "reason": f"status is {status}"}

        submitted_at = _first_status_at(events, action_id, "accepted")
        wall_cap = state["contract"]["resource_envelope"]["external"].get("max_wall_time_seconds")
        if not isinstance(wall_cap, int):
            raise BoundaryError("contract external.max_wall_time_seconds is not configured")
        elapsed = _elapsed_seconds(submitted_at, now)
        if elapsed < wall_cap:
            return {
                "action_id": action_id,
                "transitioned": False,
                "elapsed_seconds": elapsed,
                "max_wall_time_seconds": wall_cap,
            }
        _record_attempt_status_unlocked(
            session_dir, action_id, "uncertain", now,
            {"elapsed_seconds": elapsed, "max_wall_time_seconds": wall_cap},
        )
        return {
            "action_id": action_id,
            "transitioned": True,
            "elapsed_seconds": elapsed,
            "max_wall_time_seconds": wall_cap,
        }


def _record_occurrence(
    session_dir: Path,
    state: dict[str, Any],
    provider: dict[str, Any],
    action_id: str,
    request_action_id: str,
    query_hash: str,
    fingerprint: str,
    parsed: ParsedResult,
    spool_path: Path,
    now: str,
    *,
    terminal_poll_event_hash: Optional[str] = None,
) -> dict[str, Any]:
    """Write the occurrence patch and complete the attempt. Caller holds the lock.

    `query_hash` is pre-hashed by the caller rather than taking the raw query
    text: the async poll path recovers it from the journal (the raw query is
    not available at poll time) and the sync path hashes it inline, so both
    callers converge on this one shape.
    """

    occurrence = {
        "id": f"occ-{action_id}",
        "provider_id": provider["id"],
        "action_id": action_id,
        "request_action_id": request_action_id,
        "kind": parsed.kind,
        "query_hash": query_hash,
        "fingerprint": fingerprint,
        "at": now,
        "model": parsed.model,
        "cost_usd": parsed.cost_usd,
        "citation_count": len(parsed.citations),
        "citations": parsed.citations[:CITATION_LIMIT],
        "synthesis_excerpt": parsed.synthesis_text[:SYNTHESIS_EXCERPT_LIMIT],
        "synthesis_truncated": len(parsed.synthesis_text) > SYNTHESIS_EXCERPT_LIMIT,
        "spool": spool_path.name,
    }
    if terminal_poll_event_hash is not None:
        occurrence["terminal_poll_event_hash"] = terminal_poll_event_hash
    updated = _apply_boundary_patch_unlocked(
        session_dir,
        [{"op": "add", "path": "/retrieval_occurrences/-", "value": occurrence}],
        state["session"]["revision"],
        now,
    )
    _record_attempt_status_unlocked(
        session_dir, action_id, "completed", now,
        {"occurrence_id": occurrence["id"], "cost_usd": parsed.cost_usd,
         "citation_count": len(parsed.citations)},
    )
    return {
        "occurrence": occurrence,
        "revision": updated["session"]["revision"],
        "spool_path": str(spool_path),
    }
