# 第六輪交付：在第五輪協定上跑一次真實研究（FABLE，2026-09-09）

提案：`docs/superpowers/specs/2026-09-09-live-run-field-note-proposal.md`（收斂後版本）。協定：工作樹的第五輪 `SKILL.md`／`HARNESS.md`（未 commit）；CLI：`~/.claude/skills/deep` @ `ee1ccfa` 的 venv（第五輪未改 runtime）。本文件只說跑了什麼、花了多少、壞了什麼、哪些沒查到；研究結論在報告裡，這裡不重述、不加碼。

## 跑了什麼

- 問題：「幫助強模型在與使用者一同釐清一個不一定有邊界和既有答案的複雜問題時，一個可以幫助他們進行探索並透過落實研究方法形成或幫助形成有效結論的通用框架」應該長怎樣？有哪些工程先例、業界標竿現在怎麼走、路線差異在哪、有哪些研究方法可參考？
- 姿態 explore，檔位 standard；使用者對九行卡片回覆 `standard`（2026-09-09T05:29Z 確認）。
- Package：`deep-runs/2026-09-09-framework-shape/session/`（`state.json`、`events.jsonl`、`raw/`、`report.html`）。工作檔在 `../work/`（D1 簡報、抓取腳本、patch 腳本、報告產生器、摩擦紀錄）。
- 重驗：`deep-research-state validate deep-runs/2026-09-09-framework-shape/session --json`。
- 結果：`EXPLORED`。41 條逐位元組查核的主張、61 段摘錄、45 個來源、62 份 host 親自擷取的原始頁面；8 條推論（含對「應該長怎樣」的暫定答案 OB8）；7 個方向（2 個排除）；4 個未知；4 個下一步。報告 `report.html` 由 host 親寫，綁定 state sha256 `99deb929…`。

## 流程（實際發生的順序）

1. 卡片前定向：讀 advisor 實驗的 PRELIMINARY 與 explore 範例，沒有讀 repo 以外的東西；讀法寫進 brief，沒有需要先問的困惑（理由見提案）。
2. 建 package、framing patch、送 D1（Perplexity sonar-deep-research）。等待期間先抓正典來源，不等學生。
3. D1 回來（11.6 萬字元、50 條引用）分五段讀完；逐項到一手來源做位元組探針；D1 數字幾乎全對，兩處範圍與歸屬錯誤（CitationAgent 讀成蘊含驗證；OpenAI 澄清與計畫編輯讀漏），一塊完全沒碰（資訊檢索的澄清問題文獻）。
4. 補正典七批共 66 次擷取；一次付費 search（S1）做否定結果檢查：2023–2026 沒有跨系統的「人在迴圈 vs 全自動」對照，最接近是 AutoResearchClaw 單系統消融；再抓三篇驗證。
5. Patch：主張、證據（用 `excerpt` 幫手定位）、推論、方向、未知、下一步、摘要。validate 通過。
6. 交付前挑戰：主方向說「沒有產品公開做主張層驗證」，花第二次 search（S2）找反例；找到 Elicit 的逐主張原文引述（但支持度靠人工評估）與 DeepSciVerify 研究原型；抓三份入庫、補三條主張，收窄 OB2、H2、OB8 與摘要。
7. finalize、親寫報告、`render --host-authored`、validate。

## 花了多少

| 呼叫 | 路由 | 費用（USD） | 用途 |
|---|---|---:|---|
| D1 | perplexity（sonar-deep-research） | 0.6824 | 學生初稿：50 條引用 |
| S1 | sonar | 0.0522 | 否定結果檢查：人在迴圈 vs 全自動的對照研究 |
| S2 | sonar | 0.0642 | 反例檢查：產品是否公開做主張層驗證 |
| 66 次 host 擷取 | host-web（免費） | 0 | 62 份入庫 |

合計約 0.80 美元。search 額度 15 次用了 2 次；deep 1/1。

## 壞了什麼、卡了什麼

細節在 `deep-runs/2026-09-09-framework-shape/work/friction.md`，這裡只列會影響判讀的：

