# 第二輪提案：研究行為核心（SKILL.md／HARNESS.md 概念修訂稿）

日期：2026-09-08。提案者：FABLE。回應 ASTRA 第二輪方向。
狀態：只提案，不改程式、不改現行協定、不跑測試。第一輪成果與既有安全邊界全部保留。

## 先交鋒：三個我不完全照單的地方

1. **「不主導思考順序」有一個例外必須留：卡片先於研究。** 卡片不是思考順序，是支出與外送的授權邊界。我保留「先確認再花錢」，但把卡片上的 brief 改成允許誠實說「還不知道往哪找」。真正卡住情境一的不是順序，是卡片模板逼 host 憑空寫一句「決策」。
2. **「自由改寫子問題」要畫一條線，否則會撞到 hash 綁定的 question。** 我的畫法：確認過的 question 文字是邊界；子問題、方法、角度在框內自由改，改了在 `framing.assumptions` 留一行；若研究做到一半發現「問題本身問錯了」，那是要交付的發現，不是可以默默換題的理由。這條線現行 runtime 已經在強制（framing.question 必須等於 contract.question），只是文件沒說清楚。
3. **「探索與決策是位置」在現行協定下只能做到一半。** 一個 run 裡同時放已查明的局部（claims）、值得追的方向（hypotheses）與猜想，這個現在就成立，兩種 posture 都可以。做不到的是：decision run 做到一半判斷「不該下結論」，現在只能以 BLOCKED 收尾，把誠實的「還不能決定」標成失敗。這不是文案能解的，列在落差第 3 點，是後續最值得做的一項。

## 一、研究行為核心草稿（可放入 SKILL.md）

放在 trigger 卡片之後、Boundaries 之前。英文是因為 SKILL.md 是 Claude 與 Codex 共用的協定文字；卡片與人讀輸出仍是繁中。

```markdown
## How To Research

One run holds three kinds of statement at once: facts you have checked,
directions worth pursuing, and guesses you have not tested. Keep them apart
in what you write; never force the whole run to become one of them. The
confirmed posture says what this run hands back -- a direction map
(`explore`) or a bounded verdict -- not how you think along the way.

Start where you actually are. State what is already known, what is not, and
what would count as progress this round. If you do not yet know where to
look, the honest brief is "orient first" and `light` is its profile; do not
invent a decision or a success condition to fill the card.

Choose each step by what could change your mind: which one thing, if known,
would most move your current understanding or your next move? Then learn it
the cheapest way -- read the project, fetch the source of record, compare a
case, look for a counterexample, or ask the user. A provider report buys
contact with explanations you cannot reach yourself; it is not a stage, and
unspent budget is not unfinished work.

Breadth is contact with different explanations, not more items. Change angle
or re-cut the sub-question when the options share a doubtful premise, when
sources keep repeating one view, or when a finding unsettles the question as
asked. If the original direction survives that contact, keep it; do not
manufacture alternatives, objections, or a fixed number of branches.

Depth is the check that would change the judgment. Go deeper only where the
answer could move a recommendation, rule an option out, or change what you
would do next; leave detail that cannot.

Checking follows use. A guess may stand without evidence while it is only a
guess. Once a statement supports a recommendation, rules an option out, or
shapes an action, it carries evidence proportionate to that weight: a claim
traced to a captured source, or an explicit note that it is inference. Say
which each statement is -- found, inferred, or guessed; set aside for now,
or shown false; a next step, or ready to adopt.

Changing path is not changing authority. Inside the confirmed question,
count vector, provider set, and egress scope, re-cut sub-questions and
methods freely and note a major turn in one line. A new purpose, spend, data
egress, or any change to the user's system needs the user again. Finding an
answer is not permission to act on it.

Stop when the next step is clear, when more research is unlikely to change
the judgment, or when the budget is spent. Deliver what is now understood,
where it is worth going next, and what could still change the judgment; do
not keep going so the report looks complete.
```

47 行。搭配下面的處置表，SKILL.md 會落在 90 行上下；現行測試釘在 60 行以內，見落差第 5 點。

「檢查跟著用途走」那一段刻意不新增任何狀態。它要求的三組區分，現行 state 已各有位置，只差用語：

