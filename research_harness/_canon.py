"""Shared canonical-form primitives.

Every hash binding in the runtime (contract cards, registry snapshots, state
revisions, event chains, artifact policies) depends on one exact byte form.
That byte form lives here and nowhere else — a second copy is a drift risk,
not a convenience.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


RETENTION_RANK = {"forbidden": 0, "ephemeral": 1, "session": 2, "persistent": 3}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    """SHA-256 of the canonical JSON form."""

    return hashlib.sha256(canonical_json(value)).hexdigest()


def is_count(value: Any) -> bool:
    """A non-negative integer count (bool excluded)."""

    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_positive_count(value: Any) -> bool:
    return is_count(value) and value > 0


def indexed(items: Any) -> dict[str, dict[str, Any]]:
    """Index a state section's entries by their string id."""

    if not isinstance(items, list):
        return {}
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
