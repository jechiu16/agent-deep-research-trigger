# /deep Organizer Harness

Internal runtime bridge for the public flow in [SKILL.md](SKILL.md). Read it
only after the user selects `light`, `standard`, or `heavy`.

## Product Contract

- The selected host is the Organizer and sole conclusion author.
- D1/D2 are untrusted discovery memos, never evidence or verdicts.
- Re-verification corrects or annotates; it never suppresses delivery.
- Counts, not token-price guesses, stop external calls.
- Deliver one machine truth (`state.json`) and one human projection
  (`report.html`), plus their journal and raw evidence.

An epistemically `BLOCKED` package is still delivered. Only integrity failure
means the report is unsafe to act on.
Evidence gaps render as `證據不足 / EVIDENCE_INSUFFICIENT`; incomplete handoff
fields render as `交付不完整 / DELIVERY_INCOMPLETE`.

## Runtime Bridge

`ROOT` is the absolute directory containing the canonical `SKILL.md`:

```bash
ROOT="/absolute/path/to/the/canonical-skill"
CLI="$ROOT/.venv/bin/deep-research-state"
SESSION="/absolute/path/to/this-run-package"
```

Before confirmation, the only permitted command is local and read-only:

```bash
"$CLI" card --question '<question>' --posture decision
```

After confirmation, bind and start one contract:

```bash
"$CLI" draft --question '<question>' --posture decision \
  --profile standard --json
"$CLI" prepare --contract "/absolute/path/to/draft-contract.json" --json
"$CLI" confirm --prepared "/absolute/path/to/prepared.json" \
  --card-sha256 '<hash>' --registry-sha256 '<hash>' \
  --referenced-records-sha256 '<hash>' --confirmed-at '<timestamp>' \
  --confirmed-by user --json
"$CLI" init "$SESSION" --contract "/absolute/path/to/confirmed-contract.json" --json
```

The choice on the public card is the only user confirmation. `prepare` and
`confirm` are internal hash-binding steps, not a second prompt.

## Contract Shape

New runs use the compatibility tier `custom` and these authoritative fields:

```json
{
  "research_workflow": "host_led_v1",
  "conclusion_author": "host",
  "provider_reports_role": "discovery_only",
  "durability": "canonical_package",
  "resource_envelope": {
    "cost_budget": {
      "profile": "standard",
      "deep": 1,
      "search": 15,
      "free": "unlimited"
    }
  }
}
```

Copy the chosen vector from `budget_profiles.json`; a user-controlled override
may change numbers but never names tools. Exact routes remain in
`stage_permit_map`, and physical/time/storage limits remain defense-in-depth.
Require one reserved `verification` mapping and one
`final_inference_review/organizer_pass/host` mapping.

## Provider Routing

`provider_registry.json` is the only tool registry. Each route declares
`cost_class: deep|search|free`; deep routes also declare `cost_rank`. New tools
enter a class, never a profile.

A present credential is not execution readiness. The adapter, storage policy,
request boundary, and required environment must all pass local preflight.

1. Prefer direct source-of-record or local routes.
2. For D1, choose the lowest-rank ready provider unless source fit or privacy
   justifies another card-disclosed candidate.
3. Use D2 only for a material challenge, new angle, or expansion selected by
   the host after seeing D1 and current evidence.
4. Never call a bundle merely because budget remains.

The request boundary reserves before sending. Failed or uncertain calls remain
consumed. Transport polls are physically bounded but are not another `deep`
submit.

## Research Loop

1. Frame the decision, assumptions, exclusions, and flip conditions.
2. Run D1 when `deep > 0`; pass its useful hypotheses, contradictions,
   citations, and bounded session context to the Organizer.
3. Let the Organizer choose the smallest targeted checks. Paid search routes
   consume `search`; host/local/direct free routes consume `free`.
4. Capture qualifying source bytes and reconcile every load-bearing claim:
   `claim -> evidence -> source + source_origin -> raw artifact`.
5. Correct claims disproved by direct evidence. Mark unresolved claims and
   their revisit trigger; do not convert model agreement into corroboration.
6. Add a `targeted_reverification` record covering the final load-bearing claim
   IDs, with corrected and unverifiable IDs plus a concise disposition.
7. The host writes the bounded decision and development handoff, then validates
   and renders.

Minimal re-verification record:

```json
{
  "id": "VR1",
  "kind": "targeted_reverification",
  "completed": true,
  "checked_claim_ids": ["C1"],
  "corrected_claim_ids": [],
  "unverifiable_claim_ids": [],
  "disposition": "直接來源支持 C1；未採用 D1 的兩個未驗證延伸。"
}
```

## Execution And Delivery

Use boundary-owned calls; do not send a separate paid permit:

```bash
"$CLI" execute "$SESSION" --action-id A1 --stage verification \
  --route openalex --query '<targeted query>' --json
"$CLI" deep-submit "$SESSION" --action-id D1 --stage investigation \
  --route perplexity --query '<bounded brief plus context>' --json
"$CLI" host-capture "$SESSION" --payload "/absolute/path/to/capture-file" \
  --artifact-id HC1 --source-url '<url>' --source-title '<title>' \
  --upstream-key '<upstream>' --fidelity host_rendered \
  --marginal-purpose '<claim or uncertainty checked>' --json
"$CLI" patch "$SESSION" --patch "/absolute/path/to/state-patch.json" --json
"$CLI" validate "$SESSION" --json
```

