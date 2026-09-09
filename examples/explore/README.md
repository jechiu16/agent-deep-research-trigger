# 探索型交付示範（離線）

`01-framework-evolution-directions/` 是一個 **示範性質** 的 explore package，由
FABLE 於 2026-09-07 依
[探索規格](../../docs/superpowers/specs/2026-09-07-exploration-first-mvp.md)
以公開 CLI 流程離線產生：`card → draft → prepare → confirm → init → patch →
finalize → render`。它 **沒有** 進行任何外部研究、搜尋或付費呼叫；方向與依據
全部來自 host 閱讀本 repository 的程式碼與規格，且皆標為暫定。

問題採用規格指定的人工評估題：

> 除了繼續加 provider，這個框架還有哪些值得探索的演進方向？

| 內容 | 數量 | 說明 |
|---|---:|---|
| 保留的方向 `hypotheses` | 3 | 每條附 `basis` 與 `next_check` |
| 排除的方向 `hypotheses` | 2 | 保留紀錄，附 `excluded_reason` |
| 下一個檢查 `planned_checks` | 2 | 指向對應的 hypothesis |
| 尚不知道的事 `open_questions` | 3 | 含兩個規格另行追蹤的缺口 |
| 正式主張 `claims` | 0 | 探索型交付不要求；寫入者仍逐項查核 |

`summary.status` 為 `EXPLORED`，不是 `PASS`；`engineering_handoff` 為空，
finalize 不會因此改成 `BLOCKED`。package 由 `state.json`、`events.jsonl` 與
hash-bound 的 `report.html` 組成，沒有 `raw/`（本輪沒有擷取任何來源）。

接手方式：下一個 host 只讀 `state.json` 就能看出哪些方向暫定、哪些已排除、
下一步是什麼（`planned_checks`、各 hypothesis 的 `next_check`）。要把任何一條
方向變成決策，請另開 `decision` 合約，不要改寫這個 package 的 status。

重跑驗證：

```bash
deep-research-state validate examples/explore/01-framework-evolution-directions/session --json
```