| 要區分的 | 現在放哪裡 | 用語 |
|---|---|---|
| 查得的事實／推論／猜想 | `claims`＋`evidence`／`observations`／`hypotheses` | 「有來源」「是推論」「是猜想」寫在 `basis` 或 `text` 裡 |
| 暫時不追／有證據不成立 | `open_questions` 或 `engineering_handoff.constraints`／`hypotheses[].excluded_reason` 或 `counter_evidence_ids` | 「本輪未追，因為…」對「已排除，因為…」 |
| 下一個研究步驟／已可採用 | `planned_checks`、`hypotheses[].next_check`／`engineering_handoff.safe_actions` | 「值得做的下一步」對「可逆的安全行動」 |

## 二、現有指引的處置

釘死在 `tests/test_docs.py` 的片語標為「釘」。本輪不改測試，只標出哪些提案會碰到它。

### SKILL.md

| 段落 | 處置 | 理由 |
|---|---|---|
| Frontmatter、九行卡片 | 保留；第二行「Query Brief：{決策、範圍、成功條件各一句}」改寫為「{已知、還不知道、本輪想弄清楚的事各一句}」（釘） | 現在的三句逼 host 在不知道往哪找時憑空寫「決策」與「成功條件」，是情境一的直接阻礙。卡片仍是一張、仍九行。 |
| `# /deep` 觸發段 | 保留；拿掉第一輪塞進去的 `--posture explore` 括號句 | posture 的意義由核心第一段說明（「hands back what」），觸發段只管卡片。 |
| Before Confirmation | 改寫成 `## Boundaries` 的前半，語句照舊（釘：Do not search、inspect the project、call a provider、start a worker、Local profile/registry reads、make no external request、one run、Re-card only） | 這是支出／外送邊界，全部保留。「inspect the project」與情境一衝突，見落差第 2 點，本輪不動。 |
| After Confirmation 第一段（讀 HARNESS、host 是唯一作者、provider 只買廣度） | 保留，併入 Boundaries 後半（釘：sole conclusion author、buy breadth and structure only、cannot support a canonical claim） | 是誰負責結論的邊界，不是思考順序。 |
| After Confirmation 第二段（用最便宜的 D1、把假說餵給 host、複驗消耗 search、修正被推翻的主張） | 拆兩半：D1 選法移到 HARNESS Provider Routing；「targeted re-verification 才讓主張成為 corroborated；Fix disproved claims、mark unverifiable claims、never withhold delivery」留在 Boundaries／Delivery（釘） | 原段把 D1 寫成流程的固定第二步。核心第三段已把它降為「買接觸的一種方法」。 |
| After Confirmation 第三段（超限即停、Heavy 第二次 deep 只在有實質新角度時） | 併入核心的「Stop」與「Choose each step」段；「Stop external calls at the confirmed count limit」「name the unresolved gap」「no hard gate」「no automatic provider bundle」保留原句（釘） | 內容沒錯，位置錯：它是研究行為，不是確認後的作業指示。 |
| Delivery | 改寫：開頭改成「Lead with the progress of understanding, not the form: what is now known, where to go next, what could change it」；交付物清單、繁中、hash 綁定、完整性語句照舊 | 對應方向六；交付物與安全語句不變。 |

### HARNESS.md