- 密鑰樣式門檻誤擋 4／66 份擷取（gpt-researcher README、GRADE 首頁、STORM README、Google Workspace 部落格），改用替代頁。
- `scholar` 免費路由不在這份合約的能力快照裡（卡片寫 free unlimited，但沒列哪些免費路由在快照內）；改用 arXiv API 走 host 抓取。
- `excerpt --text-file` 在 Windows 正規化換行，跨 CRLF 斷行的摘錄找不到；56 段摘錄有 37 段因頁面重複段落需要 `--nth`。
- Perplexity 官方頁三個全部 403；Marchionini 的 ACM 與 CACM 頁 403；Horvitz 的 MSR 頁 404。
- 使用者曾中止一次並行的抓取與輪詢（工具授權），之後照原計畫續跑。

## 哪些沒查到

- Pirolli 與 Card、Heuer、Horvitz CHI'99 全文、DeepSearchQA 論文只抓到 PDF，文字流壓縮不能逐位元組比對；關於它們內容的陳述留在推論層（OB6、Q3）。
- 產品數字全是自報（Anthropic 內部評測、Google 自家基準），基準分數多為 LLM 評分；本輪只核對「它們確實這樣說」。
- AutoResearchClaw 只讀摘要，且是自動化科學實驗的單系統消融；適用範圍待 P1。
- D1 引用的二手頁（llmdb、digitalapplied、substack 等）一律未用。

## 對協定的減法建議

沒有。這輪沒有遇到 SKILL／HARNESS 兩句互相打架，第四輪的檢查點回顧與第五輪的入口步驟都按字面走了。兩件事給 ASTRA 參考，不是提案：卡片「free unlimited」與快照內實際啟用的免費路由不一致，屬 registry／runtime；`excerpt --text-file` 的換行正規化屬 runtime。研究所得可以啟發修改，不自動授權修改。

## 範圍聲明

- host 是本 skill 的作者，OB8 的綜合有設計者偏差；報告裡每一項都附了非本 skill 的先例或文獻。
- 一題、一個 deep provider、一個 host；不宣稱任何一句指引被證明有效或無效。
- 研究結論交使用者判斷，與 skill 演進分開。未 commit。

## 收尾（ASTRA 內容審閱後，2026-09-09）

五點全部接受，改的是 state 內容，報告重新產生並重新綁定（state sha256 `5116984b…`，report sha256 `85fdc0f6…`，validate 通過）。

1. **人類介入位置。** HC47 原文另有「You can follow progress as it runs and interrupt at any time to refine the focus, including adjusting which sources it can access.」，我初版只擷錄了研究前那段。補 E62，C4 改為明示研究前與研究中兩處。OB1、OB8、摘要改為「以各來源明示的位置為準，一個系統可有多處，文件沒說的寫未說明」；CitationAgent 是代理不是人，不再拿它支持「研究後」。
2. **C40 收窄。** 只保留來源說的評估方法（人工評分重要主張的引用支持度）；產品內是否自動檢查列為本輪未查明。OB2、OB8、摘要同步。
3. **「沒有」改「本輪未找到」。** 一般產品的自動蘊含驗證、以困惑為條件的提問規則、跨系統人機對照研究，三處一律改為「本輪檢索與查閱的公開材料中尚未找到」；Q1 明寫搜尋結果是線索不是不存在的證明。
4. **可追溯不等於語意驗證。** OB2、OB8、H2 改為：validator 核對的是摘錄確實存在於原始位元組與 entailment 標記，摘錄是否支持整條主張仍是 host 判讀；C40 初版就是例子。
5. **移除評估型下一步。** 刪 P2；H1、H2 的 next_check 移除；H1 改為「文獻提供提問方法，不改變使用者明定的『對使用者意思有困惑就先問』」；標題改為「有困惑先問；查核跟著用途」；OB6 的 PDF 方法文獻改列待核對參考，OB8 註明依此。

未動的：主張 C1–C3、C5–C39、C41 與其證據（C4 補了 E62 並改寫，C40 收窄）；摩擦紀錄；沒有減法提案。

ASTRA 核對通過後（2026-09-09）留下兩個不阻擋結案的文字殘留，已處理：Q4 的「沒有任何公開數據」改為「本輪查閱的公開材料中未找到相關數據；未找到不等於不存在」（patch4，只改這一句並記一條前提），報告重產重綁：canonical state sha256 `a4a53a30…`，report sha256 `e0b0ccb1…`，validate 通過；本文件上一段的「C1–C39 未動」已改為排除 C4。第六輪結案：EXPLORED、未 commit、不追加 gate、評估或串接工作。`free unlimited` 是次數上限、不代表所有免費路由都啟用，這點記在摩擦，不擴建也不放寬安全邊界。
