#!/usr/bin/env python3
"""Validate golden /deep transcripts.

The validator is intentionally structural. It does not judge factual truth; it
checks that each transcript exercises the Organizer protocol: contract before
actions, state discipline, evidence status, verification, spend, and handoff.
"""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT_DIR = ROOT / "examples" / "transcripts"

GENERIC_REQUIRED = [
    "/deep",
    "Contract confirmed:",
    "depth=",
    "independence=",
    "strictness=",
    "## Actions",
    "## Evidence Status",
    "## Reconciliation",
    "## Verification",
    "Verification floor completed",
    "## Delivery",
    "Research contract:",
    "Key finding",
    "Load-bearing claim",
    "Spend and artifacts:",
    "Recommendation:",
    "Handoff:",
]

STATUS_PATTERN = re.compile(
    r"\b(corroborated|single-source|corroborated-same-family|disputed|retired|unverified)\b"
)

SCENARIOS = {
    "quick-fact.md": {
        "label": "quick-fact",
        "preset": "fast",
        "state": "skipped-single-action",
        "required": [
            "Research State: skipped",
            "Ledger: not required",
            "source-of-record",
            "State file: skipped",
            "Spend: `$0.00`",
        ],
    },
    "literature-review.md": {
        "label": "literature-review",
        "preset": "standard",
        "state": "required",
        "required": [
            "Created Research State:",
            "Updated Research State:",
            "reports/deep_state_20260709_rag_hallucination.md",
            "scholar",
            "paper claims",
            "single-source",
        ],
    },
    "decision-critical.md": {
        "label": "decision-critical",
        "preset": "decision",
        "state": "required",
        "required": [
            "Created Research State:",
            "Updated Research State:",
            "cross-family-blind",
            "isolated",
            "disputed",
            "do **not** approve",
        ],
    },
}


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    _, block, _rest = text.split("---", 2)
    out = {}
    for line in block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def find_position(text: str, needle: str) -> int:
    return text.find(needle)


def validate_file(path: Path, spec: dict) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = []
    meta = frontmatter(text)

    if meta.get("scenario") != spec["label"]:
        errors.append(f"frontmatter scenario should be {spec['label']!r}")
    if meta.get("preset") != spec["preset"]:
        errors.append(f"frontmatter preset should be {spec['preset']!r}")
    if meta.get("state") != spec["state"]:
        errors.append(f"frontmatter state should be {spec['state']!r}")

    for needle in GENERIC_REQUIRED + spec["required"]:
        if needle not in text:
            errors.append(f"missing required marker: {needle}")

    if "TODO" in text or "TBD" in text:
        errors.append("contains TODO/TBD placeholder")

    contract_pos = find_position(text, "Contract confirmed:")
    actions_pos = find_position(text, "## Actions")
    if contract_pos == -1 or actions_pos == -1 or contract_pos > actions_pos:
        errors.append("contract confirmation must appear before actions")

    if not STATUS_PATTERN.search(text):
        errors.append("no recognized evidence status found")

    if spec["state"] == "required":
        if text.count("```md") < 2:
            errors.append("required-state transcript should show initial and updated state snapshots")
        if "ledger=" not in text:
            errors.append("required-state transcript should include ledger path")

    return errors


def validate_all() -> dict:
    results = {}
    for filename, spec in SCENARIOS.items():
        path = TRANSCRIPT_DIR / filename
        if not path.exists():
            results[filename] = ["missing file"]
            continue
        results[filename] = validate_file(path, spec)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate golden /deep transcripts")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    results = validate_all()
    ok = all(not errors for errors in results.values())
    if args.json:
        print(json.dumps({"ok": ok, "results": results}, ensure_ascii=False, indent=2))
    else:
        print("Golden transcript validation")
        for filename, errors in results.items():
            if errors:
                print(f"FAIL {filename}")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"OK   {filename}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
