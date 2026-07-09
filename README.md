# claude-research-cascade

`/deep` — a **meta-research trigger** for tool-using LLM agents. It doesn't run a fixed pipeline; it wakes the host agent (Claude Code, Codex, …) as the **Organizer** of a single-execution, stateful, bounded research harness over a portfolio of workers — from a $0.01 fact-check to a cross-validated multi-engine investigation.

Not another Deep Research. A harness that treats Deep Research APIs, search APIs, academic APIs, and cheap models as **orchestratable components**, and optimizes information gain per dollar across the whole portfolio.

## Architecture

| Piece | Role |
|---|---|
| [HARNESS.md](HARNESS.md) | **host-neutral spec**: workers manifest（tools characterized by cost／latency／index family／failure modes）, Research State schema, the loop, hooks, depth presets, verification floor |
| [SKILL.md](SKILL.md) | Claude Code binding — registers `/deep`, maps harness primitives to Claude Code tools |
| [AGENTS.md](AGENTS.md) | Codex binding — same harness, Codex-native conventions |
| [scripts/deep_research.py](scripts/deep_research.py) | the workers CLI — deterministic, single-call, resumable; JSON out |

```mermaid
flowchart TD
    A["/deep &lt;question&gt;"] --> B["Organizer: framing + research contract<br/>(depth × independence × strictness;<br/>≤3 clarifying Qs when needed)"]
    B --> S["Research State (on disk)<br/>evidence pool · spend ledger · open disputes"]
    S --> L{"loop: inspect state →<br/>choose highest info-gain/$ batch"}
    L -- "shared branch" --> W["workers: cascade / scholar /<br/>perplexity / openai / gemini / deepseek"]
    L -- "isolated branch (blind verify)" --> W
    L -- "targeted lookup" --> P["sonar / host search (~$0.01)"]
    W --> N["hooks: normalize claims →<br/>reconcile: corroborated / disputed"]
    P --> N
    N --> S
    N --> T{"settled at contract bar<br/>(independence + strictness)<br/>or diminishing returns?"}
    T -- no --> L
    T -- yes --> V["verification floor:<br/>spot-check load-bearing claims"]
    V --> D["verdict in user's language<br/>+ spend vs band + state file"]
```

## Why this shape

1. **A contract, not a plan** — the user sets three axes（depth × independence bar × strictness, or one preset pick）; the Organizer decides each next dollar from the live evidence state. The most expensive failure of deep research — a $4 run aimed at a badly-specified question — is prevented by cheap heterogeneous probing（`cascade`）before any expensive call. Dollar figures are indicative at list prices, never enforced in code.
2. **Role separation** — engines do what they're good at: search engines research, Semantic Scholar grounds claims in papers, DeepSeek（no retrieval, hallucination-prone ungrounded）only ever processes already-fetched material.
3. **Claim-level state** — evidence lives in an on-disk pool with provenance and independence tags; conflicts become `disputed` items and **only unresolved disagreements get more spend**. The spend ledger makes every dollar auditable.
4. **A verification floor** — load-bearing claims get an independent spot-check before delivery. Research reports are hypotheses, not facts.
5. **Host-agnostic** — one spec, thin bindings. Anything that can run a shell and read markdown can be the Organizer.

## Workers

| Worker (`--provider`) | Engine / role | Typical cost | Typical time |
|---|---|---|---|
| `cascade` | scout: 4 parallel sonar-pro probes (direct/counter/landscape/falsifier), merged | ~$0.10–0.15 | ~30 s |
| `sonar` | quick single grounded answer | ~$0.01 | seconds |
| `scholar` | Semantic Scholar Graph API (literature) | free | seconds |
| `perplexity` | sonar-deep-research | $0.5–1 | 2–5 min |
| `openai` | o3 / o4-mini-deep-research | $0.4–8 | 5–25 min |
| `gemini` | Deep Research | varies | 3–10 min |
| `deepseek` | processor over `--files` (merge/extract, no retrieval) | ~free | 1–5 min |

