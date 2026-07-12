#!/usr/bin/env python3
"""Internal calibration report: how trustworthy is a PASS on this machine?

Pure reader. Zero network, zero LLM calls, no cache — every number here is
recomputed from the session directories and (optional) human annotations
given on the command line, every time. This is a report, not a judge: it
does not re-run verification and it does not decide whether a session
should have passed.

Inputs, per session directory (anything containing a state.json written by
research_harness, schema_version 2.0):

- session.id, framing.question, summary.status, summary.load_bearing_claim_ids
- claims[].status
- verification[] (see _verification_yield for why this is a proxy today)
- provider_spool/*.raw.json for usage.cost.total_cost (see _extract_cost_usd)

Optional ground truth comes from a JSONL annotations file (see
examples/eval/annotations.example.jsonl and examples/eval/README.md), joined
to sessions by resolved session_dir path.

Design notes / known gaps (found while building this, not covered by the
schema docs):

- `verification[]` entries of kind="verifier" have no field that records
  whether the verifier actually found something wrong. The nearest-looking
  field, `produced_candidate`, means the opposite of what it sounds like: it
  must be False on a legitimate High-tier verifier (it records that the
  verifier did NOT itself originate the candidate conclusion — an
  independence check, not a correction-detection flag). Using it as a yield
  signal would invert the metric, since every clean PASS has it False. So
  this always uses the documented fallback proxy — claims whose status is
  not "corroborated" — and always labels it a proxy.
- Cost extraction covers the four nesting shapes actually used by the
  enabled adapters: response.usage.cost.total_cost (perplexity_deep, async,
  nested under "response"), usage.cost.total_cost (sonar, sync, top level),
  costDollars.total (exa, sync, top level), and meta.cost_usd (openalex,
  sync, top level). A raw payload is expected to match at most one shape
  since each file is one provider's response.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Optional


QUESTION_TRUNCATE_LEN = 80
PASSING_CLAIM_STATUS = "corroborated"
VALID_VERDICTS = frozenset({"correct", "incorrect", "partial"})


# ── Filesystem discovery ────────────────────────────────────────────────────


def find_session_dirs(paths: list[str]) -> tuple[list[Path], list[str]]:
    """Resolve CLI path arguments to a deduplicated, sorted list of session dirs.

    Each argument may be a session directory (state.json directly inside it),
    a root directory containing many session directories at any depth, or a
    direct path to a state.json file itself. Returns (session_dirs, warnings).
    """
    warnings: list[str] = []
    found: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            warnings.append(f"{raw}: path does not exist")
            continue
        if path.is_file():
            if path.name != "state.json":
                warnings.append(f"{raw}: not a state.json file or a directory")
                continue
            found.add(path.parent.resolve())
            continue
        matches = list(path.rglob("state.json"))
        if not matches:
            warnings.append(f"{raw}: no state.json found under this path")
            continue
        found.update(match.parent.resolve() for match in matches)
    return sorted(found), warnings


def _read_json(path: Path) -> tuple[Optional[Any], Optional[str]]:
    """Best-effort JSON read. Returns (value, error_message); never raises."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"{path}: cannot read file ({exc})"
    try:
        return json.loads(raw), None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{path}: invalid JSON ({exc})"


# ── Per-session extraction ──────────────────────────────────────────────────


def _truncate(text: str, limit: int = QUESTION_TRUNCATE_LEN) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _verification_yield(state: dict[str, Any]) -> tuple[int, bool]:
    """Return (yield_count, is_proxy) — see the module docstring for why this
    is always a proxy against today's schema: count claims not corroborated.
    """
    claims = state.get("claims")
    if not isinstance(claims, list):
        return 0, True
    count = 0
    for claim in claims:
        if not isinstance(claim, dict):
            count += 1  # can't confirm corroborated -> treat as unresolved
            continue
        if claim.get("status") != PASSING_CLAIM_STATUS:
            count += 1
    return count, True


