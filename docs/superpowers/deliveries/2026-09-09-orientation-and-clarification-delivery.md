# 第五輪交付：先理解、有困惑先問，再開始研究（FABLE，2026-09-09）

提案：`docs/superpowers/specs/2026-09-09-orientation-and-clarification-proposal.md`（ASTRA）。基準：`ee1ccfa`。本文件第一節是 ASTRA 提案、FABLE 三點補充、ASTRA 回覆三方收斂後的決定，作為本輪的 note；其後是落點與測試。改動檔案：`SKILL.md`、`HARNESS.md`、`SCENARIOS.md`、`CHANGELOG.md`、`tests/test_docs.py`，以及 `README.md`／`README.zh-TW.md` 各一句（理由見範圍聲明）。不加流程、欄位、gate、status、CLI、hash；不動 runtime、卡片模板、歷史 package、範例。未 commit。限定 diff：`2026-09-09-orientation-and-clarification.patch`。

## 收斂後的決定

1. **澄清分兩層，卡片不代替必要的澄清。** 已有根據、模型對使用者意思沒有困惑的重述，直接放進 brief 讓使用者確認；待研究的事實、可以點名的假設、取捨的後果，可以留到研究中處理。模型對使用者的意思、目的或價值取捨仍有困惑，就先問再開跑：不能因為自己想得到一個流暢、合理的讀法就略過詢問，也不必先證明分岔會造成多大差異才准問。權重本身是使用者想探索的東西時，把本輪目的寫成「探索不同取捨及其後果」，不要求使用者先定權重，也不由模型默填。卡片是共同確認讀法的裝置，不是把未解開的困惑轉交使用者自行察覺的裝置。明確不採用「先做合理假設，使用者沒改就算理解正確」。使用者已說清楚的事不重問；沒有困惑不為形式製造問題；沒有固定題數、話輪、問卷或確認清單。
2. **定向的預設範圍。** 目前 session 所在的專案，加上使用者點名的檔案；不反覆問「可以讀專案嗎」。家目錄或多專案的父目錄不算一個專案；憑證與未納入任務的敏感 log 不因位於專案內就自動納入；範圍外要問，使用者已點名的檔案不重複要授權。定向是允許的方法，不是必經階段：足以理解情境、提出必要問題或寫出 brief 就停；對話已足夠就不讀；發現該問的困惑就問，不繼續掃描替使用者猜。
3. **定向不擴大外送。** 契約仍是 `local_file_egress: false`（`research_harness/contracts.py:207`），卡片揭露的是「研究問題可外送，本機檔案不外送」。可以根據定向形成使用者看得到、確認過、符合既有外送範圍的研究問題；不能把本機摘錄、機密或詳細內容換成摘要後當「研究問題」送出。要擴大外送就走既有授權流程（重新出卡），不新增繞過方式；確認範圍內的後續子查詢不必預寫在卡片上。定向所得只是理解材料，不是證據；日後作為主張依據仍須完成既有擷取與查核。
4. **釐清與操作授權是兩件事。** 研究核心的「Ask the user again only for…」改寫成「何時需要重新取得操作授權」，並明寫它限制的是授權不是提問：研究途中發現同類困惑，暫停依賴該解讀的推進並詢問，未受影響的授權內工作繼續；回答不等於授權超出已確認範圍的操作，若回答讓目的或範圍超出確認，重新出卡。
5. **途中等待回答。** package 停在 `IN_PROGRESS`，回答後續跑，不加狀態、紀錄或欄位。卡片前尚未建立 package，也不為等待澄清先建一份。
6. **SCENARIOS 反模式**改為「確認前不得進行超出允許定向的研究」，避免反向允許確認前跑完整本機研究或測試。
7. **歷史決定。** 第三輪保留確認前禁令；第五輪依使用者本輪決定，有意啟用範圍內的本機唯讀定向。不寫成北極星本身自動擴張授權。

## 各項落在哪裡

