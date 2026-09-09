# SKILL.md／HARNESS.md 整合目標稿（審閱用）

日期：2026-09-08。提案者：FABLE。整合基準：第一輪 MVP＋研究行為核心 v2＋ASTRA 的整合前修正。
狀態：概念定稿。2026-09-08 依 ASTRA 審閱完成三處編輯後定稿：授權句改為「超出既有授權才再問，已授權操作不逐次重問」；推論可引用已查核前提但綜合判斷仍標為推論，「Evidence is the product」改為「重要主張的依據應可見」；Heavy 段拆成研究策略與現行 gate 描述。**不覆寫現行 SKILL.md／HARNESS.md**，不改程式、協定或測試。
第二節與第三節是兩份檔案的完整目標稿；第四節說明舊段落去向；第五節把尚未生效的差異單獨隔開，目標稿不能被當成現行可執行協定。

定位：這是幫助 host 判斷下一步的研究 skill，下面有可靠的保存與查核工具；不是讓 host 跑完保存與查核程序、順便研究。整合稿分清四件事但不新增欄位：研究方法（依發現選擇擴展、深入、反查或重構問題）、交付承諾（posture 說明本輪交回什麼）、查核責任（跟著具體主張的用途與風險走）、資源與授權（預算是上限，目的、支出與外送不能自行擴張）。

不宣稱的事：第一輪示例只證明暫定內容可以保存與交付，不證明探索品質；因範圍不追不等於證偽；另一個 host 能找到寫好的下一步，不等於已能有效延續研究。目標稿進入現行指引之前，也不能據此宣稱探索品質或跨 host 接手效率已改善。

審閱標準只有一個：host 順著這份指引工作時，是否更容易選到值得做的下一步，同時清楚知道哪些內容可信、哪些承諾尚未完成、哪些行動尚未獲授權。

## 一、SKILL.md 目標稿

````markdown
---
name: deep
description: Portable /deep research trigger for Claude Code and OpenAI Codex. Use only when the user explicitly types /deep to start one bounded, host-led research session.
---

<!-- PURE_TRIGGER_CARD_START -->
問題：{正規化後的問題}
Query Brief：{本輪想弄清楚什麼；必要時補充已知與不確定處}
建議：{light/standard/heavy}，因為{一個理由}
Light：deep {a}｜search {b}｜free unlimited
Standard：deep {a}｜search {b}｜free unlimited
Heavy：deep {a}｜search {b}｜free unlimited
D1：{最低成本 ready provider；候選與資料外送範圍}
共通：背景執行；host 複驗並寫結論；交付 JSON + 繁體中文 HTML；超限即停並標註缺口
開始：light｜standard｜heavy｜調整｜取消
<!-- PURE_TRIGGER_CARD_END -->

# /deep

`SKILL.md` is the sole public protocol shared by Claude Code and Codex. On
explicit `/deep`, normalize the question from conversation context, run only
the local `deep-research-state card` command, and show exactly one completed
card with no prose around it. Without a question, recommend `調整` and stop.
The posture on the card -- `decision` by default, `explore` when the user
wants directions rather than a verdict -- says what this run hands back, not
how you think along the way.

## How To Research

One run holds three kinds of statement at once: facts you have checked,
directions worth pursuing, and guesses you have not tested. Keep them apart
in what you write; never force the whole run to become one of them.

Start where you are. The brief says what this round is meant to find out;
add what is known or uncertain only where it helps. If the question is not
yet located, say so and make locating it the purpose. Recommend a profile by
the scope and checks you expect, not by how little you know.

Choose each step by what could change your mind: which one thing, if known,
would most move your understanding or your next move? Learn it in a way that
is sufficient to answer and proportionate in cost -- read the project, fetch
the source of record, compare a case, seek a counterexample, ask the user,
or commission a provider report. A report can save time, buy an independent
angle, or reach explanations you cannot; it is a means you choose, not a
stage you pass, and unspent budget is not unfinished work.

Breadth is contact with different explanations, not more items. Change angle
or re-cut the sub-question when options share a doubtful premise, sources
keep repeating one view, or a finding unsettles the question as asked. If
the original direction survives that contact, keep it; do not manufacture
alternatives, objections, or a fixed number of branches.