| 段落 | 處置 | 理由 |
|---|---|---|
| Product Contract | 保留；加一句「Budget is a ceiling, not a plan of work」 | 已隱含，說出來就好。 |
| Runtime Bridge、Contract Shape | 保留（釘） | 純 runtime。 |
| Provider Routing | 保留四條規則；從 SKILL.md 收進「D1 選最低價 ready provider」一句；第 3 條 D2 條件照舊 | 第 4 條「Never call a bundle merely because budget remains」已經是核心的精神。 |
| Research Loop 七步 | 改寫成「Recording what you find」：第 1 步「Frame the decision, assumptions, exclusions, and flip conditions」改成「Record where you start: known, unknown, what counts as progress」；第 2 步「Run D1 when deep > 0」改成「If you need contact with explanations you cannot reach, run D1」；第 3～7 步保留，但加前綴「when this run hands back a verdict」 | 現在的七步是決策流程的骨架，探索段落像附錄。改成「發現怎麼落到 state 的哪一格」，兩種 posture 共用同一段。 |
| Exploration Runs（第一輪新增） | 拆解：hypothesis 形狀、廣度／深度切換表、finalize 最低要求、仍查核什麼 → 併入「Recording what you find」與 Execution And Delivery；「Choose `--posture explore` when…」一句上移到 SKILL.md 核心第一段 | 第一輪是「先能完成」；這輪把它從豁免條款變成主段落的一部分。切換表保留（釘），只是不再只屬於 explore。 |
| Execution And Delivery | 保留；加一段「what each terminal status means」：PASS＝有界判斷已查核、PARTIAL＝判斷成立但有安全行動不依賴的缺口、EXPLORED＝理解有進展、判斷未下、BLOCKED＝無法交付或完整性失敗 | 四個 status 分散在 validation 註解裡，host 看不到整體。 |
| Report Authoring | 改寫「Answer first… The headline is what to do or what is true」為「Lead with what changed in understanding; for a verdict run that is what to do or what is true, for an exploration it is where to go next」；三種清單分開（constraints／would_change_if／open_questions）保留；observations 規則保留 | 對應方向六；三清單分開正好是「暫時不追／會翻掉／仍不知道」的區分，不用新表。 |
| Recovery | 保留 | 純 runtime。 |

刪除的只有一件：SKILL.md 裡把 D1 寫成固定步驟的語氣。沒有一條安全邊界被刪。

## 三、三個情境推演

每個只寫三件事：下一步怎麼選、什麼發現讓他換路、何時停。並註明現行協定下怎麼做、卡在哪。

### 1. 完全不知道往哪找

`/deep 這個服務最近變慢，不知道從哪裡查起。`

- **下一步怎麼選**：brief 誠實寫「已知：變慢；不知道：在哪一層；本輪想弄清楚：問題的形狀」，建議 `light`。確認後先讀專案：目錄、最近的 commit、設定、本機 log。每一步問同一句：知道哪件事最能改變我對「在哪一層」的理解？通常是「最近改了什麼」與「慢是全面還是單一路徑」，兩者都是免費的本機讀取。
- **什麼發現讓他換路**：最近的 commit 碰到資料層 → 收窄到查詢路徑；本機什麼都沒變 → 往外看（依賴、基礎設施），這時才值得考慮 D1 買「這類堆疊常見成因」的接觸；light 沒有 deep，就把缺口寫成下一步。
- **何時停**：問題變得具體到使用者能選擇，例如「現在知道慢在查詢路徑；下一步是 standard run 看索引策略，或你先看 DB 指標」。以 EXPLORED 交付：`hypotheses` 兩三條、`open_questions`、`planned_checks`，`framing.assumptions` 記一行「本輪把問題改讀為：慢在哪一層」。
- **現行協定下**：可行，第一輪已支援。卡在兩處：卡片第二行逼寫「決策」；確認前禁止 inspect the project，brief 只能盲寫。見落差 1、2。

### 2. 已有方案但可能問錯問題

`/deep 我們的快取要選 Redis 還是 Memcached？`

- **下一步怎麼選**：不是例行找反方，而是問「哪一個前提如果不成立，整題就不用問或答案會變」。這題最便宜的前提檢查是：瓶頸真的在可快取的地方嗎、要快取的東西是什麼、命中率會有多少。先讀專案與現有量測，再進入兩者比較。
- **什麼發現讓他換路**：前提成立 → 直接比較，不刻意岔開，這是框架必須允許的路；前提不成立（瓶頸在不可快取的計算）→ 在 `framing.assumptions` 留一行「原題前提未成立」，把這個發現當成要交付的答案；來源都引同一份 benchmark → 換來源類型，自己量一次。
- **何時停**：找到並查核了決定性差異（PASS，claim 追到直接來源或本機量測），或前提失敗而交付改讀後的問題與下一步。
- **現行協定下**：前提失敗且能擷取本機證據時，可以 PASS 並以 claim「瓶頸在 X（local-observation）」加 decision「先不選快取，做 Y」。擷取不到證據時只能 BLOCKED／證據不足，把誠實的「不該現在選」標成失敗。見落差 3。

### 3. 探索中找到局部答案

`/deep 除了繼續加 provider，這個框架還有哪些值得探索的演進方向？`（第一輪示例的延伸）

