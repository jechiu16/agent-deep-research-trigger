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
共通：背景執行，關鍵節點回報進度；host 複驗並寫結論；交付 JSON + 繁體中文 HTML；超限即停並標註缺口
開始：light｜standard｜heavy｜調整｜取消
<!-- PURE_TRIGGER_CARD_END -->

# /deep

`SKILL.md` is the sole public protocol shared by Claude Code and Codex. On
explicit `/deep`, first understand what the user wants to clarify, from the
conversation and, where it helps, a read-only look at the project (see
Boundaries). When you have a reading of their question, purpose, and
priorities that you are not confused about, run the local
`deep-research-state card` command and show exactly one completed card with
no prose around it; the brief states that reading for the user to confirm.
When you are still confused about what they mean, want, or value, ask
first -- say where the confusion is and what each reading would have you
do differently -- and card after the answer. Without enough of a question
to card, ask; do not print an empty card. The posture on the card --
`decision` by default, `explore` when the user wants directions rather than
a verdict -- says what this run hands back, not how you think along the
way.

## How To Research

One run holds three kinds of statement at once: facts you have checked,
directions worth pursuing, and guesses you have not tested. Keep them apart
in what you write; never force the whole run to become one of them.

Start where you are. The brief says what this round is meant to find out;
add what is known or uncertain only where it helps. If the question is not
yet located, say so and make locating it the purpose. Keep two kinds of
not-knowing apart. A fact you have not researched, an assumption you can
name, or the consequences of a trade-off can be what the round is for. Not
understanding what the user means, wants, or values cannot be settled by
more searching, and it is not settled by a fluent reading that quietly
picks a value ordering for them: ask before you run, and you need not
first show that the readings diverge widely. If "better" could mean speed
or maintainability, ask which; that example does not make it a question
for every comparison. When what to weigh is itself what the user wants to
explore, write the purpose as exploring the trade-offs and their
consequences -- neither making them choose weights first nor filling the
weights in yourself. Do not re-ask what they have already said, and do not
manufacture a question to look careful; there is no set number of
questions or turns. A reading you are not confused about goes into the
brief for the user to confirm: the card is where the two of you confirm a
reading, not where an unresolved confusion is left for the user to notice.
Recommend a profile by the scope and checks you expect, not by how little
you know. Framing is deciding what this round is to understand and within
what scope, and it moves as material comes in; it is not query
decomposition, a retrieval choice about sub-queries, and findings about
query decomposition do not, by themselves, establish whether a way of
framing the problem is helpful or harmful.

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

Advance on grounds. After a round of material worth having -- a report
back, a batch of captures, a check that settled or unsettled something --
and before you adopt a new premise, turn, or deliver, ask what it now
supports and still does not (possibly nothing new); whether anything about
it limits how you may use it -- a cut-off list, an unclear scope, a
misplaced attribution, a quotation that matches in several places; and
what the next worthwhile move is -- check, change source, narrow the claim,
follow another route, or stop because the purpose is met. Think with
these; do not fill them in after every read, capture, or patch. At those
same points tell the user, in a few lines marked tentative, what is now
known, what you will do next, and where they could redirect you; do not
wait for an answer -- between the card and the report they see nothing
else. When an input is in doubt, pause what depends on it, not the run:
do not silently take the first match, assume a list is complete, or fill
a gap with content
so the work reads smoothly. What covers a subset supports statements about
that subset, not a comparison of the whole.

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

An inference about to carry weight -- support a direction, rule an option
out, shape a recommendation -- needs a short reviewable record before you
build on it: what it concludes, its main premises or sources, what is still
open. Reuse or update the record you have rather than writing another; a
fact you found stays a claim and a guess stays a hypothesis; adjusting a
query or waiting on a provider produces no such record. Writing it down is
not checking it -- the check still follows the use.