Depth goes where it materially improves this round's understanding,
separates the explanations that matter, or changes the unknown behind the
next step. Understanding a mechanism or locating a problem's scope counts as
much as reaching a recommendation; leave detail that serves none of these.

Checking follows use. A guess may stand unchecked while it is only a guess.
Once a statement supports a recommendation, rules an option out, or shapes
an action, it must hold at that weight: a fact is a claim traced to a
captured source; an inference carries weight only when its premises,
reasoning, and uncertainty are stated and hold up -- calling it "inference"
does not excuse it from checking. The riskier the use, the higher the bar.
Where the difference matters to understanding, a recommendation, or whoever
picks this up next, say which a statement is: found, inferred, or guessed;
set aside, or shown false; a next check worth doing, or a reversible step
safe to take now -- neither of which means the whole answer is established.
Do not label every sentence.

Changing path is not changing authority. Inside the confirmed question,
count vector, provider set, and egress scope, re-cut sub-questions and
methods freely; note a major turn in one line. Ask the user again only for a
purpose, spend, data egress, or change to their system that goes beyond
what was confirmed; operations the confirmation already covers are not
re-asked one by one. A research conclusion adds no permission to act on it.

Continue while this round's purpose is unmet and there is still a next step
that is authorized, proportionate in cost, and expected to bring real
progress -- better understanding, separated explanations, a located
problem, or a changed judgment. If the user asked for an answer and such a
step exists, take it rather than handing it back. Otherwise deliver what is
understood and where its limits are. One check not worth making does not
end the research; the absence of any worthwhile one does. Do not pad a
report to look complete.

## Boundaries

Before confirmation, nothing that costs, sends data out, or changes
anything: do not search, inspect the project, call a provider, start a
worker, run project code or tests, or go through logs, credentials, or
sensitive files. Local profile/registry reads for the card are allowed and
make no external request. [Target wording, not in force until the protocol
changes -- see the "not yet in force" note in the integration document:
within the project the user named, read the README, the layout, and
directly relevant files only as far as it takes to write the brief and
estimate scope; if the conversation already gives you that, do not read.]
The reply `light`, `standard`, or `heavy` confirms that printed count vector
and disclosed provider/egress set for one run; `調整` and `取消` spend
nothing. Re-card only when the vector, provider set, or egress scope
changes.

After confirmation, read [HARNESS.md](HARNESS.md), create the canonical
package, and run in the background. The host is the sole conclusion author.
Provider reports, including D1/D2, buy breadth and structure only; they
cannot support a canonical claim -- the host's targeted re-verification is
what makes a claim corroborated. Stop external calls at the confirmed count
limit, finish from existing materials, and name the unresolved gap; no hard
gate, no automatic provider bundle.

## Delivery

Always deliver canonical `state.json`, `events.jsonl`, `raw/`, and a
hash-bound `report.html`, host-authored or, failing that, deterministically
rendered. Human-facing fields and HTML are Traditional Chinese; exact
excerpts, titles, URLs, IDs, hashes, and diagnostics stay unchanged. Lead
with the progress of understanding -- what is now known, where to go next,
what could still change the judgment -- and, for a verdict run, what to do.
Fix disproved claims, mark unverifiable claims, and never withhold delivery
for uncertainty.

Keep three things apart. Integrity: the package is intact and unaltered --
the only thing the validator can prove. Correctness: a captured source can
still be wrong and an inference can still be unsound; that judgment is
yours, stated with what would overturn it. Adoptability: a reversible step
can be safe before the whole answer is established, and an established
answer is still not permission to act. A `BLOCKED` package is still
delivered: it names an unmet delivery requirement or an evidence gap, not a
failed research and not a broken package.
````

## 二、HARNESS.md 目標稿

````markdown
# /deep Organizer Harness

Internal runtime bridge for the public flow in [SKILL.md](SKILL.md). Read it
only after the user selects `light`, `standard`, or `heavy`. SKILL.md says
how to research; this file says how to use the runtime to record what you
find, check what carries weight, and deliver. It does not prescribe the
order of your thinking.

