---
name: deep
description: Universal /deep research orchestrator — composes multi-step research workflows (scout, scholar, deep research, processing, verification) across Perplexity, OpenAI, Gemini, DeepSeek, and Semantic Scholar, from a $0.01 fact-check to a cross-validated multi-engine investigation. Use when the user types /deep, or asks for deep research, a cited report, a literature review, or a cross-checked investigation of any topic.
---

# /deep — Research Orchestrator

You are the orchestrator; the engine script is a dumb single-call tool. For every request you compose a **research plan** from building blocks, get it approved, execute it in the background, verify, and synthesize. **Always respond in the user's language; always write engine queries in English** (all engines research deeper in English corpora).

## Layout

- Engine: `~/.claude/skills/deep/scripts/deep_research.py` — deps `requests` + `python-dotenv` (`google-genai` only for gemini)
- Python: prefer the project venv if present (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on POSIX), else `python3` / `python`
- Keys, first hit wins: process env → nearest `.env` from cwd upward → `~/.claude/skills/deep/.env`. Missing key → name the variable and both file locations.
- Reports land in `<cwd>/reports/deep_<timestamp>_<slug>.md`; stdout is one JSON object (`report`, `report_path`, `usage`, `cost_estimate_usd`, `wall_time_s`).

## Building blocks

| Block | Invocation core | Cost / time | Role |
|---|---|---|---|
| **scout** | `--provider cascade` | ~$0.10–0.15 / ~30s | one call fires 4 parallel probes (direct／counter／landscape／falsifier) and returns them merged — maps the terrain, aims expensive engines |
| **quick** | `--provider sonar` | ~$0.01 / seconds | single grounded answer when one probe is enough |
| **scholar** | `--provider scholar --effort medium` | free / seconds | academic literature list (Semantic Scholar). Query = keyword phrase, NOT a question. 1 req/sec — never parallel |
| **standard** | `--provider perplexity --effort medium` | $0.5–1 / 2–5 min | workhorse deep research |
| **deep** | `--provider openai --effort high` (o3) or `--effort medium` (o4-mini), or `--provider perplexity --effort high` | $0.4–8 / 5–25 min | decision-critical research |
| **processor** | `--provider deepseek --files r1.md --files r2.md "instruction"` | ~free / 1–5 min | merge reports, claims tables, comparisons, rewrites — **never as a researcher** (no search; hallucinates ungrounded) |
| **gemini** | `--provider gemini` | varies / 3–5 min | 第二個引擎家族的交叉來源（Interactions API；2026-07 已對新 steps schema 更新）|
| **verify** | your own WebSearch | free | spot-check load-bearing claims |

Effort knob: perplexity `minimal` is **ungrounded** (bills searches, zero citations) — never use it for real research. openai `high`→o3; below that o4-mini with tool caps (minimal 10 / low 20 / medium 40).

## Step 1 — Triage

Underspecified question (missing goal, region, timeframe, budget where they change the answer) → ask ≤3 clarifying questions first. Skip when the hint says "go"/"快" or the question is precise.

## Step 2 — Research plan（the core step）

Compose from blocks by: stakes, decomposability, subject language, user budget. Show:

```
── 研究計畫 ──
| # | 步驟 | 引擎 | 估價 | 產出 |
|---|------|------|------|------|
| 1 | ...  | ...  | $... | ...  |
總價 ~$X.XX ・ 預計 N 分鐘

── 預計送出的 query ──
1. "..."
```

**Approval — structured choices by default.** After showing the plan, call AskUserQuestion (one question: 「這份計畫怎麼跑？」) with three options, each description carrying its concrete delta:

1. 照計畫跑（Recommended）— 總價 $X・N 分鐘
2. 精簡版 — 砍到 $Y；description 寫明砍了哪步、犧牲什麼
3. 強化版 — 加到 $Z；description 寫明多買到什麼（交叉驗證／升引擎）

The built-in "Other" free-text covers 換引擎／「預算 N 美元」／改 query — treat it as an adjustment instruction, re-plan, ask again. On 精簡／強化: apply the preset delta, state the new total in one line, launch — no second question.

**Skip asking** when: the plan is a single `sonar` quick step (≲$0.05) or a lone `cascade` scout step (~$0.12) → just run it — confirmation would cost more attention than the money; or the user said 快/go AND the total is ≤$1.5 → launch the recommended plan directly. 快/go never bypasses approval above $1.5 — it skips clarifying questions, not spend approval.

