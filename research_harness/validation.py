"""Fail-closed validation for canonical v2 research sessions."""

from __future__ import annotations

import hashlib
import html
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from ._canon import RETENTION_RANK, canonical_source_key, indexed, sha256_hex
from ._platform import is_symlink_or_reparse_point
from .artifacts import MEDIA_EXTENSIONS, SCANNER_VERSION
from .contracts import METERED_CATEGORIES
from .providers import action_cost_class
from .quota import ATTEMPT_TRANSITIONS, BOUNDARY_CATEGORIES, HASH64_RE
from .state import state_sha256, validate_state_document
from .state import CONTRACT_SEMANTICS_V3, CONTRACT_SEMANTICS_V4
from .storage import (
    _event_chain_errors,
    _load_state_unlocked,
    _read_events_unlocked,
    _recover_session_unlocked,
    session_lock,
)


PASSING_CLAIM_STATUSES = frozenset({"corroborated"})
VALID_DELIVERY_STATUSES = frozenset({"IN_PROGRESS", "PASS", "PARTIAL", "BLOCKED"})
TERMINAL_DELIVERY_STATUSES = frozenset({"PASS", "PARTIAL", "BLOCKED"})
EVIDENCE_SHORTFALL_CODES = frozenset(
    {
        "tier.load_bearing_claims_missing",
        "profile.direct_evidence_missing",
        "profile.heavy_capture_diversity",
    }
)
DELIVERY_SHORTFALL_CODES = frozenset(
    {
        "tier.terminal_status_missing",
        "tier.human_status_missing",
        "tier.human_recommendation_missing",
        "tier.decision_missing",
        "tier.human_reason_missing",
        "tier.human_limitation_missing",
        "tier.human_safe_action_missing",
        "tier.acceptance_tests_missing",
        "tier.anti_lock_in_missing",
        "tier.coverage_audit_missing",
        "tier.targeted_reverification_missing",
        "posture.decision_joint_missing",
    }
)
HUMAN_STATUS_SENTINELS = frozenset(
    {"證據不足", "EVIDENCE_INSUFFICIENT", "交付不完整", "DELIVERY_INCOMPLETE"}
)
DELIVERY_HUMAN_STATUS_SENTINELS = frozenset({"交付不完整", "DELIVERY_INCOMPLETE"})
# Semantics versions strict enough to re-derive every action's atomic
# occurrence/quota/attempt lifecycle from the event journal (see
# _validate_atomic_occurrences, _validate_quota, _validate_attempt_lifecycle).
STRICT_ATOMIC_SEMANTICS = frozenset({CONTRACT_SEMANTICS_V3, CONTRACT_SEMANTICS_V4})
# Semantics versions under which a decision-posture PASS must carry a
# coverage_audit record on every profile (ERROR), not just heavy. Packages
# recorded under an older semantics keep the historical WARNING-only
# behaviour so already-shipped packages are not retroactively invalidated.
NEW_COVERAGE_AUDIT_SEMANTICS = frozenset({CONTRACT_SEMANTICS_V4})
REPORT_HASH_RE = re.compile(r'data-state-sha256=["\']([0-9a-f]{64})["\']')


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str
    path: str


def tier_shortfall_labels(issues: Iterable[Issue]) -> tuple[str, str]:
    """Map deterministic tier issue codes to human and technical delivery labels."""

    codes = {issue.code for issue in issues}
    if codes.intersection(EVIDENCE_SHORTFALL_CODES):
        return "證據不足", "EVIDENCE_INSUFFICIENT"
    if codes.intersection(DELIVERY_SHORTFALL_CODES):
        return "交付不完整", "DELIVERY_INCOMPLETE"
    return "交付不完整", "DELIVERY_INCOMPLETE"


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...]
    state_sha256: str
    integrity_ok: bool = True
    tier_contract_met: bool = True
    human_recommendation: str = ""
    human_status: str = ""

    @property
    def ok(self) -> bool:
        return not self.errors and self.tier_contract_met

    @property
    def errors(self) -> tuple[Issue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "ERROR")

    @property
    def warnings(self) -> tuple[Issue, ...]:
        return tuple(issue for issue in self.issues if issue.level == "WARNING")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "integrity_ok": self.integrity_ok,
            "tier_contract_met": self.tier_contract_met,
            "human_recommendation": self.human_recommendation,
            "human_status": self.human_status,
            "state_sha256": self.state_sha256,
            "issues": [asdict(issue) for issue in self.issues],
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
        }


def _add(
    issues: list[Issue],
    code: str,
    message: str,
    path: str,
    level: str = "ERROR",
) -> None:
    issues.append(Issue(level=level, code=code, message=message, path=path))


def _add_once(
    issues: list[Issue],
    code: str,
    message: str,
    path: str,
    level: str = "ERROR",
) -> None:
    if not any(issue.code == code and issue.path == path for issue in issues):
        _add(issues, code, message, path, level)


def _validate_event_lineage(
    state: dict[str, Any],
    events: list[dict[str, Any]],
    event_errors: list[str],
    current_hash: str,
    issues: list[Issue],
) -> None:
    chain_errors = [] if event_errors else _event_chain_errors(events)
    for message in event_errors:
        _add(issues, "event.parse", message, "/events")
    for message in chain_errors:
        _add(issues, "event.chain", message, "/events")
    if event_errors or chain_errors:
        return

    genesis = [event for event in events if event.get("event") == "session_created"]
    if len(genesis) != 1 or genesis[0].get("session_id") != state.get("session", {}).get("id"):
        _add(issues, "state.genesis", "session genesis event is missing or inconsistent", "/events")
    revisions = [event for event in events if event.get("event") == "state_revision"]
    revision = state.get("session", {}).get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool):
        return
    expected = list(range(1, revision + 1))
    observed = [event.get("revision") for event in revisions]
    if observed != expected:
        _add(issues, "state.revision_lineage", "state revision events are not exact and monotonic", "/events")
    if revision == 0:
        if len(genesis) == 1 and genesis[0].get("state_sha256") != current_hash:
            _add(issues, "state.hash_mismatch", "genesis hash does not match canonical state", "/state")
    elif not revisions or revisions[-1].get("new_state_sha256") != current_hash:
        _add(issues, "state.hash_mismatch", "latest revision hash does not match canonical state", "/state")


def _validate_attempt_lifecycle(
    events: list[dict[str, Any]], issues: list[Issue], *, strict_atomic: bool
) -> None:
    """Independently re-derive every action's attempt state machine.

    The writer enforces ATTEMPT_TRANSITIONS at append time, but validation is
    the delivery gate and must not trust the writer: a hash-chained journal
    can still contain forged from_status values or transitions appended by
    other tooling."""

    current = {
        event.get("action_id"): event.get("initial_status", "acquired")
        for event in events
        if event.get("event") == "permit_acquired"
        and isinstance(event.get("action_id"), str)
    }
    if not strict_atomic:
        current = {
            action_id: "acquired"
            for action_id in current
        }
    index = 0
    for event in events:
        if event.get("event") != "attempt_status":
            continue
        path = f"/events/attempt/{index}"
        index += 1
        action_id = event.get("action_id")
        if action_id not in current:
            _add(issues, "attempt.unknown_action", "attempt status references unknown action", path)
            continue
        expected_from = current[action_id]
        if event.get("from_status") != expected_from:
            _add(issues, "attempt.from_status", "attempt from_status does not match lifecycle", path)
        status = event.get("status")
        if status not in ATTEMPT_TRANSITIONS.get(expected_from, set()):
            _add(issues, "attempt.transition", "attempt status transition is invalid", path)
            continue
        current[action_id] = status