## Product Contract

- The selected host is the Organizer and sole conclusion author.
- D1/D2 are untrusted discovery memos, never evidence or verdicts.
- Re-verification corrects or annotates; it never suppresses delivery.
- Counts, not token-price guesses, stop external calls. Budget is a
  ceiling, not a plan of work.
- The posture says what the run hands back. In every posture the state
  holds checked facts, directions, and guesses side by side, each in its own
  section.
- Deliver one machine truth (`state.json`) and one human projection
  (`report.html`), plus their journal and raw evidence.

An epistemically `BLOCKED` package is still delivered. Integrity failure
means the package cannot be trusted as a record; it says nothing about
whether the research was good, and an intact package says nothing about
whether its sources are right or its inferences sound. Evidence gaps render
as `證據不足 / EVIDENCE_INSUFFICIENT`; incomplete handoff fields render as
`交付不完整 / DELIVERY_INCOMPLETE`.

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

After confirmation, bind and start one contract (`--posture explore` uses the
same commands):

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
`final_inference_review/organizer_pass/host` mapping. An `explore` contract
drafts with `minimum_load_bearing_claims: 0`; every other posture keeps a
positive floor.

## Provider Routing

`provider_registry.json` is the only tool registry. Each route declares
`cost_class: deep|search|free`; deep routes also declare `cost_rank`. New tools
enter a class, never a profile.

A present credential is not execution readiness. The adapter, storage policy,
request boundary, and required environment must all pass local preflight.

1. Anything that will become a claim needs a direct source-of-record or
   local route; a provider payload cannot support it.
2. A provider report is a means you choose -- to save time, to buy an
   independent angle, or to reach explanations you cannot -- not a stage
   the profile bought. For D1, choose the lowest-rank ready provider unless
   source fit or privacy justifies another card-disclosed candidate.
3. Use D2 only for a material challenge, new angle, or expansion selected by
   the host after seeing D1 and current evidence.
4. Never call a bundle merely because budget remains.

The request boundary reserves before sending. Failed or uncertain calls remain
consumed. Transport polls are physically bounded but are not another `deep`
submit.

One narrow exception: an unambiguous, unbilled provider gateway rejection
(invalid credentials, exhausted quota, malformed request -- rejected before
any work started) returns the paid `deep`/`search` permit, so `cost_usage`
does not increment for that call. The action id is still permanently burned
either way -- a rejected call is never retried or resubmitted. Do not expect
`cost_usage` to increment 1:1 with every attempted paid call; check
`rejected_unbilled` actions when reconciling spend against attempts.

## Recording What You Find

The state has a place for each kind of statement. Record as you go. The
minimum is small; the rest is added when it exists, or when whoever picks
this up next would need it.

- **Where you start.** `framing.assumptions` and `framing.exclusions`. When
  you re-cut the sub-question, add one line there (本輪把問題改讀為…). The
  contract question itself is fixed; concluding that it was the wrong
  question is a finding to deliver, not a reason to swap it.
- **A guess or a direction.** `hypotheses`: a stable `id` and readable
  `text` are enough. Add `basis`, `next_check`, `source_ids`, `artifact_ids`
  when they exist, and `excluded_reason` when a direction is ruled out --
  keep the record, an exclusion is a finding. A hypothesis must not carry
  `status`, `load_bearing`, `supporting_evidence_ids`, or `claim_type`;
  promote it to `claims` with evidence to earn those.

```json
{
  "id": "H1",
  "text": "保留薄 skill，可能比新增獨立 runner 更符合日常專案探索。",
  "basis": "暫定假說；尚未測試跨 host 接手成本。",
  "next_check": "用同一份研究資料測試另一個 host 能否找到下一步。"
}
```

- **Set aside for now.** `open_questions`. Say it was not pursued and why
  (scope, cost, authorization); that is not the same as shown false.
- **A next check worth doing.** `planned_checks`, optionally with
  `hypothesis_ids`.
