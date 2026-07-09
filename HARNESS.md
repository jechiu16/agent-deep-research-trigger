# Research Harness Specification

**This file is host-neutral.** Any capable tool-using LLM agent (Claude Code, Codex, or another) can act as the Organizer. Host bindings live in [SKILL.md](SKILL.md) (Claude Code) and [AGENTS.md](AGENTS.md) (Codex).

## What this is

`/deep` is not a research tool — it is a **trigger** that hands the host agent a portfolio of research workers and a discipline for deploying them. The harness is:

- **single-execution** — one trigger, one research session, one verdict
- **stateful** — evidence, spend, and open disputes live in a Research State file, not in anyone's working memory
- **bounded** — a depth preset sets the spending spirit; the loop terminates on settled claims or diminishing returns
- **hybrid-path** — evidence is shared where reuse is safe, re-derived independently where verification demands it

The objective: **maximum information gain per dollar across the whole worker portfolio** — not maximum thoroughness, not minimum cost. The loop's steering question is always: *which load-bearing claim is weakest right now, and what is the cheapest action that strengthens it?*

## Vocabulary

| Term | Meaning |
|---|---|
| Trigger | `/deep <question> [hints]` — wakes the Organizer |
| Organizer | the host agent running this loop; owns all judgment |
| Harness | this spec: workers manifest + state schema + loop contract |
| Loop | inspect → choose → execute → normalize → reconcile → terminate? |
| Hooks | bounded Organizer judgments at fixed points — not code |
| Workers | the engines below: deterministic, single-call, resumable |

## Workers manifest

Engine CLI: `scripts/deep_research.py` (deps `requests` + `python-dotenv`; `google-genai` for gemini). One call = one action. Stdout = one JSON object (`report`, `report_path`, `usage`, `cost_estimate_usd`, `wall_time_s`); async workers print a **resume token** (`provider:id`) to stderr and carry a `resume` field in error JSON. Reports land in `<cwd>/reports/`. Keys resolve: process env → nearest `.env` from cwd upward → `.env` beside this file.

| Worker | Invocation core | Cost / latency | Output | Index family | Notes |
|---|---|---|---|---|---|
| cascade | `--provider cascade` | ~$0.10–0.15 / ~30 s | 4 merged probes: direct／counter／landscape／falsifier, cited | Perplexity | canonical opening move; raises if all probes fail |
| sonar | `--provider sonar` | ~$0.01 / ~3 s | one grounded cited answer | Perplexity | targeted lookups, dispute adjudication |
| scholar | `--provider scholar --effort minimal…high` | free / ~5 s | 5–40 papers (TLDR, citation counts, PDFs) | Semantic Scholar | **keyword queries, not questions**; 1 req/s — never parallel; works keyless (stricter limits) |
| perplexity | `--provider perplexity --effort medium/high` | $0.5–1 / 2–5 min | long cited report | Perplexity | async+resume; ~5 RPM; `minimal` is UNGROUNDED — never use for real research |
| openai | `--provider openai --effort medium/high` | $0.4–8 / 5–25 min | long cited report | OpenAI (2nd family) | `high`→o3, else o4-mini with tool caps; async+resume; needs a verified org |
| gemini | `--provider gemini` | varies / 3–10 min | long report, sources inline | Google (3rd family) | async+resume |
| deepseek | `--provider deepseek --files a.md --files b.md "instruction"` | ~free / 1–5 min | processed artifact | none — no retrieval | **processor only**: merges, claim tables, comparisons; never a researcher (hallucinates ungrounded) |
| host-search | host's native web search | usually free | search results | host-dependent | spot-checks; hosts without one use `sonar` instead |
| host-fetch | host's native URL fetch | usually free | page content | — | read a specific source when a claim hinges on it |

**Failure policy**:
- a failed worker never re-runs paid work without a decision; poll died or timed out → `--resume "provider:id"` — never re-pay for a lost job
- a worker that fails **before submission**（transport／proxy／auth errors — common in sandboxed hosts）is not resumable: record it in the ledger, then fall back to a host-native equivalent or another worker
- **evidence quality beats tool loyalty**: if host-native search alone satisfies a shallow contract when workers are unavailable, that's a valid session — note the substitution in the log
- example commands in this spec use bare `python` for illustration; the host binding's interpreter policy always wins

## Hooks are hybrid

**Mechanical（code-guaranteed — never depends on Organizer discipline）**:
- every worker call from `medium` depth up passes `--ledger reports/deep_state_<slug>.ledger.jsonl`（recommended even at shallow — it's free）— the engine appends its own completion／failure line（provider, cost, wall time, artifact path, resume token）to an append-only JSONL; the state file's ledger table is the Organizer's curated render of it
- blind-verification queries are template-generated（see isolated branch）
- rate limiting and resume tokens live in the engine

**Judgment（Organizer）**: claim curation, reconcile verdicts, branch typing, batch choice, termination.

## Research State

From `medium` depth up — or whenever more than one action runs（a failure plus its fallback counts as two）— keep state on disk: `reports/deep_state_<yyyymmdd>_<slug>.md`, rewritten after every reconcile hook. A quick single-action question skips it; the report file is the artifact.

```
# Research State: <question>
contract: depth=<shallow/medium/deep> ｜ independence=<bar> ｜ strictness=<level> ｜ status: running/done ｜ started: <ts>
framing: <core question; exclusions; what success looks like>

## Spend ledger（curated render of the machine-written .ledger.jsonl）
| # | action | worker | actual$ | artifact |
running total: $X.XX

## Evidence pool
| id | claim | status | sources (worker → report path) | independence |
   status ∈ corroborated / single-source / disputed / retired

## Open
gaps: <what's still uncovered>
disputes: <claim ids + what evidence would settle each>

## Log
- <n>: chose <batch> because <one line>
```