def _validate_quota(
    state: dict[str, Any], events: list[dict[str, Any]], issues: list[Issue], *, strict_atomic: bool
) -> None:
    contract = state.get("contract", {})
    mappings = contract.get("stage_permit_map", [])
    providers = {
        provider.get("id"): provider
        for provider in state.get("capabilities", {}).get("providers", [])
        if isinstance(provider, dict)
    }
    ceilings = contract.get("resource_envelope", {}).get("physical_ceiling", {})
    permits = [event for event in events if event.get("event") == "permit_acquired"]
    seen_actions: set[str] = set()
    category_usage: dict[str, int] = {}
    mapping_usage: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for index, permit in enumerate(permits):
        path = f"/events/permit/{index}"
        action_id = permit.get("action_id")
        if not isinstance(action_id, str) or not action_id or action_id in seen_actions:
            _add(issues, "quota.duplicate", "permit action IDs must be unique and non-empty", path)
        elif isinstance(action_id, str):
            seen_actions.add(action_id)
        count = permit.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            _add(issues, "quota.invalid", "permit count must be a positive integer", path)
            continue
        category = permit.get("category")
        route = permit.get("route")
        stage = permit.get("stage")
        initial_status = permit.get("initial_status")
        is_boundary_category = isinstance(category, str) and category in BOUNDARY_CATEGORIES
        if strict_atomic and category in METERED_CATEGORIES and not is_boundary_category:
            _add(
                issues,
                "quota.metered_boundary_missing",
                "metered categories require an implemented request boundary",
                path,
            )
        if strict_atomic and is_boundary_category and initial_status != "attempted":
            _add(
                issues,
                "quota.boundary_initial_status",
                "boundary permits must journal initial_status=attempted",
                path,
            )
        fingerprint = permit.get("fingerprint")
        if strict_atomic and is_boundary_category and (
            not isinstance(fingerprint, str) or HASH64_RE.fullmatch(fingerprint) is None
        ):
            _add(
                issues,
                "quota.boundary_fingerprint",
                "boundary permits must carry a 64-character lowercase hexadecimal fingerprint",
                path,
            )
        query_hash = permit.get("query_hash")
        if strict_atomic and category in {"probe", "deep"} and (
            not isinstance(query_hash, str) or HASH64_RE.fullmatch(query_hash) is None
        ):
            _add(
                issues,
                "quota.deep_query_hash",
                "probe/deep permits must carry a 64-character lowercase hexadecimal query_hash",
                path,
            )
        if strict_atomic and category not in {"probe", "deep"} and query_hash is not None:
            _add(
                issues,
                "quota.non_deep_query_hash",
                "non-deep permits must not carry query_hash",
                path,
            )
        if strict_atomic and not is_boundary_category and (
            initial_status is not None
            or "fingerprint" in permit
            or "query_hash" in permit
        ):
            _add(
                issues,
                "quota.boundary_category_mismatch",
                "boundary fields do not match the permit category",
                path,
            )
        if strict_atomic and is_boundary_category:
            base_fields = {
                "event", "at", "action_id", "stage", "category", "route",
                "invocation_index", "count", "seq", "prev_hash", "event_hash",
            }
            expected_fields = base_fields | {"initial_status", "fingerprint"}
            if category in {"probe", "deep"}:
                expected_fields.add("query_hash")
            if set(permit) != expected_fields:
                _add(
                    issues,
                    "quota.boundary_shape",
                    "boundary permit fields are missing or contain forbidden fields",
                    path,
                )
        key = (stage, category, route)
        matching = [
            mapping
            for mapping in mappings
            if isinstance(mapping, dict)
            and (mapping.get("stage"), mapping.get("category"), mapping.get("route")) == key
        ]
        if len(matching) != 1:
            _add(issues, "quota.mapping", "permit has no unique confirmed stage mapping", path)
        mapping_usage.setdefault(key, []).append(permit)
        category_usage[category] = category_usage.get(category, 0) + count
        provider = providers.get(route)
        multiplicity = provider.get("request_multiplicity", {}).get(category) if provider else None
        if multiplicity != count:
            _add(issues, "quota.multiplicity", "permit count differs from route multiplicity", path)

    for key, used in mapping_usage.items():
        mapping = next(
            (
                item
                for item in mappings
                if isinstance(item, dict)
                and (item.get("stage"), item.get("category"), item.get("route")) == key
            ),
            None,
        )
        if mapping is None:
            continue
        request_count = sum(item["count"] for item in used if isinstance(item.get("count"), int))
        if len(used) > mapping.get("invocations", -1) or request_count > mapping.get("count", -1):
            _add(issues, "quota.exceeded", "stage mapping capacity was exceeded", "/events")
    for category, used in category_usage.items():
        ceiling = ceilings.get(category)
        if not isinstance(ceiling, int) or isinstance(ceiling, bool) or used > ceiling:
            _add(issues, "quota.exceeded", f"physical ceiling exceeded for {category}", "/events")

    cost_budget = contract.get("resource_envelope", {}).get("cost_budget")
    if isinstance(cost_budget, dict):
        cost_usage = {"deep": 0, "search": 0}
        for permit in permits:
            provider = providers.get(permit.get("route"))
            count = permit.get("count")
            if provider is None or not isinstance(count, int) or isinstance(count, bool):
                continue
            cost_class = action_cost_class(provider, str(permit.get("category")))
            if cost_class in cost_usage:
                cost_usage[cost_class] += count
        for cost_class, used in cost_usage.items():
            ceiling = cost_budget.get(cost_class)
            if not isinstance(ceiling, int) or isinstance(ceiling, bool) or used > ceiling:
                _add(
                    issues,
                    "quota.cost_exceeded",
                    f"cost budget exceeded for {cost_class}",
                    "/events",
                )


def _confined_artifact_path(session_dir: Path, relative_path: Any) -> Path | None:
    if not isinstance(relative_path, str):
        return None
    relative = Path(relative_path)
    if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != "raw":
        return None
    path = session_dir / relative
    if path.parent != session_dir / "raw":
        return None
    return path