- **An inference you rely on.** `observations`, with its premises (which may
  cite checked claims by id) and its uncertainty in `basis`. Two checked
  premises do not make the conclusion drawn from them a checked fact; it
  stays an inference unless checked itself. It never satisfies an evidence
  floor and is rendered as "not evidence".
- **A checked fact.** `claims` with the chain
  `claim -> evidence -> source + source_origin -> raw artifact`. Capture the
  bytes (`host-capture`, `artifact-add`); provider payloads cannot support a
  claim. Correct claims disproved by direct evidence; mark unresolved claims
  and their revisit trigger; do not convert model agreement into
  corroboration. This chain applies to any claim presented as verified, in
  every posture -- it is not optional in an exploration.
- **What a provider report gave you.** Feed its useful hypotheses,
  contradictions, and citations into `hypotheses` and `planned_checks`;
  `"$CLI" citations` lists what is still unverified. Nothing from a report
  enters `claims` until you have captured the source yourself.

When the route changes, leave a one-line reason in `basis`,
`framing.assumptions`, or `open_questions` -- only then:

| Current finding | Reasonable next move |
|---|---|
| Sources keep repeating the same view | Change source type or angle, or stop that branch |
| Several routes hold and nothing separates them | Find the check, counterexample, or small experiment that would |
| The original premise fails, or a lead could change direction | Re-cut the sub-question and open the new direction; keep what still holds |
| Remaining detail does not affect this run's goal | Mark the gap and deliver |

No branch count, document count, or scan/deepen ratio is required.

## Checking What Carries Weight

A statement is checked in proportion to its use, not to the package status.
A guess needs nothing. A direction that shapes the next step needs its
`basis`. An inference that supports a recommendation needs its premises and
uncertainty stated, and a flip condition. A claim that supports a
recommendation, rules an option out, or shapes an action needs the full
chain above and targeted re-verification. Paid search routes consume
`search`; host/local/direct free routes consume `free`.

A verdict run (`PASS`/`PARTIAL`) records its re-verification:

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

`checked_claim_ids` must equal the final `load_bearing_claim_ids`. Today the
runtime requires this record for any host-led verdict even when that set is
empty; write the disposition honestly rather than inventing a check.

**Heavy.** The second deep call is capacity for an independent angle on the
current frame. Commission it when that angle is what the next step needs
(Provider Routing, rule 3), not because the profile bought it; a heavy run
that never needed D2 has spent nothing wrongly.

Current runtime gate, described as it is and not lifted by this document: a
heavy scientific/decision `PASS` requires

- an `anti_lock_in` record, and
- each load-bearing claim's captured evidence spanning at least two distinct
  upstream sources -- capture files that all trace back to one upstream
  (e.g. three claims that each cite only `noaa.gov`, only `navy.mil`, and
  only `nps.gov`, respectively, with nothing cross-checking any one of them)
  does not satisfy this.

The gate does not check whether D2 was actually used. If you judged it not
worth spending, the record's disposition says so; do not contrive a call to
satisfy the record.

```json
{
  "id": "AL1",
  "kind": "anti_lock_in",
  "completed": true,
  "disposition": "D2（gemini-deep）提出獨立角度並經 host 覆核，未推翻既有結論；未採用其未驗證延伸。"
}
```

A **decision**-posture package -- at any profile -- additionally requires a
`coverage_audit` record. This is the fix for the single most common silent
failure mode: a package that validates cleanly while quietly answering only
half the asked question. State plainly which parts of the question this
package addresses and which it does not; an omission is not a defect as long
as it is disclosed here (and, for the parts not addressed, usually also in
`open_questions`).

```json
{
  "id": "CA1",
  "kind": "coverage_audit",
  "completed": true,
  "candidate_omissions_dispositioned": true,
  "addressed": ["問題中已有直接證據佐證的部分，逐項列出"],
  "not_addressed": ["問題中本次未觸及或無法逐位元組佐證的部分，逐項列出"],
  "disposition": "本次僅完成問題的 X 部分；Y 部分未觸及，已記錄為待辦缺口而非結論的一部分。"
}
```