## The Loop

**0 INIT** — Read the conversation context. If the framing is ambiguous in ways that change the answer (goal, region, timeframe, stakes), ask ≤3 clarifying questions — skip on "go"／"快". Establish the **research contract**（three axes, below）: infer defaults from the question's stakes, present them for a one-tap confirm, skip entirely for obvious quick questions. Write the initial state file.

**1 INSPECT** — Read the state. What is the weakest load-bearing element right now: uncovered ground, a single-source claim that matters, an open dispute? On the first iteration, also check `<cwd>/reports/` for recent artifacts on overlapping topics — reusing a past paid report through the processor is ~free（flag staleness against the question's time-sensitivity）.

**2 CHOOSE** — Pick the next **batch** of actions with the best expected information gain per dollar. Iterations are coarse — batch parallel-safe actions into one wave; never micro-loop one worker at a time. Branch typing per action:

- **shared branch** — builds on the pool (queries refined by earlier findings)
- **isolated branch** — blind verification: the query is **template-generated**, never composed freely by the Organizer（who has read the pool and would leak framing）: `Verify or refute: <claim verbatim>. What is the primary evidence for and against?` — carries the bare claim only; prefer a different index family than the claim's current sources. For **source-of-record claims**（official prices, documented limits, dated announcements）, independently fetching an alternate authoritative page counts as the blind check — no model needed
- **targeted lookup** — one sonar／host-search probe for a small gap or a specific dispute

**Cost ordering（the shared-trunk economy）**: exhaust free moves first — reasoning over the existing pool（Organizer or deepseek）costs nothing and comes before any retrieval; then $0.01 targeted lookups; paid retrieval last, only for what the pool provably can't answer. The counterweight: savings come from sharing, trust comes from *not* sharing — the independence bar decides how much must be re-derived in isolation, and that is never traded away for cost.

Typical opening: `cascade ∥ scholar` (cheap heterogeneous retrieval). **If the opening fully answers the question, stop and deliver** — don't spend the band because it exists.

**3 EXECUTE** — Launch the batch (async workers in the background; keep the conversation alive). Respect rate limits from the manifest. **Answer-first**: when the opening wave lands, give the user the provisional read（marked as provisional）while deeper actions run — their reaction is live steering input for the remaining spend.

**4 NORMALIZE（hook）** — Per artifact: extract the claims that bear on the question, with provenance（worker, report path）. Long reports（>~3k tokens）: delegate the draft extraction to `deepseek`（free）and curate the result; short outputs: extract directly. The pool is **two-layer**: a compact layer（the claims table in the state file — what the Organizer re-reads every iteration, verdict-relevance weighted but not hard-capped）and a full layer（the report files — what deepseek reads when processing; its 1M-token window minus 20% headroom is the size bound, which in practice never binds）. Merge into the pool; tag independence by index family.

**5 RECONCILE（hook）** — Compare claims across sources: agreements → `corroborated`; conflicts → `disputed` plus a note on what would settle each. **Only chase unresolved disagreements** — settled ground gets no more spend. Update gaps, append one log line, rewrite the state file.

**6 TERMINATE?** — Stop when: load-bearing claims meet the contract's independence bar at its strictness level, OR marginal gain is clearly below marginal cost, OR spend has clearly outgrown the contract's depth without an obvious reason to continue. Depth is a spending spirit, not a ceiling — when further spend is clearly justified, say so to the user（check in if the overshoot would be large）and continue. Otherwise loop to 1.

## The research contract（three independent axes, set at INIT）

One card, three axes — the Organizer infers defaults from the question's stakes and presents them for a one-tap confirm; obvious quick questions skip the card entirely.

| Axis | Options（composition, not dollar cutoffs） |
|---|---|
| **Depth**（spend appetite） | shallow: a probe wave or one quick answer ／ medium: probes + one or two standard reports ／ deep: multiple deep engines, iterated |
| **Independence bar**（what it takes to believe a claim） | single source OK ／ load-bearing claims ≥2 sources ／ ≥2 index families + one blind isolated pass |
| **Strictness**（chase persistence before stopping） | first satisfactory answer ／ close the obvious gaps ／ chase disputes until resolved or provably unresolvable |

Preset paths（one pick instead of three）: **快查** = shallow＋single＋first ／ **日常** = medium＋2-sources＋gaps ／ **拍板** = deep＋families-blind＋chase. An explicit user budget（"預算 N"）overrides the depth axis.

**Prices are never normative**: any dollar figure in this spec is indicative at current list prices — the workers manifest is the live price source, presets are defined by worker composition, and nothing in the code enforces a budget cutoff.

## Verification floor（non-negotiable）

Before delivery, the 2–3 most load-bearing claims (headline numbers, dates, "X announced Y") get an independent spot-check — host-search where free, sonar probes otherwise. Discrepancies are flagged prominently in the verdict. Research reports are hypotheses, not facts.

## Delivery

In the user's language:

- key findings, each traceable to a pool claim and its status（corroborated N-way ／ single-source ／ disputed）
- unresolved disputes stated plainly — an honest open question beats laundered certainty
- actual spend vs the contract; state file and report paths
- your recommendation for the user's actual decision, separated from the evidence

## Query-writing standards

English; one core question per worker run; explicit exclusions（"focus on X; ignore Y"）; a context clause（"in the context of …"）; ask for primary sources; scholar gets keyword phrases, not questions.