- **下一步怎麼選**：探索中 host 從四個 field packages 的 `events.jsonl` 確認「免費 route 從未被使用」。這是查得的事實：以 local_output artifact 擷取、寫成 claim，並附 excerpt。它改變了什麼？它讓 H3「免費 route 缺口比新增 provider 更影響廣度」從猜想升為有依據的方向，但還沒證明「更影響」。下一步問的是：哪件事會決定 H3 該優先於 H1？
- **什麼發現讓他換路**：這個事實排除了某條方向 → `excluded_reason` 指向該 claim；它打開新方向 → 新 hypothesis，`source_ids`／`artifact_ids` 指回證據。不做的事：把 status 改成 PASS，或把「免費 route 未被使用」寫成「框架應優先做免費 route」。
- **何時停**：剩下的方向各有清楚的下一個檢查，而且沒有便宜的檢查能改變它們的排序。以 EXPLORED 交付，報告寫成「已查明的局部：…（有證據）；仍在探索：…；會改變判斷的是：…」。
- **現行協定下**：可行，EXPLORED package 可以含經完整查核的 claim（第一輪情境 D 的反面）。卡在呈現：explore 的第一畫面沒有「已查明的局部」區塊，claim 落在技術細節裡。見落差 7。

## 四、概念與現行實作的落差（後續議題，不在本輪）

| # | 概念要求 | 現行 | 建議 | 牽動 |
|---|---|---|---|---|
| 1 | brief 可以誠實說「還不知道往哪找」 | 卡片第二行固定「決策、範圍、成功條件」 | 改成「已知、還不知道、本輪想弄清楚的事」 | SKILL.md 卡片、`test_docs` 九行釘死 |
| 2 | 先理解專案再寫 brief | 確認前禁止 inspect the project | 允許本機唯讀定向（不外呼、不寫入、不花錢），或維持禁令但明文接受盲寫 brief 選 light | SKILL.md Before Confirmation 釘死片語；是協定邊界，需 ASTRA 決定 |
| 3 | decision run 可以誠實地「還不能決定」 | 只能 PASS／PARTIAL／BLOCKED；不下結論即 BLOCKED | 允許 decision run 以 EXPLORED 收尾並附一行理由（同合約、不新增支出），或新增「理解已交付、判斷保留」的語意；第一輪的 explore→decision 仍是另開 session | validation 的 status 分派、rendering、第一輪測試 |
| 4 | provider 報告不是必經步驟 | Heavy 的 scientific／decision PASS 要求 `anti_lock_in` 紀錄，且 HARNESS 說它「binding to that call」 | gate 改為「用了 D2 才要求」，或接受「D2 未用，因為…」的 disposition | validation `_validate_pass`、HARNESS |
| 5 | SKILL.md 容納研究核心 | 釘在 60 行 | 上限改 100；九行卡片的釘死不動 | `test_docs` |
| 6 | 改讀後的問題有地方記 | 只有 `framing.assumptions` 可用；question 與 contract 綁定 | 本輪先用 assumptions；之後考慮 `framing` 加一個「本輪把問題改讀為」欄位 | state.py（新欄位，明確延後） |
| 7 | 探索報告呈現已查明的局部 | explore 第一畫面只有方向／未知／下一步，claims 在技術細節 | 第一畫面加「已查明的局部」，只列有完整證據鏈的 claim | rendering |
| 8 | 交付不是填表 | 任何 host-led verdict 都要一筆 `targeted_reverification`，即使 checked_claim_ids 為空 | 空集合時由 finalize 推導，不要求手填 | validation |
| 9 | 找到答案不等於可以執行 | `safe_actions` 是建議，host 不執行；文件沒明說 | 在 Boundaries 明寫「Finding an answer is not permission to act on it」（核心草稿已含） | 只改文案 |

第 3 點是唯一會改變 status 語意的項目，也是「探索與決策是位置」能否成立的關鍵；其餘都是文案、模板或單一 gate。

## 對照成功標準

- 更容易發現值得改問的問題：核心的「Breadth」段給了三個換角度的觸發條件，情境二示範前提檢查不是唱反調。
- 知道下一步為什麼值得做：核心的「Choose each step」把選步驟的問題固定成一句。
- 不多記錄一層「自己如何研究」：草稿沒有新欄位、新狀態、新 gate；唯一要求的紀錄是「重大轉向一行」，落在既有的 `framing.assumptions`。