What does not depend on posture: the claim chain, raw-artifact integrity,
quota, and confirmation binding. What does: the handoff for a verdict --
`summary.decision`, the re-verification record, the coverage audit, a
reversible safe action, and acceptance tests in `檢查方式 => 預期結果`
form. An `explore` run owes none of those; it owes at least one hypothesis
or open question with text, a one-line `human_status`, and a
`human_recommendation` that names the next step or the reason to stop.

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

### What a status says today

- `PASS`: a bounded judgment whose load-bearing claims cleared the chain and
  whose handoff is complete.
- `PARTIAL`: the judgment stands with a named gap, and a reversible action
  does not depend on that gap.
- `EXPLORED` (explore posture only): understanding delivered, no judgment;
  leads are tentative; any claim it presents as verified was still checked.
- `BLOCKED`: delivered, with `human_status` saying which shortfall --
  `交付不完整` (a delivery requirement unmet) or `證據不足` (the evidence does
  not carry the claims). `finalize` seals every sound-but-undeliverable
  package this way. It is not "the research failed".
- `/ INVALID` on the report: validation found an `ERROR` of any kind, or the
  embedded hash no longer matches the state. After `finalize` the errors that
  remain are usually integrity ones (hash, journal, raw bytes, excerpt), but
  the label is not integrity-only by definition; read the issue list.

A status is a claim about the package's delivery shape. It is not a claim
that the sources are right, that an inference is sound, or that anything in
the handoff may be executed without the user.

### Delivering understanding without the verdict (target semantics)

A run confirmed for a verdict may end without one. That is a legitimate
outcome only when all of the following hold, and the report says each in
plain words:

- The verdict the user asked for is explicitly not given, with the reason:
  the premise failed, the decisive check needs authorization or information
  this run lacks, or the evidence does not yet separate the options.
- Every statement already used to recommend, to rule an option out, or to
  shape an action still meets the bar for that use. Withholding the verdict
  lowers nothing; it removes only the verdict.
- The package is intact. An integrity failure is never presented as an
  exploration result.
- The findings are offered as progress, never as completion of the original
  commission, and what would complete it is named.

How the runtime records this outcome is undecided. Today such a run is
sealed `BLOCKED / 交付不完整` and the deterministic report tells the reader
to complete the handoff; write the reason into `summary.human_recommendation`
and `open_questions` so the honest reading survives that label.

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

- Lead with what changed in understanding. The reader already knows the
  question; put it in small supporting text, not the headline. For a verdict
  run the headline is what to do or what is true; for an exploration it is
  where to go next -- use `summary.headline` if present, else
  `summary.human_recommendation`.
- Display type is for one line. `summary.decision` is body copy, not a
  headline-sized wall of text.
- Keep three different lists visually and structurally separate:
  `engineering_handoff.constraints` (what this run did not do), each claim's
  `would_change_if` (what would overturn it), and `open_questions` (what is
  still unresolved). Merging them into one flat undifferentiated list is the
  single worst defect this instruction replaces -- do not reintroduce it.
- Do not break Chinese sentence flow with inlined English source titles; use
  numbered references with a source list instead.
- The basis of every statement that carries weight must be visible in the
  default view: load-bearing claims with their status and evidence chain,
  inferences with their premises, leads marked as tentative. Collapse only
  genuine machinery -- quota tables, hashes, validation internals.
- Omit a section entirely rather than rendering an empty placeholder like
  「尚未記錄」.
