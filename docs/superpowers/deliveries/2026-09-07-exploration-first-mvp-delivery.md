# 第一輪交付：探索型研究可以正常完成

日期：2026-09-07。交付者：FABLE。對應規格：
[2026-09-07-exploration-first-mvp.md](../specs/2026-09-07-exploration-first-mvp.md)。
基準：`56a5340a470051f0ab25080f7609758b15d1a35d`（`2.0.0b10`）。

## 結果

| 檢查 | 基準 | 本輪 |
|---|---:|---:|
| `python -m unittest discover -s tests -t . -q` | 606 通過，1 略過 | 623 通過，1 略過 |
| `ruff check research_harness scripts tests` | 通過 | 通過 |
| `git diff --check` | 通過 | 通過 |

新增測試 17 項：`tests/test_explore_posture.py` 16 項（涵蓋驗收情境 A–G），
`tests/test_docs.py` 1 項。既有測試與四個 `examples/field/` package 一字未改。
版本號未動；CHANGELOG 以 `Unreleased` 段記錄。本機 Python 3.12.8，Windows 11。

## 改了什麼

- `research_harness/contracts.py`：`POSTURES` 加 `explore`；explore 的
  `evidence_floor.minimum_load_bearing_claims` 為 0，contract 驗證只對 explore
  允許 0。
- `research_harness/state.py`：`pure_trigger_v5`；`EXPLORE_SEMANTICS`；
  五個 semantics 集合改用具名常數（`STRICT_ATOMIC_SEMANTICS`、
  `_KNOWN_SEMANTICS`、`_QUESTION_BOUND_SEMANTICS`）避免再漏；v5 session 的
  hypothesis 不得帶 `status`／`load_bearing`／`supporting_evidence_ids`／
  `claim_type`，`source_ids`／`artifact_ids` 必須可解析；非 v5 出現 explore
  posture 是結構錯誤。
- `research_harness/validation.py`：`EXPLORED` 加入有效與 terminal status；
  `_explore_delivery_contract` 取代 explore 的 handoff／reverification gate；
  `_validate_claim_chain` 從 `_validate_pass` 抽出，EXPLORED 對任何標
  `load_bearing` 或 `corroborated` 的 claim 跑同一套；explore 不能以
  PASS／PARTIAL 結束，EXPLORED 不能出現在其他 posture 或舊 semantics。
- `research_harness/rendering.py`：explore 第一畫面（有希望的方向、已排除的
  方向、本輪仍不知道的事、最值得做的下一個檢查）；技術細節省略工程交接、
  關鍵主張下限與空的紀錄區塊；其他 posture 輸出不變。
- `scripts/research_state.py`：`card`／`draft` 接受 `--posture explore`；
  人讀卡片多一行探索說明。
- 文件：HARNESS.md 新增「Exploration Runs」（含廣度／深度切換表）；
  SKILL.md、README、README.zh-TW、CHANGELOG 各加一句或一段。
- 示例：`examples/explore/01-framework-evolution-directions/`，由公開 CLI
  離線產生，示範性質，未做外部研究。

## 與提案的交鋒與採用的決定

1. explore 只能以 `EXPLORED` 或 `BLOCKED` 結束；`EXPLORED` 只能出現在
   explore。理由：保住「本輪在找方向還是做決策」這條線。代價：探索中驗到的
   正式主張可記錄為 claim，但不會產生 verdict。
2. explore 的 evidence floor 設 0，其他 posture 維持正值。避免 heavy explore
   合約寫著「至少兩條承重主張」卻永遠不查。
3. hypothesis 禁用四個 claims 詞彙 key，是硬錯誤；排除改用 `excluded_reason`。
   可退成 WARNING，但那會讓情境 D 只剩渲染層防線。
4. 「剩餘不確定性必須明示」不做程式 gate，報告固定顯示未知區塊。
5. 公開卡片九行模板不動（被 test_docs 釘死），只在 SKILL.md 散文加一句。
6. 版本邊界 `pure_trigger_v5`；舊 package 不會學到新語意。
7. explore 最低交付三項：至少一條有文字的 hypothesis 或 open_question、
   `human_status`、`human_recommendation`（承載下一步或停止原因）。
8. claim 檢查共用，PASS 路徑行為不變。
9. Heavy explore 在 draft 時仍需要一個 ready deep provider（既有行為）。
10. 不動版本號。

## 省掉的操作

探索型交付不再需要：承重 claim set、`summary.decision`、可逆 safe action、
`檢查方式 => 預期結果` 驗收測試、`targeted_reverification`、
`coverage_audit`／`anti_lock_in`、evidence floor、profile 的直接證據與
雙上游檢查、每條線索的 raw artifact／exact excerpt／entailment。finalize 不再
因為缺這些改成 BLOCKED。

## 仍保留的查核

contract 的 card／registry／records 三重 hash 綁定；quota 與 cost budget
（超限仍拒絕、`budget_exhausted` 仍註記）；raw artifact 的 size／hash 與
excerpt 位元組比對；state 結構檢查（id 唯一、引用可解析）；report.html 的
state hash 綁定；任何標為 `load_bearing` 或 `corroborated` 的 claim 走完整
`claim -> evidence -> source + source_origin -> raw artifact` 鏈；空白 package
仍封 `BLOCKED / DELIVERY_INCOMPLETE`。

## 仍存在的使用摩擦

1. 公開卡片沒有 posture 一行，使用者在卡片上看不到「這是探索」；
   「決策、範圍、成功條件」對探索用詞不準。改動要連同 test_docs 的釘死模板。
2. 排除一條方向要用陣列索引 patch（`/hypotheses/1/excluded_reason`），
   不是用 id；清單一變就容易錯位。缺一個以 id 定址的 patch 幫手。
3. 下一步有兩個寫的地方：`planned_checks` 與 hypothesis 的 `next_check`。
   渲染以前者優先、後者備援，但 host 可能不確定該寫哪裡。
4. explore 仍要填 `human_status` 與 `human_recommendation` 兩個摘要欄位；
   已是最少，但仍是表格感。
5. 開始探索前仍要 `draft → prepare → confirm → init` 四步 hash 綁定，
   與決策型完全相同；對 light explore 顯得重。
6. Heavy explore 必須有 deep provider 憑證才能 draft，無法把 Heavy 純當上限
   選。
7. 探索途中若真的驗到答案，要進入選型得另開 session 重新 card／confirm。
8. Windows 主控台把 CLI 輸出重導到檔案時預設 cp950，`draft.json` 會壞掉，
   需要 `PYTHONUTF8=1`；產生示例時實際踩到，所有 posture 都受影響。
9. Windows 產生的 package 在報告的「決定性檢查結果」固定顯示兩條
   `session.degraded_*` 警告，對讀者是雜訊。

## 提案方檢查提示

- 探索空間是否真正增加：看 `examples/explore/.../state.json` 的五條方向
  是否實質不同，以及 HARNESS.md 的切換表是否足以支持改題。
- 決策責任是否仍清楚：試著把示例的 H1 改寫成 `claims` 並標
  `corroborated`，validate 應回 `claim.*` 錯誤並在 finalize 封 BLOCKED。
- 是否引入新的填表負擔：explore 的必填只有交鋒第 7 點的三項；
  請檢查是否還能更少。