def _extract_cost_usd(session_dir: Path) -> tuple[Optional[float], list[str]]:
    """Sum provider-reported cost across provider_spool/*.raw.json.

    Returns None (not 0.0) when the provider_spool directory itself does not
    exist, to distinguish "no cost visibility" from "looked and found zero".
    See the module docstring for the four nesting shapes handled (perplexity_
    deep, sonar, exa, openalex).
    """
    spool = session_dir / "provider_spool"
    if not spool.is_dir():
        return None, []
    warnings: list[str] = []
    total = 0.0
    for raw_path in sorted(spool.glob("*.raw.json")):
        payload, error = _read_json(raw_path)
        if error:
            warnings.append(error)
            continue
        if not isinstance(payload, dict):
            continue

        usage: Optional[dict[str, Any]] = None
        response = payload.get("response")
        if isinstance(response, dict) and isinstance(response.get("usage"), dict):
            usage = response["usage"]
        elif isinstance(payload.get("usage"), dict):
            usage = payload["usage"]
        if isinstance(usage, dict):
            cost_obj = usage.get("cost")
            total_cost = cost_obj.get("total_cost") if isinstance(cost_obj, dict) else None
            if isinstance(total_cost, (int, float)) and not isinstance(total_cost, bool):
                total += float(total_cost)
                continue

        cost_dollars = payload.get("costDollars")  # exa
        if isinstance(cost_dollars, dict):
            exa_total = cost_dollars.get("total")
            if isinstance(exa_total, (int, float)) and not isinstance(exa_total, bool):
                total += float(exa_total)
                continue

        meta = payload.get("meta")  # openalex
        if isinstance(meta, dict):
            openalex_cost = meta.get("cost_usd")
            if isinstance(openalex_cost, (int, float)) and not isinstance(openalex_cost, bool):
                total += float(openalex_cost)
    return total, warnings


def extract_session(session_dir: Path) -> tuple[Optional[dict[str, Any]], list[str]]:
    """Extract one session's calibration row. Returns (row_or_None, warnings).

    row is None when state.json is missing, unreadable, or not an object —
    the caller is expected to log the warnings and skip the session, not
    abort the run.
    """
    state, error = _read_json(session_dir / "state.json")
    if error:
        return None, [error]
    if not isinstance(state, dict):
        return None, [f"{session_dir / 'state.json'}: not a JSON object"]

    session_obj = state.get("session")
    session_id = (
        session_obj.get("id")
        if isinstance(session_obj, dict) and isinstance(session_obj.get("id"), str)
        else session_dir.name
    )

    framing = state.get("framing")
    question_raw = framing.get("question") if isinstance(framing, dict) else None
    question = _truncate(question_raw) if isinstance(question_raw, str) else ""

    summary = state.get("summary")
    status = (
        summary.get("status")
        if isinstance(summary, dict) and isinstance(summary.get("status"), str)
        else "UNKNOWN"
    )
    load_bearing_ids = summary.get("load_bearing_claim_ids") if isinstance(summary, dict) else None
    load_bearing_count = len(load_bearing_ids) if isinstance(load_bearing_ids, list) else 0

    yield_count, yield_is_proxy = _verification_yield(state)
    cost_usd, cost_warnings = _extract_cost_usd(session_dir)

    row: dict[str, Any] = {
        "session_dir": str(session_dir),
        "session_id": session_id,
        "question": question,
        "status": status,
        "load_bearing_claims": load_bearing_count,
        "verification_yield": yield_count,
        "verification_yield_is_proxy": yield_is_proxy,
        "total_cost_usd": cost_usd,
        "ground_truth_verdict": None,
    }
    return row, cost_warnings


# ── Annotations ──────────────────────────────────────────────────────────────


def load_annotations(path: Path) -> tuple[dict[Path, dict[str, Any]], list[str]]:
    """Load a ground-truth annotations JSONL file, keyed by resolved session_dir.

    Malformed or invalid lines are warned about and skipped, not fatal.
    """
    warnings: list[str] = []
    by_dir: dict[Path, dict[str, Any]] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"{path}: cannot read annotations file ({exc})"]

    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"{path}:{lineno}: invalid JSON ({exc})")
            continue
        if not isinstance(record, dict):
            warnings.append(f"{path}:{lineno}: annotation is not a JSON object")
            continue
        session_dir = record.get("session_dir")
        verdict = record.get("ground_truth_verdict")
        if not isinstance(session_dir, str) or not session_dir:
            warnings.append(f"{path}:{lineno}: missing session_dir")
            continue
        if verdict not in VALID_VERDICTS:
            warnings.append(
                f"{path}:{lineno}: ground_truth_verdict must be one of {sorted(VALID_VERDICTS)}, got {verdict!r}"
            )
            continue
        by_dir[Path(session_dir).resolve()] = record
    return by_dir, warnings