- `claims` are byte-backed and evidenced; `observations` are not, and must
  never be rendered so a reader could mistake one for the other. Some
  questions cannot be reduced to a claim no matter how much budget a run
  buys -- future events, subjective experience, or a cross-source synthesis
  such as driving time vs. walking distance, physical load, or meal rhythm.
  Put that judgement in `observations` instead of stretching a claim's
  evidence past what it supports; give it its own visually distinct block
  (a different heading, styling, and an explicit "not evidence" label -- see
  `research_harness/rendering.py::_render_observations` for the deterministic
  fallback's treatment), and never let it satisfy an evidence floor,
  load-bearing requirement, or diversity check. An observation needs no
  `supporting_evidence_ids` or `source_origin_ids`. Its premises may cite
  checked claims by id in `basis`; the synthesis drawn from them stays an
  observation, labelled as inference, unless that judgment itself has been
  checked to the same standard -- only then does it belong in `claims`.
- Leads render as tentative (`暫定假說`) and exclusions keep their reason;
  the unknowns block is always present; a lead is never shown with a claim
  status, a load-bearing marker, or an evidence link. In an exploration, no
  bounded decision, load-bearing reasons, safe action, or acceptance test is
  shown or reported missing; checked facts it does contain are shown as
  claims, apart from the leads. The deterministic fallback implements the
  lead rules in `rendering.py::_render_explore_first_screen`; today it does
  not surface checked facts on the first screen, so a host-authored
  exploration report should.

Three field-shape notes:

- `summary.human_status` is a short one-line note on what this run actually
  did (≤40 全形字) -- not a narrative. The bounded conclusion belongs in
  `summary.decision`, the recommendation in `summary.human_recommendation`.
- `summary.headline` is optional: an action phrase, ≤20 全形字, used as the
  report's headline and `h1`. Omit it and both tracks fall back to
  `summary.human_recommendation`; existing packages that predate this field
  keep validating unchanged.
- `observations` entries are free-form but conventionally carry `id`, `text`,
  and an optional `basis` describing what was synthesized across (e.g. "跨來源綜合判斷（氣候常年值 + 日照時數 + 路網結構），非單一可查核來源").
  Never give one a `load_bearing`, `supporting_evidence_ids`, or `status`
  field -- those are `claims` vocabulary, and no validator ever reads them
  off an observation, so borrowing that shape only invites confusing the two.

Only packages recorded under `pure_trigger_v5` know the explore posture and
the `EXPLORED` status; older packages keep their recorded verdict
vocabulary. `examples/explore/` holds an offline, demonstration-only package:
it shows that tentative content can be saved and delivered, not that the
exploration it contains was good.

## Recovery

```bash
"$CLI" status "$SESSION" --json
"$CLI" deep-pending "$SESSION" --json
"$CLI" recover "$SESSION" --json
"$CLI" render "$SESSION" --json
```

No token means a deep attempt is consumed and not pollable. A recorded token
may be polled with a new poll action ID; never resubmit the same deep action.
````

## 三、整合說明：舊段落去向

### SKILL.md

| 現行段落 | 去向 | 說明 |
|---|---|---|
| 九行卡片 | 保留；第二行改為已決定的 brief 措辭 | 其餘八行不動。 |
| `# /deep` 觸發段 | 保留；第一輪加的 `--posture explore` 括號句改寫為「posture 說明交回什麼」一句 | 消除「explore 是特例」的語氣。 |
| Before Confirmation | 併入 Boundaries 前段；釘死句照留；定向讀取以方括號標為目標措辭 | 邊界不變，只把「理解」與「成本／外送／操作」分開說。 |
| After Confirmation 第一段 | 併入 Boundaries 後段 | 唯一結論作者、provider 只買廣度，原句保留。 |
| After Confirmation 第二段 | D1 選法移到 HARNESS Provider Routing 第 2 條；「targeted re-verification 才讓主張 corroborated」留在 Boundaries；Fix disproved／mark unverifiable／never withhold 移到 Delivery | 消除「D1 是固定第二步」的語氣；查核責任改由 HARNESS「Checking What Carries Weight」承接。 |
| After Confirmation 第三段 | 「Stop external calls…name the unresolved gap…no hard gate…no automatic provider bundle」留在 Boundaries；Heavy 第二次 deep 的條件留在 HARNESS Provider Routing 第 3 條 | 「何時停」改由核心第八段用統一原則說。 |
| Delivery | 改寫開頭為理解的進展；新增完整性／正確性／可採用性三分；BLOCKED 不是失敗 | 交付物與繁中規則不變。 |

### HARNESS.md

| 現行段落 | 去向 | 說明 |
|---|---|---|
| 開頭與 Product Contract | 保留；加「預算是上限」「posture 說明交回什麼、三種陳述並存」；刪「Only integrity failure means the report is unsafe to act on」，改寫為完整性與正確性分開 | 對應整合前修正 1。 |
| Runtime Bridge、Contract Shape | 保留；Contract Shape 加一句 explore 的 floor 為 0 | 純 runtime。 |
| Provider Routing | 保留四條；第 1 條改為「會成為 claim 的內容需要直接來源」，第 2 條收進 D1 選法並寫明報告是手段 | 對應核心第三段。 |
| Research Loop 七步 | 消除：第 1 步改為「Where you start」；第 2 步改為 Provider Routing 第 2 條與「What a provider report gave you」；第 3～5 步成為「A checked fact」與「Checking What Carries Weight」開頭；第 6 步的 VR 紀錄與第 7 步的交接移到「Checking What Carries Weight」末段 | 不再把所有研究寫成固定決策流程；查核鏈明寫「任何 posture 都適用」。 |
| Research Loop 的 heavy／decision 段與三份 JSON | 保留於「Checking What Carries Weight」；Heavy 段拆成研究策略（按價值選用 D2）與現行 gate 描述（不寫成應採取的步驟、不暗示 gate 已解除）；空集合仍需 VR 紀錄以現況句註明 | 落差如實註明，不靠文案宣稱已解。 |
| Exploration Runs（第一輪） | 拆散：hypothesis 形狀與 JSON、切換表、「不設分支數」併入「Recording What You Find」；explore 的最低交付併入「Checking What Carries Weight」末段；報告規則併入 Report Authoring；v5 與示例說明移到 Report Authoring 末尾並加「不證明探索品質」 | 探索不再是附錄，也不再是主流程的豁免條款。 |
| Execution And Delivery | 保留；新增「What a status says today」與「Delivering understanding without the verdict (target semantics)」，兩者明確分開 | 對應整合前修正 1 與決定 3。 |
| Report Authoring | 「Answer first」改為「Lead with what changed in understanding」；「Evidence is the product」改為「重要主張的依據應可見」；observations 的前提可引用已查核 claim，綜合判斷仍標為推論；三清單分開保留；新增線索渲染規則一條 | 對應方向六與審閱收尾第 2 點。 |
| Recovery | 保留 | 純 runtime。 |

沒有一條安全邊界被刪。被消除的只有兩種語氣：D1 是必經步驟；探索是例外。

## 四、尚未生效的差異（目標稿 ≠ 現行協定）

以下每一項在正式修改前，現行文字與行為仍有效。它們是落差註記，不是實作待辦。

1. **卡片第二行**。現行：「決策、範圍、成功條件各一句」；目標：「本輪想弄清楚什麼；必要時補充已知與不確定處」。`tests/test_docs.py` 釘死九行。
2. **確認前的本機唯讀定向**。現行：禁止 inspect the project，方括號內文字不生效；目標：使用者指定專案內，為寫 brief 與估範圍而定向讀取，不執行程式、不翻 log 與憑證。「inspect the project」為釘死片語。
3. **可交付理解、保留判斷**。現行：decision run 不下結論即封 `BLOCKED / 交付不完整`，備援報告提示補齊交付要件；目標：第二節的四條語意；status 方案未決。
4. **空集合的 targeted_reverification**。現行：任何 host-led verdict 都需要一筆，即使 `checked_claim_ids` 為空；目標稿只要求誠實寫 disposition，未改 gate。
5. **Heavy 的 anti_lock_in**。現行：scientific／decision 的 heavy PASS 一律要求，不看 D2 是否使用；目標稿要求 disposition 說明未用 D2 的理由，未改 gate。
6. **探索報告的已查明局部**。現行：備援渲染的 explore 第一畫面沒有 claims 區塊；目標：host 自撰報告應呈現，備援渲染待補。
7. **SKILL.md 行數**。現行測試釘在 60 行以內；目標稿明顯超過。不以任何數字代替內容取捨，留給實作輪連同測試決定。
8. **提醒**：以上之外，預算、provider、status 與查核之間沒有其他被本稿改寫的實作行為；目標稿凡寫「today」「現行」之處，皆為如實描述，不是已解決的宣稱。
