# 第一步：讓探索型研究可以正常完成

日期：2026-09-07。交接對象：FABLE。
基準：`56a5340a470051f0ab25080f7609758b15d1a35d`，`2.0.0b10`。
狀態：待實作的第一輪規格；本文件不代表功能已存在。

## 目的

使用者的核心回饋：「可追溯很強，但感覺有點綁住了」，需要重新平衡探索的廣度與深度。

本輪只解決一件事：**讓 host 能保存暫定方向、依發現調整探索，並交付有用的方向地圖，不必先把所有內容變成已證實的工程結論。**

完成後，同一套框架應能分辨：本輪是在找方向，還是在做決策。嚴謹程度隨主張的決策責任增加；保存與引用的手續盡量沿用現有 runtime。

## 使用者可見的前後差異

問題：「這個專案除了繼續加 provider，還有哪些值得探索的演進方向？」

目前，各種 canonical package 都要有承重 claims、targeted re-verification、工程 handoff 與 acceptance tests。即使方向地圖已經有用，也可能因為沒有這些欄位被標成 BLOCKED／交付不完整。

本輪完成後，host 可以交付：

- 有希望的方向，以及值得繼續看的理由。
- 暫定判斷、未驗證假說與尚未排除的替代解釋。
- 本輪仍不知道什麼，以及最值得做的下一個檢查。

呈現為「探索完成，方向仍待驗證」。不暗示已做出選型或已證實全部說法。

## 行為要求

### 1. 明確支援 explore

優先沿用既有 `contract.posture`，增加 `explore`。公開 CLI 的 `card`、`draft` 能接受它，host 協定能依使用者「找方向／探索可能性」的意圖選用。既有 CLI 預設與其他 posture 的語意保持相容。

探索交付需要獨立於「答案已通過查核」的完成語意。建議新增明確 terminal status（例如 `EXPLORED`），由 state validation、finalize、render、status 一致處理；不要只把原有 PASS 的 requirements 全部關掉。精確名稱可由 FABLE 依相容性檢查調整，並在交付說明。

### 2. 暫定內容可以先保存

優先使用既有 `hypotheses`、`planned_checks`、`open_questions`；避免另建重複的知識容器。

線索的最小資料只需穩定 ID 與有內容的文字。依據、來源指標、值得追的理由、下一個檢查與已排除原因可以逐步補上。每條暫定線索不需要 raw artifact、exact excerpt、entailment、雙來源或獨立 reviewer。

例如以下只是建議形狀，欄位命名可配合現有程式調整：

```json
{
  "id": "H1",
  "text": "保留薄 skill，可能比新增獨立 runner 更符合日常專案探索。",
  "basis": "暫定假說；尚未測試跨 host 接手成本。",
  "next_check": "用同一份研究資料測試另一個 host 能否找到下一步。"
}
```

已有工具紀錄或來源時應保留引用指標。上述自由適用於明示的假說，不允許將缺證內容標為 corroborated 或冒充直接觀察。

### 3. 廣度與深度依結果切換

在共享 host 協定寫入簡短指引，使用現有 patch／state 即可；本輪不必新增 scheduler：

| 當前發現 | 合理的下一步 |
|---|---|
| 來源只是在重複既有觀點 | 換來源類型、換角度，或停止該分支 |
| 幾條路線都成立，但不知道如何選 | 找能區分它們的檢查、反例或小實驗 |
| 原始前提被推翻，或出現可能改變方向的線索 | 調整子題、展開新方向；保留先前仍有效的成果 |
| 剩餘細節不影響本輪目標 | 標記缺口，交付已有成果 |

這些是策略指引，不是逐項勾選的 validator gate。只在路線實質改變時留簡短理由，不要求每次工具呼叫前填研究表格。

不設必達分支數、文件數、廣掃／深化比例。探索模式下 `light/standard/heavy` 表示可用資源上限，D1／D2 是否使用由其預期價值決定；所有實際付費請求仍遵守既有確認範圍與 boundary。

### 4. 驗證依交付目的分流

有效的探索交付可以沒有 load-bearing claim、最終選型、工程 safe action、可執行 acceptance test，或針對不存在 claim 的 verification record。不能只因缺少這些內容就被 finalize 改成 BLOCKED。

但空白 package 也不算完成：至少有可讀的探索成果（方向或排除結果），以及接續建議或清楚的停止原因；剩餘不確定性若存在，必須明示。程式驗證最低結構，人讀情境評估內容是否有用。

凡已寫入正式 claims／evidence 的內容，仍須遵守適用的來源、引用與 claim 檢查。任何被當成承重決策前提的主張，都不能透過 explore 跳過查核。必要時抽出可共用的 claim validation，不要只在 summary.status 為 PASS 時才保護正式主張。