def _validate_atomic_occurrences(
    state: dict[str, Any], events: list[dict[str, Any]], issues: list[Issue]
) -> None:
    """Bind each v3 occurrence to its exact logical and physical actions."""

    permits = [event for event in events if event.get("event") == "permit_acquired"]
    permits_by_id: dict[str, list[dict[str, Any]]] = {}
    for permit in permits:
        action_id = permit.get("action_id")
        if isinstance(action_id, str):
            permits_by_id.setdefault(action_id, []).append(permit)
    statuses: dict[str, list[str]] = {}
    for event in events:
        if event.get("event") == "attempt_status" and isinstance(event.get("action_id"), str):
            statuses.setdefault(event["action_id"], []).append(event.get("status"))

    seen_request_ids: set[str] = set()
    seen_logical_ids: set[str] = set()
    providers = {
        provider.get("id"): provider
        for provider in state.get("capabilities", {}).get("providers", [])
        if isinstance(provider, dict)
    }
    for index, occurrence in enumerate(state.get("retrieval_occurrences", [])):
        path = f"/retrieval_occurrences/{index}"
        if not isinstance(occurrence, dict):
            _add(issues, "occurrence.shape", "occurrence must be an object", path)
            continue
        logical_id = occurrence.get("action_id")
        request_id = occurrence.get("request_action_id")
        if not isinstance(logical_id, str) or not logical_id:
            _add(issues, "occurrence.action_id", "occurrence logical action_id is required", path)
            continue
        logical_permits = permits_by_id.get(logical_id, [])
        if not isinstance(request_id, str) or not request_id:
            _add(issues, "occurrence.request_action_id", "occurrence request_action_id is required", path)
            continue
        if request_id in seen_request_ids:
            _add(issues, "occurrence.request_duplicate", "request_action_id may have only one occurrence", path)
        seen_request_ids.add(request_id)
        if logical_id in seen_logical_ids:
            _add(issues, "occurrence.logical_duplicate", "logical action_id may have only one terminal occurrence", path)
        seen_logical_ids.add(logical_id)

        request_permits = permits_by_id.get(request_id, [])
        if len(request_permits) != 1:
            _add(issues, "occurrence.request_action_missing", "request_action_id must reference one permit", path)
            continue
        if len(logical_permits) != 1:
            _add(issues, "occurrence.logical_action_missing", "occurrence action_id must reference one permit", path)
            continue
        request_permit = request_permits[0]
        logical_permit = logical_permits[0]
        provider = providers.get(occurrence.get("provider_id"))
        if not isinstance(provider, dict):
            _add(issues, "occurrence.provider", "occurrence provider is not in the capability snapshot", path)
        fingerprint = occurrence.get("fingerprint")
        if not isinstance(fingerprint, str) or HASH64_RE.fullmatch(fingerprint) is None:
            _add(issues, "occurrence.fingerprint", "occurrence fingerprint must be a 64-character lowercase hexadecimal hash", path)
        elif request_permit.get("fingerprint") != fingerprint:
            _add(issues, "occurrence.fingerprint", "occurrence fingerprint does not match request permit", path)
        query_hash = occurrence.get("query_hash")
        if not isinstance(query_hash, str) or HASH64_RE.fullmatch(query_hash) is None:
            _add(issues, "occurrence.query_hash", "occurrence query_hash must be a 64-character lowercase hexadecimal hash", path)
        elif logical_permit.get("query_hash") != query_hash:
            _add(issues, "occurrence.query_hash", "occurrence query_hash does not match logical permit", path)
        if logical_permit.get("route") != occurrence.get("provider_id"):
            _add(issues, "occurrence.route", "occurrence provider does not match logical permit route", path)

        request_statuses = statuses.get(request_id, [])
        logical_statuses = statuses.get(logical_id, [])
        if not request_statuses or request_statuses[-1] != "completed":
            _add(issues, "occurrence.request_lifecycle", "request permit is not terminal completed", path)
        if not logical_statuses or logical_statuses[-1] != "completed":
            _add(issues, "occurrence.logical_lifecycle", "logical permit is not terminal completed", path)

        request_category = request_permit.get("category")
        logical_category = logical_permit.get("category")
        if request_category == "probe":
            if (
                logical_id != request_id
                or logical_category != "probe"
                or request_permit.get("route") != logical_permit.get("route")
            ):
                _add(issues, "occurrence.category", "sync occurrence must reference its probe action", path)
            if "terminal_poll_event_hash" in occurrence:
                _add(
                    issues,
                    "occurrence.terminal_poll_event_hash",
                    "sync occurrence must not carry terminal_poll_event_hash",
                    path,
                )
        elif request_category == "transport":
            if (
                logical_category != "deep"
                or logical_id == request_id
                or request_permit.get("stage") != logical_permit.get("stage")
                or request_permit.get("route") != logical_permit.get("route")
            ):
                _add(issues, "occurrence.category", "async occurrence must reference a deep logical action and terminal poll", path)
            terminal_hash = occurrence.get("terminal_poll_event_hash")
            if not isinstance(terminal_hash, str) or HASH64_RE.fullmatch(terminal_hash) is None:
                _add(
                    issues,
                    "occurrence.terminal_poll_event_hash",
                    "v3 async occurrence must carry a valid terminal_poll_event_hash",
                    path,
                )
            else:
                terminal_events = [
                    event for event in events if event.get("event_hash") == terminal_hash
                ]
                if len(terminal_events) != 1:
                    _add(
                        issues,
                        "occurrence.terminal_poll_event_missing",
                        "terminal_poll_event_hash must resolve to exactly one event",
                        path,
                    )
                else:
                    terminal_event = terminal_events[0]
                    details = terminal_event.get("details")
                    if (
                        terminal_event.get("event") != "attempt_status"
                        or terminal_event.get("action_id") != request_id
                        or terminal_event.get("from_status") != "accepted"
                        or terminal_event.get("status") != "completed"
                        or not isinstance(details, dict)
                        or details.get("job_status") != "completed"
                        or details.get("spool") != occurrence.get("spool")
                    ):
                        _add(
                            issues,
                            "occurrence.terminal_poll_event",
                            "terminal_poll_event_hash must bind the completed terminal poll",
                            path,
                        )
        else:
            _add(issues, "occurrence.category", "occurrence must reference a sync probe or async transport action", path)


