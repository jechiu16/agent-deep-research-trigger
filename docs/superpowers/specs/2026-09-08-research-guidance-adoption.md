# 第三輪規格：研究指引換版，不擴充 runtime

日期：2026-09-08。交接對象：FABLE。
狀態：待實作規格；本文件本身不修改或啟用現行協定。
基準：保留第一輪 exploration-first MVP 的未提交工作樹；概念來源為已定稿的
[整合目標稿](../deliveries/2026-09-08-integrated-guidance-draft.md)。

## 目的與本輪決定

把已收斂的研究行為核心換入現行 `SKILL.md`／`HARNESS.md`，讓 host 先判斷值得做的下一步，再使用既有 runtime 保存、查核與交付。不再新增概念稿，也不把七項落差全部變成實作待辦。

本輪是「研究指引＋相應文件檢查」換版，不是整份目標稿無差別複製。啟用新的 brief 措辭與研究行為；不啟用確認前專案讀取，不改 status、合約、quota、provider 或 validator 行為。

## 修改範圍

| 檔案 | 本輪工作 |
|---|---|
| `SKILL.md` | 採用定稿的研究核心、授權與交付說明；只保留本輪有效的指令 |
| `HARNESS.md` | 依定稿整合記錄、查核、交付；如實交代現行限制，不用舊決策流程限制所有研究 |
| `tests/test_docs.py` | 適應段落重組與 brief 更新，移除 60 行限制；保留必要協定檢查 |
| `CHANGELOG.md` | 在既有 Unreleased 下簡短記錄這次指引換版，不動版本號 |

README、AGENTS 與兩個 discovery wrappers 只做唯讀一致性檢查。若因本輪改名造成明確的失效連結或相反指令，可以最小修正文案並在交付說明；不要順便重寫它們。

不修改 `research_harness/`、`scripts/`、registry、budget profiles、其他測試、既有 session／fixtures 或範例報告。保留第一輪的全部既有變更，不自動 commit、push、安裝或發布。

## SKILL.md 的實作要求

1. 保留 frontmatter、明確 `/deep` 才啟動、root SKILL 為唯一公開協定、單次使用者確認與既有輸出物。兩個 host 不新增各自的研究流程。
2. 採用整合稿的 How To Research 八段。第三段負責選值得知道的未知，再選成本相稱的方法；第八段負責依目的、價值與授權判斷是否繼續。可精簡重複文字，但不得把方法改回必經步驟、固定分支數或固定廣深比例。
3. 九行公開卡片只修改第二行為：`Query Brief：{本輪想弄清楚什麼；必要時補充已知與不確定處}`。不新增必填三格、posture 確認或第二張卡片；其他八行不在本輪重設計。
4. Boundaries 保留現行確認前禁令：除本機 card／profile／registry 讀取外，不搜尋、不讀專案、不呼叫 provider、不啟動 worker。定稿內方括號的未生效讀取權限不可放成可執行指令。模糊問題可依現有對話把「定位問題」寫成本輪目的，不補造專案知識。
5. 確認後，已授權範圍內的操作不逐次重問；超出目的、成本向量、provider／外送範圍或操作權限才需新增授權。研究結論不自動授權修改使用者系統。
6. Delivery 先呈現理解的進展；保留 JSON／journal／raw／HTML 與繁中要求。分清完整性、正確性、可採用性；不能承諾 validator 證明內容為真，也不能把完整性通過當成可安全執行。

公開九行模板與 CLI 自身的人讀 card 並非相同排版，且 CLI 已呈現 posture。本輪只改 host 的公開 brief 指引，不修改 CLI 的輸出形狀、JSON 或 hash 綁定；若發現需要 CLI 改動才能成立，列明原因，不自行擴充範圍。

## HARNESS.md 的實作要求