本輪的 profile 放寬僅針對探索型交付；其他 posture 的歷史規則不在此輪全面重定義。之後使用者要求選型時，走正式 decision 合約；本輪不要求實作同一 session 的合約切換或自動升格。

### 5. 人讀報告與接手資料一致

canonical JSON 與 HTML 都能辨識探索完成及暫定內容。探索型報告優先呈現方向、依據或猜測性質、未知項與下一步；省略不適用的工程決策區塊。

host-authored 指引與 deterministic fallback 必須具有相同語意。兩者都不能把線索渲染成「已驗證事實」，也不能將缺少工程 handoff 顯示為失敗。

下一個 host 能從保存的 JSON 看懂哪些方向暫定、哪些已排除、下一步做什麼；不需要先增加跨專案資料庫。

## 相容與範圍

沿用現有 CLI、儲存、quota 與 artifact 機制。新語意須有明確版本邊界；舊 session 不自動遷移、不改寫歷史 verdict。若新增 contract semantics，檢查所有相關集合及原子性驗證路徑，避免新版本漏掉舊有檢查。

Codex 與 Claude 共用 root `SKILL.md`／`HARNESS.md`；更新相關英／繁中說明與必要 wrapper 內容。此需求屬於開發規格，不是在執行 `/deep`，不要為了開始開發再要求使用者選研究 profile。

本輪不包含新 provider、Apodex 串接、多 agent 排程、MCP server、vector database、自動改寫 prompts、全面重做安裝／確認流程。先前發現的免費 route 與 HTML report hash 缺口另行追蹤，除非是完成本輪必需，避免混入此變更。

## 驗收情境

| 情境 | 預期結果 |
|---|---|
| A. 只有暫定方向，尚無 raw evidence | 經正式 CLI 建立 explore package，保存／validate／finalize／render 後可以正常交付；沒有假 claim 或補造 handoff |
| B. 選 Heavy，但本輪不需要付費 deep call | profile 本身不迫使探索交付補 D1／D2、兩個來源或更多 claims；每個實際請求仍受原有額度限制 |
| C. 中途發現原始方向不成立 | 保存其排除理由、加入新線索、保留其他有效內容；不要求推倒重建全部資料或維持最初路線數 |
| D. 嘗試把未驗證線索當成正式決策依據 | 無法僅靠 explore／完成標記獲得 validated／corroborated 語意；正式 claim 的必要檢查仍有效 |
| E. raw artifact 被改動，或請求超過預算 | 原有完整性檢查與 quota 拒絕仍生效，不因 explore 放寬 |
| F. 讀取舊 decision／lookup／synthesis／scientific package | 行為按原記錄語意維持；不為通過新測試而改寫舊 fixtures 的語意版本 |
| G. 另一個 host 接手探索結果 | 僅讀保存資料，就能指出暫定方向、排除結果與下一步；報告與 JSON 的不確定性標示一致 |

A、B、D、E、F 以必要的公開流程整合／回歸測試檢查；C、G 可先用具體離線 fixture 加人讀審查，不要求付費多 agent 測試。

人工評估題使用本 repository：「除了繼續加 provider，這個框架還有哪些值得探索的演進方向？」檢查方向是否實質不同、是否有值得深入的問題、是否能容許改題。不要把答案固定成指定幾條路線，也不要以篇數或分支數作為品質分數。

## 程式入口提示

- `research_harness/contracts.py`：posture、draft 與 evidence floor。
- `research_harness/state.py`：state／semantics、hypotheses 與相關結構檢查。
- `research_harness/validation.py`：terminal status、claim checks、canonical handoff 與 profile gates。
- `research_harness/rendering.py`：探索呈現、finalize 的 BLOCKED seal、兩種報告路徑。
- `scripts/research_state.py`：card／draft 的 choices 與 status 輸出。
- `tests/test_profile_gates.py`、`tests/test_host_tier_contract.py`、`tests/test_rendering.py`、`tests/test_cli.py`：可沿用的測試模式。

FABLE 可選擇最小且容易維護的實作方式；若需要偏離建議欄位或 status 名稱，保留以上行為並說明原因。若發現目標本身衝突，先提出具體案例與可行修正，再擴大範圍。

## FABLE 交付要求

交付實作 diff、實際測試結果、一份使用新流程產生的離線探索示例，以及短說明：哪些操作被省掉、哪些查核仍保留、哪裡仍有使用摩擦。範例資料須標明示範性質，不能聲稱已完成真實外部研究。

先跑適用測試，再跑 repository 要求的整體檢查。基準全套測試曾於本機 Python 3.12.8 執行 606 項、略過 1 項，其餘通過；這是既有版本的結果，不是本輪已完成的驗證。

交付後由提案方檢查：探索空間是否真正增加、決策責任是否仍清楚、是否引入了新的填表負擔。
