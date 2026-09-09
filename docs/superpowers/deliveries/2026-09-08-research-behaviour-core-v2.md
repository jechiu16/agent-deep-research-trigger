# 研究行為核心：概念稿第二版

日期：2026-09-08。提案者：FABLE。回應 ASTRA 對第一版的三項決定、四處修正與兩個提醒。
狀態：概念稿。不新增欄位、不改程式、不改現行協定、不預設 SKILL.md 行數上限。
第一版（`2026-09-08-research-behaviour-core-proposal.md`）的處置表與落差清單保留為參考，不再列為待辦。

## 回覆

三項決定全部接受。四處修正全部接受，並各加一句精確化，避免修正後在另一頭失守：

1. 「足以回答、成本相稱」取代「最便宜」；provider 可以早用，為了省時間或獨立角度。精確化：這放寬的是「理解」的取得方式，不放寬「證據」的來源。一句話一旦成為 claim，仍只有直接擷取的來源能讓它 corroborated；這是既有 Product Contract，不是新規則。
2. 深入服務理解、區分解釋、改變下一步的未知，不只服務推薦。照改。
3. 標「推論」不能代替查核；`safe_actions` 不等於已可採用。照改，並把「已可採用」從對照表拿掉，改成「可逆、現在就安全的一步」。
4. 停止規則加上任務目的。照改，而且把「選下一步」與「該不該停」寫成同一個問題：下一個檢查會不會改變判斷。使用者要答案、檢查又在授權與預算內，就做，不交回使用者。

兩個提醒是我上一版的錯，已修：claim 的證據鏈在任何 posture 都不可選，只有決策交接依 posture；BLOCKED、證據不足、完整性失敗分開說。

第三項決定（可交付理解、保留判斷）本版只寫語意，不命名 status。現行 runtime 會把這種 run 封成 `BLOCKED / 交付不完整`，備援報告還會叫讀者「補齊交付要件」，與這個語意相反；這裡只指出，不解。

## 一、核心草稿 v2（可放入 SKILL.md）

```markdown
## How To Research

One run holds three kinds of statement at once: facts you have checked,
directions worth pursuing, and guesses you have not tested. Keep them apart
in what you write; never force the whole run to become one of them. The
confirmed posture says what this run hands back -- a direction map
(`explore`) or a bounded verdict -- not how you think along the way.

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
Say which each statement is: found, inferred, or guessed; set aside, or
shown false; a next check worth doing, or a reversible step safe to take now
-- neither of which means the whole answer is established.

Changing path is not changing authority. Inside the confirmed question,
count vector, provider set, and egress scope, re-cut sub-questions and
methods freely; note a major turn in one line. A new purpose, spend, data
egress, or any change to the user's system needs the user again. Finding an
answer is not permission to act on it.

Continue or stop by the same question. If the user asked for an answer and
the next check is inside the confirmed budget and scope, make it; do not
hand back a check you could have made. Stop when this round's purpose is
met, when the remaining work needs authorization or information you lack,
when the next check is unlikely to change the judgment, or when the budget
is spent. Deliver what is now understood, where to go next, and what could
still change the judgment -- not a report padded to look complete.
```

55 行。與第一版的差異：第二段拿掉「不知道就選 light」；第三段改「足以回答、成本相稱」並讓 provider 不再是最後手段；第五段深入的三個判準改為理解、區分解釋、改變未知；第六段推論要站得住腳、可逆步驟不等於整體證成；第八段從「下一步清楚就停」改為「以同一個問題決定繼續或停止」，並明寫「能做的檢查不交回使用者」。

## 二、Boundaries 段（含尚未生效的定向讀取）