def _validate_artifacts(
    session_dir: Path,
    state: dict[str, Any],
    events: list[dict[str, Any]],
    issues: list[Issue],
) -> tuple[dict[str, dict[str, Any]], dict[str, bytes]]:
    artifacts = indexed(state.get("artifact_index"))
    sources = indexed(state.get("sources"))
    occurrences = indexed(state.get("retrieval_occurrences"))
    providers = indexed(state.get("capabilities", {}).get("providers"))
    permits = [event for event in events if event.get("event") == "permit_acquired"]
    indexed_paths: set[str] = set()
    raw_payloads: dict[str, bytes] = {}

    for artifact_id, artifact in artifacts.items():
        path_root = f"/artifact_index/{artifact_id}"
        availability = artifact.get("availability")
        if availability == "purge_pending":
            _add(issues, "artifact.purge_pending", "artifact purge recovery is incomplete", path_root)
        if availability not in {"available", "purge_pending", "purged"}:
            _add(issues, "artifact.availability", "artifact availability is invalid", path_root)
        relative_key = "relative_path" if availability == "available" else "former_relative_path"
        raw_path = _confined_artifact_path(session_dir, artifact.get(relative_key))
        if raw_path is None:
            _add(issues, "artifact.path", "artifact path is not confined under raw", path_root)
        else:
            indexed_paths.add(raw_path.name)
            extension = MEDIA_EXTENSIONS.get(artifact.get("media_type"))
            if extension is None or raw_path.name != f"{artifact_id}{extension}":
                _add(issues, "artifact.path", "artifact path does not match its ID and media type", path_root)
        policy = artifact.get("policy_snapshot")
        expected_policy_hash = sha256_hex(policy) if isinstance(policy, dict) else None
        if artifact.get("policy_sha256") != expected_policy_hash:
            _add(issues, "artifact.policy_hash", "artifact policy snapshot hash is invalid", path_root)
        if artifact.get("scanner_version") != SCANNER_VERSION:
            _add(issues, "artifact.scanner", "artifact scanner version is missing or unknown", path_root)
        if artifact.get("sensitivity") == "secret":
            _add(issues, "artifact.secret", "secret-classified artifacts cannot be persisted", path_root)
        if artifact.get("sensitivity") == "local-sensitive" and artifact.get("include_in_html") is not False:
            _add(issues, "artifact.html_policy", "local-sensitive artifact cannot enter HTML", path_root)

        if availability == "available" and raw_path is not None:
            try:
                metadata = raw_path.lstat()
            except FileNotFoundError:
                _add(issues, "artifact.raw_missing", "available raw artifact is missing", path_root)
            else:
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                    _add(issues, "artifact.path", "raw artifact is not a regular non-symlink file", path_root)
                else:
                    payload = raw_path.read_bytes()
                    raw_payloads[artifact_id] = payload
                    if (
                        metadata.st_size != artifact.get("byte_size")
                        or hashlib.sha256(payload).hexdigest() != artifact.get("sha256")
                    ):
                        _add(issues, "artifact.integrity", "raw artifact size or hash changed", path_root)

        provenance = artifact.get("provenance")
        if not isinstance(provenance, dict):
            _add(issues, "artifact.provenance", "artifact provenance is missing", path_root)
            continue
        origin_kind = provenance.get("origin_kind")
        if origin_kind == "local_output":
            action_id = provenance.get("action_id")
            if not any(
                permit.get("action_id") == action_id
                and permit.get("category") == "local"
                and permit.get("route") == "local"
                for permit in permits
            ):
                _add(issues, "artifact.provenance", "local artifact action is missing", path_root)
        elif origin_kind == "user_file":
            if not isinstance(provenance.get("supplied_by"), str) or not provenance["supplied_by"]:
                _add(issues, "artifact.provenance", "user artifact supplier is missing", path_root)
        elif origin_kind == "fetched_source":
            source_id = provenance.get("source_id")
            occurrence = occurrences.get(provenance.get("fetch_occurrence_id"))
            if source_id not in sources or occurrence is None or occurrence.get("source_id") != source_id:
                _add(issues, "artifact.provenance", "fetched artifact lineage is missing", path_root)
        elif origin_kind == "host_capture":
            capture = artifact.get("host_capture")
            if not isinstance(capture, dict):
                _add(issues, "artifact.host_capture", "host capture metadata is missing", path_root)
                continue
            required = {
                "source_url",
                "source_title",
                "canonical_source_key",
                "upstream_key",
                "fidelity",
                "captured_at",
                "marginal_purpose",
            }
            if set(capture) != required:
                _add(issues, "artifact.host_capture", "host capture metadata is incomplete", path_root)
            if not isinstance(capture.get("source_url"), str) or not capture["source_url"].strip():
                _add(issues, "artifact.host_capture", "host capture source URL is missing", path_root)
            else:
                try:
                    expected_key = canonical_source_key(capture["source_url"])
                except ValueError:
                    expected_key = None
                    _add(issues, "artifact.host_capture", "host capture source URL is invalid", path_root)
                if expected_key != capture.get("canonical_source_key"):
                    _add(issues, "artifact.host_capture", "host capture source key does not match source URL", path_root)
            if not isinstance(capture.get("source_title"), str) or not capture["source_title"].strip():
                _add(issues, "artifact.host_capture", "host capture source title is missing", path_root)
            if not isinstance(capture.get("canonical_source_key"), str) or not capture["canonical_source_key"].strip():
                _add(issues, "artifact.host_capture", "host capture source key is missing", path_root)
            if not isinstance(capture.get("upstream_key"), str) or not capture["upstream_key"].strip():
                _add(issues, "artifact.host_capture", "host capture upstream key is missing", path_root)
            if capture.get("fidelity") not in {"raw_http", "host_rendered"}:
                _add(issues, "artifact.host_capture", "host capture fidelity is invalid", path_root)
            for field in ("captured_at", "marginal_purpose"):
                if not isinstance(capture.get(field), str) or not capture[field].strip():
                    _add(issues, "artifact.host_capture", f"host capture {field} is missing", path_root)
        elif origin_kind == "provider_payload":
            provider_id = provenance.get("provider_id")
            attempt_id = provenance.get("attempt_or_occurrence_id")
            provider = providers.get(provider_id)
            matched = any(
                permit.get("action_id") == attempt_id and permit.get("route") == provider_id
                for permit in permits
            ) or (
                attempt_id in occurrences and occurrences[attempt_id].get("provider_id") == provider_id
            )
            rights = provider.get("storage_rights", {}) if provider else {}
            allowed = rights.get("payload_retention")
            requested = artifact.get("retention")
            if provider is None or not matched:
                _add(issues, "artifact.provenance", "provider artifact lineage is missing", path_root)
            if (
                allowed not in {"session", "persistent"}
                or requested not in {"session", "persistent"}
                or RETENTION_RANK[requested] > RETENTION_RANK[allowed]
                or (artifact.get("include_in_html") and rights.get("html_allowed") is not True)
            ):
                _add(issues, "artifact.storage_rights", "provider artifact exceeds storage rights", path_root)
        else:
            _add(issues, "artifact.provenance", "artifact origin kind is invalid", path_root)

    raw_dir = session_dir / "raw"
    if raw_dir.exists():
        if is_symlink_or_reparse_point(raw_dir) or not raw_dir.is_dir():
            _add(issues, "artifact.raw_directory", "raw path is not a safe directory", "/raw")
        else:
            for path in raw_dir.iterdir():
                if path.name not in indexed_paths:
                    _add(issues, "artifact.unindexed", f"unindexed raw entry: {path.name}", "/raw")
    return artifacts, raw_payloads