| 決定 | SKILL.md | HARNESS.md／其他 |
|---|---|---|
| 1 澄清分兩層 | 入口段改寫：先理解使用者要釐清什麼，對話不夠時可唯讀看專案；對問題、目的、優先順序沒有困惑才出卡，brief 寫出那個讀法供確認；仍有困惑就先問（說明困惑在哪、不同讀法會讓你做什麼不同）再出卡；問題內容不足就問，不印空卡。「Start where you are」加一段：分開「還沒研究的事實／可點名的假設／取捨後果」與「不懂使用者的意思」；後者搜尋解決不了，流暢讀法也不能代替詢問，不必先證明分岔多大；「比較好」例子及其限制；權重是探索對象時目的寫成探索取捨及後果；不重問、不造題、無固定題數；沒有困惑的讀法進 brief，卡片是共同確認讀法的地方，不是把困惑丟給使用者察覺的地方 | 無 |
| 2 定向範圍 | Boundaries：確認前禁令改列「search、provider、worker、專案程式或測試、建立 package」；唯讀定向是方法不是階段，範圍是 session 所在專案加點名檔案，讀到足以理解、提問或寫 brief 為止，對話已足夠就不讀；家目錄或多專案父目錄不是專案，憑證與敏感 log 不因在專案內就納入，範圍外要問，點名檔案不重複授權；不為了猜意思繼續掃 | Runtime Bridge：確認前唯一的研究 CLI 命令仍是 `card`；定向用 host 自己的唯讀檔案工具，不是 CLI；尚無 package，不為等回答建立 |
| 3 不擴大外送 | Boundaries：定向所得是理解材料不是證據，日後作為主張仍需擷取與查核；不擴大外送，卡片揭露研究問題可出、本機檔案不出；研究問題可受定向影響，但本機摘錄、機密、細節不以「研究問題」名義出去，摘要也不行；擴大外送重新出卡，確認範圍內的子查詢不必出卡 | Runtime Bridge：理解使用者的提問不是確認、不授權任何事；`local_file_egress` 仍為 `false`，定向讀到的只以卡片揭露的研究問題離開 |
| 4 釐清 ≠ 授權 | 「Changing path is not changing authority」改寫：只有目的、花費、外送、系統變更超出確認才需要新授權；它限制的是授權不是提問；途中困惑用問的，暫停依賴該解讀的部分、保留不受影響的工作、答後續跑；回答不授權超出確認的事，超出就重新出卡 | 無 |
| 5 途中等待 | 無 | Recording「Review progress」段末加一句：對使用者意思或價值的困惑用問的解決，不靠更多材料；package 停在 `IN_PROGRESS`，答後續跑，不加 status、紀錄、欄位 |
| 6 SCENARIOS | 無 | Anti-Patterns：「Research before profile confirmation beyond the read-only orientation the protocol allows.」 |
| 7 歷史決定 | 無 | CHANGELOG Unreleased／Changed 一則：內容摘要與「第三輪保留禁令；第五輪依使用者本輪決定啟用範圍內定向」 |
| README 同步 | 無 | Demo 段「第一次回覆只是一張卡，不會自動開始研究」改為「一張卡，或在 host 不確定你的意思時先問一句；不會自動開始研究」，英文同義 |

「Start where you are」原本「If the question is vague, write locating it as this round's purpose」改為「A question that is open -- no settled boundary or answer -- is not one you misunderstand: write locating it as this round's purpose」，把「問題本身開放」與「我不懂使用者」分開，對應提案「允許問題仍有未知邊界或沒有既有答案；釐清到知道本輪想探索什麼，不等於先把問題框死」。

## 測試

- `tests/test_docs.py` 只改因本輪協定變更失效的釘死片語：Boundaries 的「do not search, inspect the project, call a provider, or start a worker」改為「do not search, call a provider, start a worker」，並新增反向檢查 `inspect the project` 不再出現於 Boundaries；新釘兩個邊界「material for understanding, not evidence」「widening egress is a new card」；研究核心的「Ask the user again only for」改為「New authorization is needed only for」，並加釘「bounds authorization, not questions」。澄清散文（兩層分法、「比較好」例子、權重、不造題）一概不釘；沒有題數、話輪或行為評測。
- 執行：`pytest tests/test_docs.py`：13 passed；全套 `pytest -q`：627 passed, 1 skipped, 246 subtests；`uvx ruff check tests/test_docs.py` 通過。這些只說明改動沒破壞既有協定與 runtime，不證明模型會問對問題。

## 範圍聲明

- README 兩句是因本輪而失真才改：入口允許卡片前的釐清問題後，「第一次回覆只是一張卡」不再成立。不動 README 其他內容。
- HARNESS 只補確認前說明、提問不是確認、`local_file_egress` 仍為 false、途中等待的三處；確認命令、契約流程、hash 綁定全部照舊。
- 沒有為定向新增檔案數、時間、步數配額或另一份日誌；沒有新增 status、欄位、gate。
- 未接觸 AGENTS.md 與兩個 discovery wrapper（本來就未重述禁令）。

## 收尾（ASTRA 審閱後，2026-09-09）

1. **重新出卡條件統一。** Boundaries 原句「Re-card only when the vector, provider set, or egress scope changes」與「Changing path」段的「超出目的或範圍就重新出卡」互相矛盾，改為：vector、provider set、egress scope 改變，或目的、研究範圍超出已確認者，重新出卡；範圍內的子問題與方法調整不需要。`tests/test_docs.py` 的舊句釘死改釘新句「or when the purpose or research scope moves past what was confirmed」。
2. **HARNESS 外送句收窄。** 「what orientation read does not leave except as the research question the card disclosed」可被讀成內容外送的例外通道，改為：定向可以幫助形成卡片揭露的研究問題，但不授權外送本機內容，摘錄、機密、詳細摘要都不行；`local_file_egress` 仍為 `false`。
3. **刪除用字禁令。** `self.assertNotIn("inspect the project", boundaries)` 檢查的是用字不是授權邊界，會擋掉「You may inspect the project within scope」這類合法改寫，直接刪除，不另補檢查。

限定 patch 已重產。重跑：`pytest tests/test_docs.py` 13 passed；全套 `pytest -q` 627 passed, 1 skipped, 246 subtests（收尾後重跑）；`uvx ruff check tests/test_docs.py` 通過。
