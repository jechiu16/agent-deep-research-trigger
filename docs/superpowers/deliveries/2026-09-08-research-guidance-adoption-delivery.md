# 第三輪交付：研究指引換版

日期：2026-09-08。交付者：FABLE。對應規格：
[2026-09-08-research-guidance-adoption.md](../specs/2026-09-08-research-guidance-adoption.md)。
概念來源：[整合目標稿（定稿）](2026-09-08-integrated-guidance-draft.md)。

## 本輪實際改動的檔案

| 檔案 | 本輪 | 第一輪（仍未提交） |
|---|---|---|
| `SKILL.md` | 全文換版：卡片第二行、觸發段、How To Research 八段、Boundaries、Delivery（124 行） | 曾加一句 explore |
| `HARNESS.md` | 全文換版：Research Loop 與 Exploration Runs 拆入 Recording What You Find、Checking What Carries Weight、What a status says（480 行） | 曾加 Exploration Runs 段 |
| `tests/test_docs.py` | 卡片第二行期望值；移除 60 行 assertion；Before／After Confirmation 檢查改為 Boundaries 檢查；Exploration Runs 檢查改為共用段落檢查；研究核心只留邊界檢查點，不釘散文 | 曾加 Exploration Runs 檢查 |
| `CHANGELOG.md` | Unreleased › Changed 加一則 | 曾加 Unreleased 段 |
| `docs/superpowers/deliveries/…adoption-delivery.md` | 本文件 | — |
| `docs/superpowers/deliveries/…adoption.patch` | 本輪限定 patch（上列四個檔案，相對第一輪後的工作樹） | — |

只讀檢查、未改動：`README.md`、`README.zh-TW.md`、`AGENTS.md`、`.claude/skills/deep/SKILL.md`、`.agents/skills/deep/SKILL.md`、`SCENARIOS.md`。README 第 122 行的範例 brief（選出預設值；限目前架構；成功條件…）在新的第二行措辭下仍是合法的「本輪想弄清楚什麼」，不構成相反指令，故未動。全 repo 沒有指向 `#research-loop`、`#exploration-runs`、`#before-confirmation`、`#after-confirmation` 的連結。

未改動並已確認：`research_harness/`、`scripts/`、`provider_registry.json`、`budget_profiles.json`、其他測試、`examples/` 下所有 session 與報告、`pyproject.toml` 版本號。第一輪的全部工作樹變更保留。未 commit、push、安裝或發布。

本輪限定 patch（相對第一輪後的工作樹，四個檔案）：`docs/superpowers/deliveries/2026-09-08-research-guidance-adoption.patch`。產生方式：以 `git archive HEAD` 快照套用第一輪 patch 作為基底，再與現行工作樹逐檔 `diff -u`；已用該基底 `patch -p1 --dry-run` 驗證四檔皆可套用。

## 已換入的規則

- **研究核心八段**：選下一步先問「哪個未知值得解」再選成本相稱的方法；廣度是接觸不同解釋；深入服務理解、區分解釋、改變未知；查核跟著用途走且不逐句貼標籤；改路不擴權、已授權操作不逐次重問、結論不授權執行；依目的、價值、授權判斷繼續或停止。
- **卡片第二行**：`Query Brief：{本輪想弄清楚什麼；必要時補充已知與不確定處}`。其他八行未動。CLI 的人讀 card 與 JSON 未改。
- **Boundaries**：確認前禁令原句保留（do not search, inspect the project, call a provider, or start a worker）；模糊問題以現有對話寫「定位問題」為目的，不補造專案知識；單次確認、外送與成本邊界、Re-card 條件原句保留；確認後 host 唯一作者、provider 只買廣度、超限即停原句保留。
- **HARNESS**：Recording What You Find（每種陳述放哪裡、最小紀錄、切換表）、Checking What Carries Weight（查核依用途；VR、Heavy、coverage audit 的機械要求以現況描述；runtime 對 PASS／PARTIAL 實際強制的項目列表）、What a status says（PASS／PARTIAL／EXPLORED／BLOCKED／INVALID 現行語意）、When a verdict run cannot reach its verdict（用現行 status 誠實交付未完成委託）、Report Authoring（以理解的進展開頭；重要主張的依據可見；推論可引用已查核前提仍標為推論；線索渲染規則；備援渲染不呈現已查明局部如實標註）。