def _validate_evidence(
    state: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    evidence_map = indexed(state.get("evidence"))
    sources = indexed(state.get("sources"))
    origins = indexed(state.get("source_origins"))
    providers = indexed(state.get("capabilities", {}).get("providers"))
    occurrences = state.get("retrieval_occurrences", [])

    for evidence_id, evidence in evidence_map.items():
        path = f"/evidence/{evidence_id}"
        source = sources.get(evidence.get("source_id"))
        if source is None:
            _add(issues, "evidence.source_missing", "evidence source is missing", path)
        origin_id = evidence.get("origin_id")
        if origin_id not in origins or (source and source.get("origin_id") != origin_id):
            _add(issues, "evidence.origin_missing", "evidence source origin is missing or inconsistent", path)
        artifact_id = evidence.get("artifact_id")
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            _add(issues, "evidence.artifact_missing", "evidence artifact record is missing", path)
        provenance = artifact.get("provenance", {}) if artifact is not None else {}
        if provenance.get("origin_kind") == "host_capture" and artifact is not None:
            capture = artifact.get("host_capture", {})
            if source is not None:
                try:
                    derived_key = canonical_source_key(source.get("url"))
                except (TypeError, ValueError):
                    derived_key = None
                    _add(issues, "evidence.source_url_invalid", "host evidence source URL is invalid", path)
                if derived_key != source.get("canonical_source_key") or derived_key != capture.get(
                    "canonical_source_key"
                ):
                    _add(
                        issues,
                        "evidence.host_capture_source_key_mismatch",
                        "host evidence source key does not match captured artifact",
                        path,
                    )
                for field in ("url", "title", "upstream_key"):
                    capture_field = {
                        "url": "source_url",
                        "title": "source_title",
                        "upstream_key": "upstream_key",
                    }[field]
                    if source.get(field) != capture.get(capture_field):
                        _add(
                            issues,
                            "evidence.host_capture_source_metadata_mismatch",
                            "host evidence source metadata does not match captured artifact",
                            path,
                        )
        if provenance.get("origin_kind") == "provider_payload":
            provider = providers.get(provenance.get("provider_id"))
            if (
                provider is None
                or provider.get("evidence_capabilities", {}).get("can_support_claims") is not True
            ):
                _add(
                    issues,
                    "evidence.provider_claims_forbidden",
                    "this provider payload cannot support canonical claims",
                    path,
                )
        payload = raw_payloads.get(artifact_id)
        start = evidence.get("excerpt_start")
        end = evidence.get("excerpt_end")
        excerpt = evidence.get("excerpt")
        artifact_was_purged = artifact is not None and artifact.get("availability") in {
            "purge_pending",
            "purged",
        }
        if artifact_was_purged:
            pass
        elif (
            payload is None
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 0
            or end <= start
            or end > (len(payload) if payload is not None else 0)
            or not isinstance(excerpt, str)
        ):
            _add(issues, "evidence.excerpt_bounds", "exact raw excerpt bounds are invalid", path)
        else:
            try:
                exact = payload[start:end].decode("utf-8")
            except UnicodeDecodeError:
                exact = None
            if exact != excerpt:
                _add(issues, "evidence.excerpt_mismatch", "excerpt does not match raw artifact bytes", path)

        source_id = evidence.get("source_id")
        source_occurrences = [
            occurrence
            for occurrence in occurrences
            if isinstance(occurrence, dict) and occurrence.get("source_id") == source_id
        ]
        if any(
            providers.get(occurrence.get("provider_id"), {}).get("execution_binding")
            == "no_network_demo"
            for occurrence in source_occurrences
        ):
            _add(
                issues,
                "evidence.demo_route_forbidden",
                "no-network demo routes cannot contribute canonical evidence",
                path,
            )
    return evidence_map


def _has_direct_t1_evidence(
    evidence_ids: Any,
    evidence_map: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> bool:
    """True when any supporting evidence is a directly fetched T1 source."""

    return any(
        evidence_map.get(evidence_id, {}).get("source_tier") == "T1"
        and sources.get(evidence_map.get(evidence_id, {}).get("source_id"), {}).get("direct_fetch") is True
        for evidence_id in (evidence_ids if isinstance(evidence_ids, list) else [])
    )


def _claim_has_available_evidence(
    claim: dict[str, Any],
    evidence_map: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
) -> bool:
    for evidence_id in claim.get("supporting_evidence_ids", []):
        evidence = evidence_map.get(evidence_id)
        artifact = artifacts.get(evidence.get("artifact_id")) if evidence else None
        if (
            artifact
            and artifact.get("availability") == "available"
            and evidence.get("artifact_id") in raw_payloads
        ):
            return True
    return False


def _qualifying_profile_capture(
    evidence_id: Any,
    evidence_map: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
) -> tuple[str, str] | None:
    """Return (canonical_source_key, upstream_key) for one clean, available host capture.

    Qualification rules: host capture provenance, available artifact, raw
    bytes present, non-empty key/upstream.
    """

    evidence = evidence_map.get(evidence_id)
    if not isinstance(evidence, dict):
        return None
    artifact = artifacts.get(evidence.get("artifact_id"))
    if (
        not isinstance(artifact, dict)
        or artifact.get("provenance", {}).get("origin_kind") != "host_capture"
        or artifact.get("availability") != "available"
        or artifact.get("id") not in raw_payloads
    ):
        return None
    capture = artifact.get("host_capture", {})
    key = capture.get("canonical_source_key")
    upstream = capture.get("upstream_key")
    if not isinstance(key, str) or not key or not isinstance(upstream, str) or not upstream.strip():
        return None
    return key, upstream


def _has_locally_verifiable_evidence(
    claim: dict[str, Any],
    evidence_map: dict[str, dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
) -> bool:
    """True when a claim links at least one host-captured or local-output artifact.

    Something the host itself fetched or produced, not solely a relayed
    provider synthesis.
    """

    for evidence_id in claim.get("supporting_evidence_ids", []):
        evidence = evidence_map.get(evidence_id)
        if not isinstance(evidence, dict):
            continue
        artifact = artifacts.get(evidence.get("artifact_id"))
        if not isinstance(artifact, dict) or artifact.get("id") not in raw_payloads:
            continue
        if artifact.get("provenance", {}).get("origin_kind") in {"host_capture", "local_output"}:
            return True
    return False


def _profile_evidence_contract(
    state: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
    evidence_map: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> bool:
    """Live-vocabulary evidence requirements keyed on the public cost profile.

    `contract.tier` is pinned to "custom" for every host-led draft (see
    contracts.draft_host_led_contract); this gates on the vocabulary the
    public CLI actually emits: resource_envelope.cost_budget.profile.

    Scope, by design:
      * light (0 deep calls): no extra floor here. Light must stay cheap
        and usable, so it keeps only the tier-agnostic baseline already
        applied to every claim in `_validate_pass` (raw artifact presence,
        source-of-record T1 provenance, etc).
      * standard/heavy (>=1 deep call): each load-bearing claim needs at
        least one directly observed (host-captured or locally produced)
        piece of evidence, not solely a relayed, unverifiable provider
        synthesis.
      * heavy only (2 deep calls -- the second bought specifically for an
        independent angle): each load-bearing claim's captured evidence
        must span at least two distinct upstream sources. A claim resting
        on several capture files that all trace back to one upstream (the
        real regression this task fixes: a Heavy package whose three
        load-bearing claims each cited only noaa.gov, only navy.mil, and
        only nps.gov, respectively) does not count as corroborated.
    """

    contract = state.get("contract", {})
    if contract.get("durability") != "canonical_package":
        return True
    profile = contract.get("resource_envelope", {}).get("cost_budget", {}).get("profile")
    if profile not in {"standard", "heavy"}:
        return True

    load_ids = state.get("summary", {}).get("load_bearing_claim_ids", [])
    if not isinstance(load_ids, list) or not load_ids:
        return True
    claims = indexed(state.get("claims"))

    met = True
    for claim_id in load_ids:
        claim = claims.get(claim_id)
        if not isinstance(claim, dict):
            continue
        if not _has_locally_verifiable_evidence(claim, evidence_map, artifacts, raw_payloads):
            _add(
                issues,
                "profile.direct_evidence_missing",
                "standard and heavy load-bearing claims require at least one directly observed source",
                f"/claims/{claim_id}",
                "WARNING",
            )
            met = False

    if profile != "heavy":
        return met

    for claim_id in load_ids:
        claim = claims.get(claim_id)
        if not isinstance(claim, dict):
            continue
        upstream_keys: set[str] = set()
        has_capture = False
        for evidence_id in claim.get("supporting_evidence_ids", []):
            match = _qualifying_profile_capture(evidence_id, evidence_map, artifacts, raw_payloads)
            if match is not None:
                has_capture = True
                upstream_keys.add(match[1])
        if has_capture and len(upstream_keys) < 2:
            _add(
                issues,
                "profile.heavy_capture_diversity",
                "heavy load-bearing claims resting on captured evidence require at least two distinct upstream sources",
                f"/claims/{claim_id}",
                "WARNING",
            )
            met = False
    return met


def _renderable_human_reasons(
    state: dict[str, Any],
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Return load-bearing claims with at least one validated titled URL source."""

    claims = indexed(state.get("claims"))
    evidence = indexed(state.get("evidence"))
    sources = indexed(state.get("sources"))
    renderable: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for claim_id in state.get("summary", {}).get("load_bearing_claim_ids", []):
        claim = claims.get(claim_id)
        if (
            not isinstance(claim, dict)
            or claim.get("load_bearing") is not True
            or not isinstance(claim.get("text"), str)
            or not claim["text"].strip()
        ):
            continue
        linked_sources: list[dict[str, Any]] = []
        for evidence_id in claim.get("supporting_evidence_ids", []):
            evidence_item = evidence.get(evidence_id)
            source = sources.get(evidence_item.get("source_id")) if isinstance(evidence_item, dict) else None
            if not isinstance(source, dict):
                continue
            try:
                derived_key = canonical_source_key(source.get("url"))
            except (TypeError, ValueError):
                continue
            if (
                not isinstance(source.get("title"), str)
                or not source["title"].strip()
                or source.get("canonical_source_key") != derived_key
            ):
                continue
            linked_sources.append(source)
        if linked_sources:
            renderable.append((claim, linked_sources))
    return renderable


def _canonical_handoff_completeness(
    state: dict[str, Any],
    issues: list[Issue],
) -> bool:
    summary = state.get("summary", {})
    missing = False

    def required_text(
        field: str, code: str, message: str, reject_human_status_sentinel: bool = False
    ) -> None:
        nonlocal missing
        value = summary.get(field)
        if (
            not isinstance(value, str)
            or not value.strip()
            or (reject_human_status_sentinel and value.strip() in HUMAN_STATUS_SENTINELS)
        ):
            _add(issues, code, message, f"/summary/{field}", "WARNING")
            missing = True

    required_text(
        "human_status",
        "tier.human_status_missing",
        "canonical package requires an explicit human status",
        reject_human_status_sentinel=True,
    )
    required_text(
        "human_recommendation",
        "tier.human_recommendation_missing",
        "canonical package requires an explicit human recommendation",
    )
    required_text("decision", "tier.decision_missing", "canonical package requires a bounded decision")

    if not _renderable_human_reasons(state):
        _add(
            issues,
            "tier.human_reason_missing",
            "canonical package requires a named load-bearing reason linked to a validated titled URL",
            "/summary/load_bearing_claim_ids",
            "WARNING",
        )
        missing = True

    handoff = state.get("engineering_handoff", {})
    limitation_values: list[Any] = []
    for values in (handoff.get("constraints"), state.get("open_questions")):
        if isinstance(values, list):
            limitation_values.extend(values)
    limitation_values.extend(
        claim.get("would_change_if")
        for claim in state.get("claims", [])
        if isinstance(claim, dict)
    )
    has_limitation = any(isinstance(value, str) and value.strip() for value in limitation_values)
    if not has_limitation:
        _add(
            issues,
            "tier.human_limitation_missing",
            "canonical package requires a limitation or flip condition",
            "/engineering_handoff/constraints",
            "WARNING",
        )
        missing = True

    has_reversible_action = any(
        isinstance(action, dict)
        and action.get("reversible") is True
        and isinstance(action.get("id"), str)
        and action["id"].strip()
        and isinstance(action.get("description"), str)
        and action["description"].strip()
        for action in handoff.get("safe_actions", [])
    )
    if not has_reversible_action:
        _add(
            issues,
            "tier.human_safe_action_missing",
            "canonical package requires a reversible safe action",
            "/engineering_handoff/safe_actions",
            "WARNING",
        )
        missing = True

    acceptance_tests = handoff.get("acceptance_tests")

    def valid_acceptance_test(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        for separator in ("=>", "->"):
            check, found, expected = value.partition(separator)
            if found and check.strip() and expected.strip():
                return True
        return False

    has_acceptance_test = isinstance(acceptance_tests, list) and any(
        valid_acceptance_test(test) for test in acceptance_tests
    )
    if not has_acceptance_test:
        _add(
            issues,
            "tier.acceptance_tests_missing",
            "canonical packages require at least one acceptance test formatted as 'check => expected' or 'check -> expected'",
            "/engineering_handoff/acceptance_tests",
            "WARNING",
        )
        missing = True

    return not missing


def _canonical_delivery_tier_contract(
    state: dict[str, Any],
    issues: list[Issue],
) -> bool:
    contract = state.get("contract", {})
    host_led = contract.get("research_workflow") == "host_led_v1"
    if contract.get("durability") != "canonical_package" or not host_led:
        return True

    summary = state.get("summary", {})
    status = summary.get("status")
    if status not in TERMINAL_DELIVERY_STATUSES:
        _add_once(
            issues,
            "tier.terminal_status_missing",
            "canonical packages require a terminal summary status",
            "/summary/status",
            "WARNING",
        )
        return False

    load_ids = summary.get("load_bearing_claim_ids")
    claims = indexed(state.get("claims"))
    load_set_met = (
        isinstance(load_ids, list)
        and bool(load_ids)
        and all(
            isinstance(claim_id, str)
            and claim_id in claims
            and claims[claim_id].get("load_bearing") is True
            for claim_id in load_ids
        )
    )
    delivery_sealed = (
        status == "BLOCKED"
        and summary.get("human_status") in DELIVERY_HUMAN_STATUS_SENTINELS
    )
    # Keep a finalizer-sealed terminal shortfall as delivery-incomplete; an
    # independently terminal package with no claims remains an evidence gap.
    if not load_set_met and not delivery_sealed:
        _add_once(
            issues,
            "tier.load_bearing_claims_missing",
            "canonical package requires a load-bearing claim set",
            "/summary",
            "WARNING",
        )

    handoff_met = _canonical_handoff_completeness(state, issues)
    reverification_met = True
    if host_led:
        load_ids = summary.get("load_bearing_claim_ids")

        def disposition_ids_are_valid(record: dict[str, Any]) -> bool:
            if not isinstance(load_ids, list):
                return False
            for field in ("corrected_claim_ids", "unverifiable_claim_ids"):
                values = record.get(field)
                if (
                    not isinstance(values, list)
                    or not all(isinstance(value, str) and value in load_ids for value in values)
                    or len(values) != len(set(values))
                ):
                    return False
            return True

        valid_records = [
            record
            for record in state.get("verification", [])
            if isinstance(record, dict)
            and record.get("kind") == "targeted_reverification"
            and record.get("completed") is True
            and record.get("checked_claim_ids") == load_ids
            and disposition_ids_are_valid(record)
            and isinstance(record.get("disposition"), str)
            and bool(record["disposition"].strip())
        ]
        reverification_met = bool(valid_records)
        if not reverification_met:
            _add_once(
                issues,
                "tier.targeted_reverification_missing",
                "host-led delivery requires a completed targeted re-verification record",
                "/verification",
                "ERROR" if status == "PASS" else "WARNING",
            )
    return load_set_met and handoff_met and reverification_met


def _validate_pass(
    state: dict[str, Any],
    events: list[dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
    evidence_map: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> None:
    summary = state.get("summary", {})
    decision = summary.get("decision")
    admitted = state.get("contract", {}).get("resource_envelope", {}).get("host", {}).get(
        "admitted_characters"
    )
    if not isinstance(decision, str) or not decision.strip():
        _add(issues, "status.pass_answer_missing", "PASS requires a non-empty bounded answer", "/summary/decision")
    elif isinstance(admitted, int) and len(decision) > admitted:
        _add(issues, "status.pass_answer_unbounded", "PASS answer exceeds the confirmed host envelope", "/summary/decision")

    load_ids = summary.get("load_bearing_claim_ids")
    if not isinstance(load_ids, list) or not load_ids:
        _add(issues, "status.pass_claim_set_empty", "PASS requires load-bearing claims", "/summary")
        load_ids = []
    claims = indexed(state.get("claims"))
    marked = {claim_id for claim_id, claim in claims.items() if claim.get("load_bearing") is True}
    if set(load_ids) != marked:
        _add(issues, "status.pass_claim_set_mismatch", "summary and claim load-bearing markers differ", "/summary")
    floor = state.get("contract", {}).get("evidence_floor", {}).get("minimum_load_bearing_claims")
    if not isinstance(floor, int) or isinstance(floor, bool) or len(load_ids) < floor:
        _add(issues, "status.evidence_floor", "confirmed evidence floor is not satisfied", "/summary")

    sources = indexed(state.get("sources"))
    origins = indexed(state.get("source_origins"))
    for claim_id in load_ids:
        claim = claims.get(claim_id)
        path = f"/claims/{claim_id}"
        if claim is None:
            continue
        if claim.get("status") not in PASSING_CLAIM_STATUSES:
            _add(issues, "claim.status", "load-bearing claim status cannot clear PASS", path)
        claim_type = claim.get("claim_type")
        if claim_type not in {"source-of-record", "empirical", "local-observation"}:
            _add(issues, "claim.type", "load-bearing claim type is missing or invalid", path)
        supporting = claim.get("supporting_evidence_ids")
        if not isinstance(supporting, list) or not supporting:
            _add(issues, "claim.evidence_missing", "load-bearing claim has no supporting evidence", path)
            continue
        if not _claim_has_available_evidence(claim, evidence_map, artifacts, raw_payloads):
            _add(issues, "claim.raw_missing", "load-bearing claim has no available raw artifact", path)
        if claim.get("applicability") != "checked":
            _add(issues, "claim.applicability", "load-bearing claim applicability is not checked", path)
        origin_ids = claim.get("source_origin_ids")
        if not isinstance(origin_ids, list) or not origin_ids:
            _add(issues, "claim.origin_missing", "load-bearing claim has no source origin", path)
        evidence_origins = {
            evidence_map[evidence_id].get("origin_id")
            for evidence_id in supporting
            if evidence_id in evidence_map
        }
        if isinstance(origin_ids, list) and set(origin_ids) != evidence_origins:
            _add(issues, "claim.origin_mismatch", "claim origins differ from supporting evidence", path)
        if claim_type == "empirical":
            independent = {
                origin_id
                for origin_id in evidence_origins
                if origins.get(origin_id, {}).get("independent") is True
            }
            if len(independent) < 2:
                _add(
                    issues,
                    "claim.origin_independence",
                    "empirical load-bearing claims require two independent source origins",
                    path,
                )
        for evidence_id in supporting:
            evidence = evidence_map.get(evidence_id)
            if evidence is None:
                continue
            if evidence.get("entailment") != "entailed":
                _add(issues, "claim.entailment", "load-bearing evidence is not marked entailing", path)
            if evidence.get("applicability") != "checked":
                _add(issues, "claim.applicability", "load-bearing evidence applicability is not checked", path)
        if claim_type == "source-of-record" and not _has_direct_t1_evidence(supporting, evidence_map, sources):
            _add(
                issues,
                "claim.source_of_record_missing",
                "source-of-record claim requires a directly fetched T1 source",
                path,
            )

    contract = state.get("contract", {})
    posture = contract.get("posture")
    # `profile` is the live cost-tier vocabulary: heavy buys a second deep
    # call specifically for an independent angle, so it -- and it alone
    # among the profiles -- inherits the old High/Ultra reinforcement bar.
    profile = contract.get("resource_envelope", {}).get("cost_budget", {}).get("profile")
    semantics = state.get("session", {}).get("contract_semantics")
    verification = [item for item in state.get("verification", []) if isinstance(item, dict)]
    if posture == "lookup":
        for claim_id in load_ids:
            claim = claims.get(claim_id, {})
            if not _has_direct_t1_evidence(claim.get("supporting_evidence_ids"), evidence_map, sources):
                _add(issues, "posture.lookup_primary_missing", "lookup PASS requires a directly fetched T1 source", f"/claims/{claim_id}")
    has_anti_lock_in = any(
        item.get("kind") == "anti_lock_in" and item.get("completed") is True for item in verification
    )
    if posture in {"scientific", "decision"} and profile == "heavy":
        if not has_anti_lock_in:
            _add(issues, "tier.anti_lock_in_missing", "anti-lock-in checkpoint is missing", "/verification")
    has_coverage_audit = any(
        item.get("kind") == "coverage_audit"
        and item.get("completed") is True
        and item.get("candidate_omissions_dispositioned") is True
        for item in verification
    )
    # synthesis's posture promise IS a coverage/omissions declaration (see
    # HARNESS.md's posture table), so it shares this gate at heavy even
    # though it has no anti-lock-in requirement of its own.
    if posture in {"scientific", "decision", "synthesis"} and profile == "heavy":
        if not has_coverage_audit:
            _add(issues, "tier.coverage_audit_missing", "coverage audit is incomplete", "/verification")
    elif posture == "decision" and not has_coverage_audit:
        # Decision posture always needs a documented coverage disposition --
        # which parts of the asked question this package does and does not
        # address (see HARNESS.md) -- regardless of profile. A package
        # created under the current contract semantics is held to this as a
        # hard failure on every profile, including standard (the
        # recommended default): a standard decision run that silently
        # answers half the asked question is exactly the failure this gate
        # exists to catch. A package created under an older semantics keeps
        # the historical WARNING-only behaviour, so it does not
        # retroactively invalidate the four canonical packages under
        # examples/field/: all predate this convention and are gated on
        # their recorded contract_semantics, not on their path or profile.
        if semantics in NEW_COVERAGE_AUDIT_SEMANTICS:
            _add(
                issues,
                "tier.coverage_audit_missing",
                "decision-posture packages require a coverage audit stating which parts of "
                "the asked question this package does and does not address",
                "/verification",
            )
        else:
            _add(
                issues,
                "posture.coverage_audit_recommended",
                "decision-posture packages should record a coverage audit stating which parts of "
                "the asked question this package does and does not address",
                "/verification",
                "WARNING",
            )
    if posture == "decision" and not any(
        isinstance(joint, dict)
        and joint.get("weakest_joint") is True
        and joint.get("adversarially_reviewed") is True
        for joint in state.get("inference_joints", [])
    ):
        _add(issues, "posture.decision_joint_missing", "decision inference joint review is missing", "/inference_joints")


def _validate_partial(
    state: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    raw_payloads: dict[str, bytes],
    evidence_map: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> None:
    load_ids = set(state.get("summary", {}).get("load_bearing_claim_ids", []))
    claims = indexed(state.get("claims"))
    unresolved = {
        claim_id
        for claim_id in load_ids
        if claim_id not in claims
        or claims[claim_id].get("status") not in PASSING_CLAIM_STATUSES
        or not _claim_has_available_evidence(
            claims[claim_id], evidence_map, artifacts, raw_payloads
        )
    }
    safe = False
    for action in state.get("engineering_handoff", {}).get("safe_actions", []):
        dependencies = action.get("depends_on_claim_ids") if isinstance(action, dict) else None
        if (
            isinstance(action, dict)
            and isinstance(action.get("id"), str)
            and action["id"]
            and action.get("reversible") is True
            and isinstance(dependencies, list)
            and not unresolved.intersection(dependencies)
        ):
            safe = True
            break
    if not safe:
        _add(
            issues,
            "status.partial_safe_action_missing",
            "PARTIAL requires a reversible action independent of every unresolved gap",
            "/engineering_handoff/safe_actions",
        )


def _validate_report_hash(
    session_dir: Path, current_hash: str, issues: list[Issue]
) -> None:
    report_path = session_dir / "report.html"
    if not report_path.exists():
        return
    if report_path.is_symlink() or not report_path.is_file():
        _add(issues, "report.invalid", "report.html is not a regular file", "/report.html")
        return
    try:
        document = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        _add(issues, "report.invalid", "report.html cannot be read as UTF-8", "/report.html")
        return
    match = REPORT_HASH_RE.search(html.unescape(document))
    if match is None or match.group(1) != current_hash:
        _add(issues, "report.stale", "report.html is not bound to the current canonical state", "/report.html")


def _validate_platform_durability(state: dict[str, Any], issues: list[Issue]) -> None:
    """Warn (never fail) when a session was produced without full guarantees.

    session.durability_capabilities (see state.new_state / _platform.py) is
    optional and backward-compatible: sessions created before this field
    existed, and the canonical fixtures under examples/field/, simply omit
    it. An absent record is treated as "not degraded" rather than warned on,
    matching the historical (fully-capable POSIX) contract those packages
    were actually produced under.
    """

    capabilities = state.get("session", {}).get("durability_capabilities")
    if not isinstance(capabilities, dict):
        return
    if capabilities.get("directory_fsync") is False:
        _add(
            issues,
            "session.degraded_durability",
            "session was produced on a host that cannot fsync a directory "
            "(e.g. Windows); a crash between a rename/unlink and its "
            "directory fsync could leave this package's most recent write "
            "unconfirmed on disk",
            "/session/durability_capabilities/directory_fsync",
            "WARNING",
        )
    if capabilities.get("private_file_mode") is False:
        _add(
            issues,
            "session.degraded_privacy",
            "session was produced on a host without POSIX private file "
            "modes (e.g. Windows); state.json, events.jsonl, and raw "
            "artifact bytes are not confined to the owning user by "
            "filesystem permissions",
            "/session/durability_capabilities/private_file_mode",
            "WARNING",
        )


def _validate_loaded_session(
    session_dir: Path,
    state: dict[str, Any],
    events: list[dict[str, Any]],
    event_errors: list[str],
    check_report: bool,
) -> ValidationReport:
    session_dir = Path(session_dir)
    issues: list[Issue] = []
    current_hash = state_sha256(state)
    strict_atomic = state.get("session", {}).get("contract_semantics") in STRICT_ATOMIC_SEMANTICS
    for message in validate_state_document(state):
        _add(issues, "state.structural", message, "/state")
    _validate_platform_durability(state, issues)
    _validate_event_lineage(state, events, event_errors, current_hash, issues)
    _validate_quota(state, events, issues, strict_atomic=strict_atomic)
    _validate_attempt_lifecycle(events, issues, strict_atomic=strict_atomic)
    if strict_atomic:
        _validate_atomic_occurrences(state, events, issues)
    artifacts, raw_payloads = _validate_artifacts(session_dir, state, events, issues)
    evidence_map = _validate_evidence(state, artifacts, raw_payloads, issues)

    status = state.get("summary", {}).get("status")
    if status not in VALID_DELIVERY_STATUSES:
        _add(issues, "status.invalid", "delivery status is invalid", "/summary/status")
    elif status == "PASS":
        _validate_pass(state, events, artifacts, raw_payloads, evidence_map, issues)
    elif status == "PARTIAL":
        _validate_partial(state, artifacts, raw_payloads, evidence_map, issues)
    canonical_delivery_met = _canonical_delivery_tier_contract(state, issues)
    profile_evidence_met = _profile_evidence_contract(
        state, artifacts, raw_payloads, evidence_map, issues
    )
    tier_contract_met = canonical_delivery_met and profile_evidence_met
    integrity_prefixes = (
        "state.",
        "event.",
        "quota.",
        "attempt.",
        "occurrence.",
        "artifact.",
        "evidence.",
        "capture.",
        "report.",
    )
    integrity_ok = not any(
        issue.level == "ERROR" and issue.code.startswith(integrity_prefixes) for issue in issues
    )
    summary = state.get("summary", {})
    human_recommendation = summary.get("human_recommendation", "")
    if not isinstance(human_recommendation, str):
        human_recommendation = ""
    human_status = (
        tier_shortfall_labels(issues)[0]
        if not tier_contract_met
        else summary.get("human_status", "")
    )
    if not isinstance(human_status, str):
        human_status = ""
    if check_report:
        _validate_report_hash(session_dir, current_hash, issues)
        integrity_ok = not any(
            issue.level == "ERROR" and issue.code.startswith(integrity_prefixes) for issue in issues
        )
    return ValidationReport(
        tuple(issues),
        current_hash,
        integrity_ok,
        tier_contract_met,
        human_recommendation,
        human_status,
    )


def validate_session(session_dir: Path, check_report: bool = True) -> ValidationReport:
    session_dir = Path(session_dir)
    with session_lock(session_dir):
        _recover_session_unlocked(session_dir)
        state = _load_state_unlocked(session_dir)
        events, event_errors = _read_events_unlocked(session_dir)
        return _validate_loaded_session(session_dir, state, events, event_errors, check_report)
