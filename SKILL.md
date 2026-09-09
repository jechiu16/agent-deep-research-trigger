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
anything: do not search, inspect the project, call a provider, or start a
worker. Local profile/registry reads for the card are allowed and make no
external request. If the question is vague, write locating it as this
round's purpose from the conversation you already have; do not invent
project knowledge to fill the brief. The reply `light`, `standard`, or
`heavy` confirms that printed count vector and disclosed provider/egress set
for one run; `調整` and `取消` spend nothing. Re-card only when the vector,
provider set, or egress scope changes.

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