Planning rules:
- **Simple question → 1-step plan.** Zero added ceremony; don't pad plans to look thorough.
- Decompose into **2–4 sub-questions max**, each with its own engine run; perplexity ~5 RPM — batch beyond 4.
- **Scout when** terms are ambiguous, the field is unfamiliar, or before any step ≥$3. One `cascade` call does the whole probe fan-out (4 framings, merged in the result) — you read the merged report and judge. ~$0.12 here re-aims every downstream dollar; if the probes fully answer the question, stop and deliver — don't spend the rest of the plan.
- **scholar** when methodology / science / economics claims need paper backing.
- **processor** whenever ≥2 reports must merge into one artifact.
- **Reuse before re-buying**: check `<cwd>/reports/` for recent `deep_*.md` on overlapping topics; offer to build on them with the processor (~free) instead of repeating paid research. Flag staleness (report date vs the question's time-sensitivity).
- **Budget syntax**: "/deep 預算N美元" or "budget $N" → the plan must fit N; say what was cut to fit.

## Step 3 — Execute（always background）

```bash
# run_in_background: true
"$PY" ~/.claude/skills/deep/scripts/deep_research.py --provider perplexity --effort medium "QUERY"
```

- **Execution graph**: wave 1 = `cascade` ∥ `scholar`（互不依賴，同時發）；wave 2 = main research（等 cascade 落地、用它改寫 query 後才發，多子題彼此並行）；wave 3 = `processor`（等它要合併的報告齊）；verify 的多條 spot-check 在同一則訊息並行發。不確定依賴時寧可等——省下的秒數不值一發瞄歪的 $1。
- After each step lands, extract what changes the next step (scout findings refine the main queries — update them before launching).
- **Answer-first delivery**: when the plan starts with scout, give the user the provisional read（標明「初判」）as soon as probes land while deep steps run — their reaction is live steering input for the remaining spend.
- The script prints a **resume token** (`provider:id`) to stderr right after submitting; on poll failure the error JSON carries a `resume` field. Poll died or timed out → `--resume "openai:resp_..."`; never re-pay for a lost job.
- **Step failure policy**: a failed step never re-runs paid work without approval. Preserve completed report paths, deliver partial synthesis if useful, and offer: retry/resume the failed step (token if any), continue without it, or stop.
- Tell the user what's running and the expected time; keep conversing.

## Step 4 — Verify（mandatory for standard and above）

Pick the 2–3 most load-bearing claims (headline numbers, dates, "X announced Y") and spot-check with WebSearch. Discrepancies get flagged prominently — never silently trust a report. Multi-engine plans: build a convergence/divergence table first (processor can draft it); divergent claims are what you spot-check — adjudicate each disputed claim with a targeted $0.01 probe, not another broad report.

## Step 5 — Deliver（user's language）

```
── 關鍵發現 ──
• 3–6 bullets, each traceable to a report
（報告：reports/... ｜ 實際總花費 $X.XX（計畫 $Y.YY）｜ N sources ｜ 抽查 K 條：結果）

── 我的整合 ──
What this means for the user's actual question; your recommendation.
```

## Query-writing standards

- English; one core question per engine run
- Explicit exclusions: `"focus on X; ignore Y"`
- Context clause: `"in the context of [scale/domain/constraints]"`
- Output structure: `"Structure findings as: ..."`
- Evidence: `"cite primary sources where possible"`
- scholar queries = keyword phrases（`"dynamic factor model nowcasting"`, not a full question）

## Troubleshooting

- **Missing key** → name the env var (`PERPLEXITY_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` / `DEEPSEEK_API_KEY`); keys live in the project `.env` or `~/.claude/skills/deep/.env`. `S2_API_KEY` is optional — keyless scholar uses the shared pool (stricter limits).
- **Timeout** → resume token; caps: perplexity 20 min, openai 45 min, gemini 30 min (`--timeout-min` overrides)
- **S2 429** → the engine retries once (1 req/sec limit); still failing → wait a few seconds, never parallel scholar calls
- **OpenAI 429 / insufficient_quota or "organization must be verified"** → top up or verify org at platform.openai.com
- **Missing deps** → `pip install requests python-dotenv` (+ `google-genai` for gemini)