(Worker names match the [HARNESS.md](HARNESS.md) manifest exactly; the depth axis is `shallow/medium/deep`, a separate concept from any worker.)

## Install

The harness is host-neutral, but each host discovers it differently:

**Claude Code** — clone into the skill directory; `/deep` registers automatically:
```bash
git clone https://github.com/jechiu16/claude-research-cascade ~/.claude/skills/deep
```

**Codex** — clone anywhere, then make it discoverable. Codex reads `AGENTS.md` from the working directory upward, *not* `~/.claude/skills/`, so the checkout alone is invisible:
```bash
git clone https://github.com/jechiu16/claude-research-cascade ~/tools/research-cascade
export DEEP_HARNESS_DIR=~/tools/research-cascade   # workers: python "$DEEP_HARNESS_DIR/scripts/deep_research.py" ...
# add a one-line AGENTS.md stub in your project root pointing at $DEEP_HARNESS_DIR/HARNESS.md
# (see AGENTS.md "Discovery and install" for the exact wording)
```

**Any other host** — clone anywhere; the Organizer reads `HARNESS.md` and invokes workers by absolute path. That is the entire contract.

Then, for every host — install worker deps and keys:
```bash
pip install requests python-dotenv          # + google-genai for the gemini provider
cp .env.example .env                        # fill in the keys you'll use (scholar works keyless too)
```

Key resolution order: process env -> nearest `.env` from your working directory upward -> `.env` beside the scripts. Project-local keys win; a checkout-local `.env` makes workers runnable from any directory.

## Workers CLI

```bash
# pick the python that has the deps: project venv first, else system
PY=.venv/Scripts/python.exe   # Windows; POSIX: PY=.venv/bin/python; no venv: PY=python3

"$PY" scripts/deep_research.py --provider sonar                "quick question"
"$PY" scripts/deep_research.py --provider cascade              "scout: 4 probe framings in one call"
"$PY" scripts/deep_research.py --provider scholar              "dynamic factor model nowcasting"
"$PY" scripts/deep_research.py                                 "standard research question"    # perplexity medium
"$PY" scripts/deep_research.py --provider openai --effort high "decision-critical question"    # o3
"$PY" scripts/deep_research.py --provider deepseek --files a.md --files b.md "merge into a claims table"
"$PY" scripts/deep_research.py --resume "openai:resp_abc123"   # recover a dropped job — don't re-pay
```

Output: one JSON object on stdout（`report`, `report_path`, `usage`, `cost_estimate_usd`, `wall_time_s`）; progress + resume token on stderr; report saved to `<cwd>/reports/deep_<timestamp>_<slug>.md` with usage, official/estimated cost, and a Sources section.

## Field notes（measured, not vibes）

- Perplexity `reasoning_effort=minimal` is **ungrounded**: bills searches, returns zero citations, writes from parametric memory. Use `medium`+ for real research.
- Perplexity returns an official `usage.cost.total_cost` — reported verbatim. OpenAI returns no cost field; the engine estimates from tokens + search-call count.
- Perplexity usage fields can be `key: null` — the engine is None-safe throughout.
- Perplexity deep research: ~5 RPM on low tiers. Semantic Scholar: 1 request/sec with a key（engine retries a 429 once; never call scholar in parallel）; keyless falls back to the shared pool.
- OpenAI deep-research models require a **verified organization**（one-time, platform.openai.com → settings → Verify Organization）.
- Gemini's Interactions API had a breaking change in May 2026; the engine targets the new `steps` schema（needs `google-genai ≥ 2.0`）. Gemini writes sources as markdown links inside the report body.
- DeepSeek thinking models reject `temperature`／`top_p` — the engine never sends them.
- Report filenames embed `hash(query + pid)` — parallel probes and pure-CJK queries can't overwrite each other.
- Failed polls exit with `{"error": …, "resume": "provider:id"}` — an Organizer should resume, never re-pay.

## License

MIT