## 仍未生效的方案

- 確認前本機唯讀定向：未啟用，禁令原句在 Boundaries；方括號候選文字未進入現行 skill（測試守住）。
- 可交付理解、保留判斷的新 status：未實作。HARNESS 只說明如何在現行 BLOCKED 下誠實交付未完成委託，並禁止改標 EXPLORED。
- 空集合 targeted_reverification、Heavy anti_lock_in 與 profile 要求：gate 未改，以現況描述，並要求不為填紀錄硬呼叫。
- 探索報告的已查明局部：host-authored 指引已寫入；備援 renderer 未改，文件如實標註兩種報告不完全一致。
- SKILL 行數：assertion 已移除，未換成其他數字。

## 與定稿的偏離與原因

1. Boundaries 的方括號目標措辭整段移除，改為一句「模糊問題以現有對話寫定位為目的、不補造專案知識」。規格第 32 行要求。
2. 「Delivering understanding without the verdict (target semantics)」改寫為「When a verdict run cannot reach its verdict」，只描述現行 status 下的做法。規格差異表第 3 列。
3. 「What a status says today」改為「What a status says」，全文不用 today 語氣，避免暗示 gate 即將解除。規格第 44、48 行。
4. 新增一段 runtime 對 PASS／PARTIAL 實際強制項目的列表（evidence floor、claim 的 corroborated／raw／applicability／entailment／origin、decision 長度上限、VR 紀錄、decision 的 coverage audit 與 `inference_joints` 的 weakest_joint／adversarially_reviewed、lookup 的 T1、standard／heavy 的直接證據、handoff 完整性各項、PARTIAL 的安全行動）。原 HARNESS 從未提到 `inference_joints` 與多項 handoff 要件，host 只會在 finalize 時撞到。依規格第 48 行靜態閱讀 `validation.py` 後限縮表述，未改 runtime。ASTRA 審閱後保留，並分成「Applies before a verdict delivery」與「Applies to an exploration」兩段標明適用範圍；留在 HARNESS，不進 SKILL 研究核心。
5. Checking 段加一句「這是 host 的責任；validator 只查你標為已驗證的鏈，不查你是否把所有承重內容都標了」。規格第 43 行。
6. 探索豁免句依審閱改為明確範圍：只豁免決策專屬交接要求與最低主張數量；凡呈現為已驗證或承重的主張仍遵守適用查核；profile gate 不因本段解除。接著才列探索的最低交付三項。

## 審閱後收尾（2026-09-08）

- HARNESS 門檻段拆為兩段並改寫探索豁免句，如上第 4、6 點。
- `tests/test_docs.py`：研究核心測試改名為 `test_research_core_keeps_authority_and_checking_boundaries`，移除對研究散文的逐句原文匹配，只留三個邊界檢查點（claim 追到擷取來源、只在超出授權時再問、結論不授權執行）；探索共用段落測試改為只檢查欄位名、記錄種類、豁免範圍句、status 現行限制與版本邊界；全域禁止方括號的 assertion 改為只擋「not in force」候選文字，不阻止 Markdown 連結。未新增語意測試框架。
- 限定 patch 補進工作區，位置與產生方式如上。

## 執行過的檢查與結果

| 檢查 | 結果 |
|---|---|
| `python -m unittest tests.test_docs -v` | 12 項通過（審閱後收尾重跑亦通過） |
| `git diff --check` | 通過（收尾後重跑亦通過） |
| `python -m unittest discover -s tests -t . -q`（規格未要求，額外執行） | 624 項通過，1 略過（收尾後重跑亦同） |
| 限定 patch 對第一輪基底 `patch -p1 --dry-run` | 四檔皆可套用 |

未執行：真實 `/deep` run、多 host 評測、付費研究。以上靜態檢查不證明探索品質或跨 host 接手效率有任何提升。

## 完成標準對照

現行 SKILL.md 從卡片之後依序回答：下一步怎麼選（核心第三段）、何時繼續（第八段）、哪些主張需要查核（第六段與 HARNESS Checking 段）、哪些操作尚未授權（第七段與 Boundaries）。host 不需要先讀設計文件；未決方案只留在 `docs/superpowers/deliveries/` 與本說明。