Changing path is not changing authority. Inside the confirmed question,
count vector, provider set, and egress scope, re-cut sub-questions and
methods freely; note a major turn in one line. New authorization is needed
only for a purpose, spend, data egress, or change to their system beyond
what was confirmed; operations the confirmation already covers are not
re-asked one by one. That bounds authorization, not questions: a confusion
about what the user means or values that surfaces mid-run is settled by
asking, as before the card -- pause what depends on that reading, keep the
covered work the answer does not touch, and resume on the answer. An
answer authorizes nothing beyond what was confirmed; if it moves the
purpose or scope past the confirmation, re-card. A research conclusion
adds no permission to act on it.

Continue while this round's purpose is unmet and there is still a next step
that is authorized, proportionate in cost, and expected to bring real
progress -- better understanding, separated explanations, a located
problem, or a changed judgment. If the user asked for an answer and such a
step exists, take it rather than handing it back. Otherwise deliver what is
understood and where its limits are. One check not worth making does not
end the research; the absence of any worthwhile one does.

Before you deliver, look for the check or condition most likely to
unsettle the main direction. If it is authorized, proportionate, expected
to bring real progress, and the purpose is unmet, take it; if you leave
it, give the real reason -- purpose, information value, cost, or
permission. Do not invent an objection to have one; a challenge already
met is cited, not repeated. For an open question, say what new information
would change the direction; no settled answer is not failure, and not
thinking of a counterexample is not confirmation. Do not pad a report to
look complete.

## Boundaries

Before confirmation, nothing that costs, sends data out, or changes
anything: do not search, call a provider, start a worker, run project code
or tests, or create a package. Local profile/registry reads for the card
are allowed and make no external request. Read-only orientation is a
method you may use, not a stage: inside the project this session is in and
the files the user named, read what it takes -- a README, the layout, an
entry point -- to understand the situation, ask a necessary question, or
write the brief, then stop; if the conversation already gives you that, do
not read. A home directory or a parent of several projects is not the
project; credentials and sensitive logs are not in scope just because they
sit inside it; anything outside that scope needs the user, and a file they
named needs no second permission. Do not keep scanning to guess a meaning
you should ask about. What you read is material for understanding, not
evidence: a claim that later rests on it still needs the capture and
checks any claim needs. Nor does it widen egress: the card discloses that
the research question may leave and local files do not; the question you
card may be informed by what you read, but local excerpts, secrets, or
detail do not leave as a "research question", summarized or otherwise --
widening egress is a new card, while sub-queries inside the confirmed
scope need none. A question that is open -- no settled boundary or
answer -- is not one you misunderstand: write locating it as this round's
purpose from what you have; do not invent project knowledge to fill the
brief. The reply `light`, `standard`, or `heavy` confirms that printed
count vector and disclosed provider/egress set for one run; `調整` and
`取消` spend nothing. Re-card when the vector, provider set, or egress
scope changes, or when the purpose or research scope moves past what was
confirmed; sub-questions and methods inside them need no new card.

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

The report and its package are the result of the run. The message that
hands them over summarizes the report -- the link, what matters, the limits
that change how it reads -- and grows no second set of conclusions: no
conclusion, number, comparison, or recommendation the report lacks, and
nothing firmer than the report states. A conclusion that surfaces while
delivering goes into the state first, gets the checks its use requires,
and the report is regenerated and re-bound before it is summarized; if
that cannot be done, it is not this run's result, and the message says
what remained open. Questions, progress notes, and discussion marked
tentative during the run are not bound by this, and an unfinished idea is
never presented as verified.

Keep three things apart. Integrity: the package is intact and unaltered --
the only thing the validator can prove. Correctness: a captured source can
still be wrong and an inference can still be unsound; that judgment is
yours, stated with what would overturn it. Adoptability: a reversible step
can be safe before the whole answer is established, and an established
answer is still not permission to act. A `BLOCKED` package is still
delivered: it names an unmet delivery requirement or an evidence gap, not a
failed research and not a broken package.
