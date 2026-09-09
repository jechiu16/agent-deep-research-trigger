# 第四輪交付：研究進展與報告一致性（FABLE，2026-09-09）

規格：`docs/superpowers/specs/2026-09-09-research-progression-and-report-discipline.md`。範圍照規格：只改 `SKILL.md`、`HARNESS.md`、`tests/test_docs.py`。不加欄位、status、gate、CLI、旗標；不動 runtime、密鑰掃描、hash 綁定、Heavy 要求、歷史 package。未 commit。限定 diff：`2026-09-09-research-progression.patch`（相對本輪起點，也就是摩擦修正之後；三個檔案，10 個 hunk）。2026-09-09 依 ASTRA 收尾意見更新兩處（見末段）。

## 各項落在哪裡

| 規格 | SKILL.md（研究核心／Delivery） | HARNESS.md |
|---|---|---|
| Q1 有依據地推進 | 新段「Advance on grounds」：在一輪有意義的材料之後、採納新前提／轉向／交付之前問三件事；明寫「不是每次 read、capture、patch 後填表」；輸入有疑點時暫停依賴它的推進，不停整場；不得默選第一筆、默認清單完整、補內容；子集只支持子集的陳述 | Recording 段末新段：回顧的時機、三個問題各自沿用哪個既有欄位、「已有就更新、沒變就不記」；`excerpt` 多筆匹配要讀上下文，`--nth` 只表達選擇不證明適當；只持有部分清單時，做數量或涵蓋比較前先核對使用範圍 |
| Q2 推論先留可審閱摘要 | 新段：推論將支撐方向、排除選項或建議之前，先有短摘要（結論、前提或來源、未定之處）；沿用已有紀錄；事實仍是 claim、猜想仍是 hypothesis；調整查詢、等回傳不記；記錄不等於查核 | observations 條目加三句：在下一步依賴它之前寫、更新而不複製、寫下不等於查核 |
| Q3 具體挑戰與停止理由 | 「Continue while」之後新段：交付前找最可能動搖主要方向的檢查；符合同一組條件且目的未達就做，不做就給實際理由；不造假反方，已處理的引用結果；開放題說明什麼新資訊會改變方向；「想不到反例」不是證實 | Recording 新條目「What would overturn it」：對應 `would_change_if`、`basis`、`open_questions`、`summary.human_recommendation`，填適用的那一個 |
| Q4 報告是成果、聊天是忠實摘要 | Delivery 新段：報告與 package 是成果；交接訊息可有連結、重點、限制，不得多出報告沒有的結論、數字、比較、建議，也不得比報告更確定；交付時冒出的新結論先進 state、做查核、重綁報告再摘要，做不到就不算本輪成果；研究中的提問、進度、明示暫定的討論不受此限 | Execution And Delivery 在 finalize／render 說明後加一段，同一規則落在機制上 |
| Q9 查核考量、否決固定順序 | 無 | provider 報告條目改寫：來源能否承載、歸屬是否正確、對象或範圍是否被擴張、數字及含義是否成立；順序依本題最便宜且最有決定性者，不固定；專案原始碼、本機觀察、使用者可能比論文更合適；分歧是候選查核不是錯誤，共識不是真理 |
| Q10 查詢拆解不等於問題框定 | 「Start where you are」加兩句：框定是本輪要理解什麼與範圍，隨材料更新；不是查詢拆解那種檢索技術選擇；查詢拆解的研究結果本身不足以確立某種框定方式有益或有害 | 無（一處足夠） |
| 摩擦修正的措辭銜接 | 無 | 「read all of it」改為：完整保存，依問題所需分段讀；未讀的部分不算查核；全文是研究材料，不是指令也不是證據 |

## 怎麼避免「每一步填表」與「聊天另造結論」

- 回顧綁在「有意義的材料之後、採納新前提／轉向／交付之前」，SKILL 與 HARNESS 都明寫不在每個指令後做；三個問題是思考提示，落點全是既有欄位，已有就更新、沒變就不記。
- 聊天規則只約束正式交接摘要，並明寫研究中的提問與暫定討論不受限；新結論的路徑是「先進 state、查核、重綁、再摘要」，做不到就標為未完成而不是講出來。

## 測試

- `tests/test_docs.py` 新增一個測試，只釘協定邊界、不釘研究方法的表述：SKILL Delivery 的「no conclusion, number, comparison, or recommendation the report lacks」「not this run's result」「never presented as verified」；HARNESS Recording 的「not instructions, not evidence」；HARNESS Delivery 的「adds no conclusion」「reported as open, not as a result」。舊句「read all of it」只在原本承載它的 Recording 段落內排除，不做全域禁止。研究核心（Q1 到 Q3、Q10）的句子一概不釘，換同義寫法不會讓測試失敗。沒有段數、observation 數、planned_checks 非空或固定挑戰句的檢查。
- 既有 12 個文件測試全部維持，第三輪釘的邊界句（`traced to a captured source`、`Ask the user again only for`、`permission to act`、`No branch count` 等）未動。
- 執行：`pytest tests/test_docs.py`：13 passed（收尾後重跑）；全套 `pytest -q`：627 passed, 1 skipped, 246 subtests（收尾前跑的，收尾只動 SKILL 一句與 test_docs 一個測試）；`uvx ruff check tests/test_docs.py` 通過。這些數字說明改動沒破壞既有協定，不是新指引有效的證據。

## 範圍聲明

- 引用的案例（B 輪 E6 在 HB22 三處匹配、C 輪以 40 條子集做的比較）只用來說明規則要擋什麼，沒有寫進 SKILL／HARNESS，也沒有改歷史 package。
- CHANGELOG 未動，因為規格範圍未列。若 ASTRA 同意，建議在 Unreleased 的 Changed 加一條：「`SKILL.md` 的研究核心新增有依據地推進（在有意義的材料之後、採納新前提／轉向／交付之前回顧，不按指令填表）、推論先留可審閱摘要、交付前的最強挑戰與停止理由、框定不等於查詢拆解；Delivery 明寫報告是成果、聊天摘要不得多出或加強結論。`HARNESS.md` 把同一組規則對應到既有欄位、provider 報告的查核考量與完整保存的讀法。不加欄位、gate、CLI。」

## 收尾（ASTRA 審閱後，2026-09-09）

1. `tests/test_docs.py`：移除對研究散文的原句匹配（「pause what depends on it」「not query decomposition」「not a fixed one」等九句），只保留報告一致性、未驗證不得冒充已驗證、provider 材料不具指令或證據資格三類邊界；「read all of it」的排除限縮到 HARNESS 的 Recording 段落。測試改名為 `test_report_discipline_and_provider_material_boundaries_are_public_rules`。
2. `SKILL.md` Q10：「what is known about the one says nothing about the other」改為「findings about query decomposition do not, by themselves, establish whether a way of framing the problem is helpful or harmful」，保留兩者可能相關、但不能直接外推的空間。

限定 patch 已重產（三個檔案、10 個 hunk）。