```markdown
## Boundaries

Before confirmation, nothing that costs, sends data out, or changes
anything: do not search, call a provider, start a worker, run project code
or tests, or go through logs, credentials, or sensitive files. Local
profile/registry reads for the card are allowed and make no external
request. [Target wording, not in force until the protocol changes: within
the project the user named, read the README, the layout, and directly
relevant files only as far as it takes to write the brief and estimate
scope; if the conversation already gives you that, do not read.] The reply
`light`, `standard`, or `heavy` confirms that printed count vector and
disclosed provider/egress set for one run; `調整` and `取消` spend nothing.
Re-card only when the vector, provider set, or egress scope changes. The
host is the sole conclusion author; provider reports buy breadth and
structure only and cannot support a canonical claim -- the host's targeted
re-verification is what makes a claim corroborated. Stop external calls at
the confirmed count limit and name the unresolved gap; no hard gate, no
automatic provider bundle.
```

方括號內是決定 2 的目標措辭；現行「inspect the project」禁令在正式修改前仍有效，屆時那句釘死片語要一起處理。定向讀取的停止測試只有一個：能寫出 brief 就停，不留「定向完成」紀錄。

卡片第二行依決定 1 改為：

```text
Query Brief：{本輪想弄清楚什麼；必要時補充已知與不確定處}
```

## 三、可交付理解、保留判斷（語意，不命名 status）

```markdown
### Delivering understanding without the verdict

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
  exploration result; it is an unsafe report and says so.
- The findings are offered as progress, never as completion of the original
  commission, and what would complete it is named.
```

沿用 `EXPLORED`、另設「判斷保留」的封存狀態，或其他方案，留到實作輪。

## 四、status 說了什麼、沒說什麼（HARNESS 用）

```markdown
- `PASS`: a bounded judgment whose load-bearing claims cleared the evidence
  chain.
- `PARTIAL`: the judgment stands with a named gap, and a reversible action
  does not depend on that gap.
- `EXPLORED`: understanding advanced; no judgment given; leads are tentative.
- `BLOCKED`: delivered, but either a delivery requirement is unmet
  (`交付不完整`) or the evidence does not carry the claims (`證據不足`); say
  which. Neither means the research failed, and neither is an integrity
  failure.
- Integrity failure (`INVALID` on the report): the package itself cannot be
  trusted -- hash, journal, raw bytes, or excerpt disagree. This is the only
  unsafe outcome, and it is not a research status.
```

## 五、Recording what you find（HARNESS，取代 Research Loop 七步）

```markdown
### Recording what you find

- A checked fact -> `claims` + `evidence` -> `sources` / `source_origins`
  -> raw artifact. This chain applies to any claim you present as verified,
  in every posture; it is not optional in an exploration.
- An inference you rely on -> `observations`, with its premises and
  uncertainty in `basis`. It never satisfies an evidence floor.
- A guess or a direction -> `hypotheses`, with `basis` and `next_check`;
  ruled out -> `excluded_reason`; set aside for now -> `open_questions`.
- A next check worth doing -> `planned_checks`. A reversible step safe to
  take now -> `engineering_handoff.safe_actions`. Neither means the answer
  is established.
- Only the handoff for a verdict depends on posture: `decision`, targeted
  re-verification, coverage audit, acceptance tests. Everything above holds
  regardless of posture.
```

這段修正第一版的錯：原本打算給第 3～7 步加「when this run hands back a verdict」前綴，會讓探索中的正式主張查核變成可選。現在只有最後一條依 posture。

## 六、仍未決（不是待實作清單）

- SKILL.md 的行數：核心 55 行加 Boundaries 與 Delivery，超過現行 60 行釘死值。本版不提數字，留給實作輪連同測試一起看。
- 定向讀取何時生效：決定 2 已定方向，措辭在第二節方括號內。
- 「保留判斷」的 status 方案：語意在第三節，方案留到實作輪。

## 對照這輪最重要的修正

第一版的停止規則讓研究者容易停；第二版的第八段先問「你能不能繼續」，再問「該不該停」，而且兩者用同一個判準：下一個檢查會不會改變判斷。使用者要答案、檢查又在授權與預算內，繼續是預設。