- 以 Recording What You Find、Checking What Carries Weight 與 Execution And Delivery 取代固定的七步 Research Loop，將探索納入共用段落。保留 repo-local CLI、確認後才讀 HARNESS、內部 hash 綁定不是第二次詢問等既有操作邊界。
- hypotheses 的最小紀錄仍是穩定 ID 與可讀文字。basis、來源指標與 next_check 逐步補充；不要新增每句分類、每條假說附來源／下一步、每次工具呼叫留理由的義務。只在重要轉向或交接需要時留簡短說明。
- 暫放與證偽分開；有查核前提的推論仍可留在 observations，不因前提有證據就要求把綜合判斷改成 claim。仍不得用 observations 滿足 evidence floor。
- 任何被當成已驗證或承重依據的主張，都有相應查核責任；探索不是免查理由。這是 host 的責任，不得描述成「所有 status 路徑都已由 validator 保證」。研究查核與依 posture 要求的交接紀錄分開。
- provider 是可選的方法，不是工作量；D2 按預期價值選用。另以明確的現況段落描述仍存在的資格、profile 與 gate 要求，不能暗示未使用 provider 就一定能通過所有交付條件，也不能要求為填紀錄而硬呼叫一次。
- 保留 PASS／PARTIAL／EXPLORED／BLOCKED 現行適用範圍與不足標示。decision 不新增 EXPLORED 出口；探索已有正式主張也不自動升為 verdict。不得把完整性異常當成探索完成。
- 人寫報告可依既有 state 呈現「已查明的局部」，與暫定方向、推論分開，不必有固定標題。備援報告的既有顯示限制如實標註，不改 renderer，也不宣稱兩種報告已完全一致。

保留 runtime 的精確操作要求，但不為保存舊散文而重複整段決策流程。若原文對現行 gate 的描述不精確，可靜態閱讀相關程式後限縮表述；不修 runtime、不把發現轉為本輪新功能。

## 七項差異在本輪的處置

| 差異 | 本輪處置 |
|---|---|
| 卡片 brief | 啟用已定稿的新第二行 |
| 確認前本機唯讀定向 | 不啟用，保留現行禁令 |
| 可交付理解、保留判斷的新 status 方案 | 不實作；可以解釋未完成的委託，不能假稱取得新的完成語意 |
| 空集合 targeted_reverification | 保留現行要求；不自動推導、不虛構查核 |
| Heavy anti_lock_in／profile 要求 | 不改 gate；研究策略與機械要求分開描述 |
| 探索已查明局部的呈現 | 採用 host-authored 指引；備援 renderer 不變 |
| SKILL 60 行上限 | 移除該 assertion，不換成 100 或其他任意數字 |

定稿保留為設計歷史，不改寫成「七項均已實作」。尚未生效的方案留在設計文件及交付說明；現行 skill 不夾帶方括號候選規則，不要求每次研究先讀設計討論。

## 文件檢查怎麼改

只調整 `tests/test_docs.py`，不新建測試框架或 doc schema：

- 公開卡片的九行介面與新 brief 可精確檢查，因為這是本輪有意維持的介面；不要要求 CLI 變成同一排版。
- Before／After Confirmation 改組為 Boundaries 後，檢查仍須守住確認前禁令、單次確認、外送與成本邊界，不能只刪掉失效的舊測試。
- Exploration Runs 被拆入共用段落後，仍檢查 explore／EXPLORED 的現行限制、假說不可冒用 claim 語意、既有查核責任與版本邊界。不要為通過測試保留一個空的舊章節。
- 保留單一協定、wrapper 指向、CLI bridge、既有成本向量、證據鏈、交付物與不足狀態的必要檢查。
- 移除 SKILL 60 行 assertion；不要新增全文快照、逐段文案精確相等、固定段數或研究行為的字數／關鍵字評分。必要協定語句可以有穩定檢查點，一般散文可改寫。

這些靜態檢查不證明探索品質。本輪不要求新實驗、多 host 評測、付費研究或另一份情境推演報告。

## 驗證與交付

實作者 FABLE 可在文件與測試調整後執行限定的本機文件測試 `python -m unittest tests.test_docs -q` 及該 diff 的格式檢查；不要求全套回歸或真實 `/deep` run。ASTRA 本次開規格不執行測試。若使用者另有限制，以其明確指示為準。

交付只需實際修改、結果與一份短說明：

- 清楚區分本輪新增變更與原本未提交的第一輪 MVP，列出本輪實際改動檔案。
- 說明哪些規則已換入、哪些方案仍未生效；必要偏離定稿的地方只解釋差異與原因。
- 如實列出執行過的檢查與結果；未執行就寫未執行，不沿用第一輪測試數字冒充本輪驗證。
- 確認 runtime、公開 CLI 行為、既有資料與版本號未被本輪修改；不聲稱已提升研究品質或跨 host 效率。

完成標準：現行主要指引能一致地說明「下一步怎麼選、何時繼續、哪些主張需要查核、哪些操作尚未授權」，而 host 不必先理解設計文件中的豁免與未決方案。這輪到此為止，不附帶下一輪 status 或 provider 改造。