If a call would exceed `deep` or `search`, the boundary sends nothing and
journals `budget_exhausted`. `render` adds the unresolved budget gap to
`state.json`, stops external work, and still writes `report.html`.

Human narrative fields, handoff, limitations, and recommendations are
Traditional Chinese. Preserve exact excerpts, titles, URLs, IDs, hashes,
provider names, and diagnostics. Acceptance tests use
`檢查方式 => 預期結果`.

`state.json`, `events.jsonl`, and `raw/` are the canonical package: deterministic,
hash-chained, byte-exact, and the sole audit surface. Never touch that
guarantee. `report.html` is the separate human projection of it, and has two
tracks:

- **Host-authored (default).** You write `report.html` yourself; see
  [Report Authoring](#report-authoring). It reads far better than a fixed
  template and can adapt its shape to the question.
- **Deterministic fallback.** `"$CLI" render "$SESSION" --json` renders a
  fixed, always-faithful projection instead. Use this only when you cannot
  author a report yourself -- a crash, budget exhaustion mid-session, or a
  degraded run -- never as a stylistic choice.

To author your own report:

```bash
"$CLI" finalize "$SESSION" --json
# write "$SESSION/report.html" yourself; embed the returned state_sha256
"$CLI" render "$SESSION" --host-authored --json
```

`finalize` seals the same budget-gap annotation and insufficient-tier BLOCKED
status `render` would seal, and returns the exact `state_sha256` the report
must embed in `<meta data-state-sha256="...">` -- calling it again with
nothing else changed returns the same hash. Write the file, then
`render --host-authored` binds it to the sealed state and journals
`report_generated`; if the file is missing or its embedded hash does not
match, this fails closed instead of recording a stale report. Do not patch
state between the two calls -- if you must, re-run `finalize` and rewrite the
file before `render --host-authored`.

## Report Authoring

Read `state.json` in full before writing. Every claim, number, and quotation
in the report must come from it -- rearrange, group, summarize, and choose
emphasis freely, but never introduce a fact the canonical package does not
contain, and never drop a recorded limitation or unverified disposition. One
worked reference calibrated to this standard:
`examples/field/04-duckdb-concurrency-boundary/session/report.html` -- an
example of the intended standard, not a template to fill in.

Hard constraints:

- One self-contained HTML file: no JavaScript, no remote assets, no external
  fonts or CSS. It must still open correctly from disk years from now.
- Embed `<meta data-state-sha256="{the hash finalize returned}">` exactly --
  this is how `deep-research-state validate` binds the report to this exact
  package; get it wrong or omit it and validation reports `report.stale`.
- All narrative in Traditional Chinese (zh-Hant-TW). Exact excerpts, source
  titles, URLs, IDs, and hashes stay verbatim in their original language.
- Link preserved evidence under `raw/` only where `artifact_index` permits:
  `availability == "available"`, `include_in_html is True`, and
  `sensitivity` in `{"public", "internal"}` -- match the exact gate in
  `research_harness/rendering.py::_artifact_link`.
- Must read correctly in both light and dark browser themes, and print
  sensibly.

Design intent, not a template -- fit the shape to the question:

- Answer first. The reader already knows the question; put it in small
  supporting text, not the headline. The headline is what to do or what is
  true -- use `summary.headline` if present, else `summary.human_recommendation`.
- Display type is for one line. `summary.decision` is body copy, not a
  headline-sized wall of text.
- Keep three different lists visually and structurally separate:
  `engineering_handoff.constraints` (what this run did not do), each claim's
  `would_change_if` (what would overturn it), and `open_questions` (what is
  still unresolved). Merging them into one flat undifferentiated list is the
  single worst defect this instruction replaces -- do not reintroduce it.
- Do not break Chinese sentence flow with inlined English source titles; use
  numbered references with a source list instead.
- Evidence is the product: load-bearing claims, their status, and their
  evidence chain belong in the default view. Collapse only genuine machinery
  -- quota tables, hashes, validation internals.
- Omit a section entirely rather than rendering an empty placeholder like
  「尚未記錄」.

Two field-shape notes:

- `summary.human_status` is a short one-line note on what this run actually
  did (≤40 全形字) -- not a narrative. The bounded conclusion belongs in
  `summary.decision`, the recommendation in `summary.human_recommendation`.
- `summary.headline` is optional: an action phrase, ≤20 全形字, used as the
  report's headline and `h1`. Omit it and both tracks fall back to
  `summary.human_recommendation`; existing packages that predate this field
  keep validating unchanged.

## Recovery

```bash
"$CLI" status "$SESSION" --json
"$CLI" deep-pending "$SESSION" --json
"$CLI" recover "$SESSION" --json
"$CLI" render "$SESSION" --json
```

No token means a deep attempt is consumed and not pollable. A recorded token
may be polled with a new poll action ID; never resubmit the same deep action.