# ── Aggregation ──────────────────────────────────────────────────────────────


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll per-session rows up into the summary block. Recomputed, not cached."""
    pass_rows = [row for row in rows if row["status"] == "PASS"]
    annotated_pass = [row for row in pass_rows if row.get("ground_truth_verdict") is not None]
    pass_correct_rate: Optional[float] = None
    if annotated_pass:
        correct = sum(1 for row in annotated_pass if row["ground_truth_verdict"] == "correct")
        pass_correct_rate = correct / len(annotated_pass)

    known_costs = [row["total_cost_usd"] for row in rows if row["total_cost_usd"] is not None]
    mean_cost = statistics.fmean(known_costs) if known_costs else None

    yields = [row["verification_yield"] for row in rows]
    mean_yield = statistics.fmean(yields) if yields else None

    return {
        "sessions_scanned": len(rows),
        "pass_count": len(pass_rows),
        "pass_annotated_count": len(annotated_pass),
        "pass_correct_rate": pass_correct_rate,
        "mean_cost_usd": mean_cost,
        "sessions_with_unknown_cost": sum(1 for row in rows if row["total_cost_usd"] is None),
        "mean_verification_yield": mean_yield,
    }


# ── Rendering ────────────────────────────────────────────────────────────────


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(rows: list[dict[str, Any]], summary: dict[str, Any], warnings: list[str]) -> str:
    lines = ["# Calibration report", ""]
    if rows:
        lines.append("| session_id | question | status | load-bearing | verif. yield (proxy) | cost (USD) | ground truth |")
        lines.append("|---|---|---|---|---|---|---|")
        for row in rows:
            cost = "n/a" if row["total_cost_usd"] is None else f"{row['total_cost_usd']:.4f}"
            verdict = row["ground_truth_verdict"] or "-"
            lines.append(
                f"| {_md_escape(row['session_id'])} | {_md_escape(row['question']) or '-'} | {row['status']} | "
                f"{row['load_bearing_claims']} | {row['verification_yield']} | {cost} | {verdict} |"
            )
    else:
        lines.append("_No sessions found._")

    lines.extend(["", "## Summary", ""])
    lines.append(f"- sessions scanned: {summary['sessions_scanned']}")
    lines.append(f"- PASS count: {summary['pass_count']}")
    if summary["pass_correct_rate"] is None:
        lines.append("- PASS correct rate: n/a (no annotated PASS sessions)")
    else:
        lines.append(
            f"- PASS correct rate: {summary['pass_correct_rate']:.1%} "
            f"({summary['pass_annotated_count']} PASS sessions annotated)"
        )
    if summary["mean_cost_usd"] is None:
        lines.append("- mean cost (USD): n/a (no session had provider_spool visibility)")
    else:
        lines.append(
            f"- mean cost (USD): {summary['mean_cost_usd']:.4f} "
            f"({summary['sessions_with_unknown_cost']} session(s) with unknown cost excluded)"
        )
    if summary["mean_verification_yield"] is None:
        lines.append("- mean verification yield: n/a")
    else:
        lines.append(f"- mean verification yield (proxy, see README): {summary['mean_verification_yield']:.2f}")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    return "\n".join(lines) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────────────


def run(paths: list[str], annotations_path: Optional[str]) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Do the actual work; kept separate from argparse/printing for testability."""
    session_dirs, warnings = find_session_dirs(paths)

    annotations: dict[Path, dict[str, Any]] = {}
    if annotations_path:
        annotations, annotation_warnings = load_annotations(Path(annotations_path))
        warnings.extend(annotation_warnings)

    rows: list[dict[str, Any]] = []
    for session_dir in session_dirs:
        row, row_warnings = extract_session(session_dir)
        warnings.extend(row_warnings)
        if row is None:
            continue
        annotation = annotations.get(session_dir)
        if annotation is not None:
            row["ground_truth_verdict"] = annotation["ground_truth_verdict"]
        rows.append(row)

    rows.sort(key=lambda row: row["session_dir"])
    summary = aggregate(rows)
    return rows, summary, warnings


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Internal calibration report for /deep session PASS trustworthiness.")
    parser.add_argument(
        "paths",
        nargs="+",
        help="Session directories, or root directories containing many session directories (each with a state.json).",
    )
    parser.add_argument("--annotations", help="Path to a ground-truth annotations JSONL file.")
    parser.add_argument("--json", action="store_true", help="Print one JSON object instead of a markdown report.")
    args = parser.parse_args(argv)

    rows, summary, warnings = run(args.paths, args.annotations)

    if args.json:
        payload = {"sessions": rows, "summary": summary, "warnings": warnings}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(render_markdown(rows, summary, warnings), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
