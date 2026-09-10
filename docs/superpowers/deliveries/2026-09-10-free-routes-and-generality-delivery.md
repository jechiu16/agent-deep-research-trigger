# 第八輪交付：免費路由接進草約、去單一專案化（FABLE，2026-09-10）

起因是第七輪 merge 後以兩個北極星重新打分，通用性 5／10 是最低的一項。使用者裁定先整理這部分，免費路由預設全開。基準：master `584a5e5`。未 commit。

## 根因

session 初始化時的能力快照只收 `stage_permit_map` 裡引用到的路由。`draft_host_led_contract` 寫死只放 host、host-web、local，所以 registry 裡八條免費 probe 路由（scholar、crossref、europe-pmc、github、pypi、osv、nvd、ietf）從未進過快照，`execute` 一律回「not enabled in the capability snapshot」。第六輪真跑就撞到這個，當時繞道 arXiv API 走 host 抓取。

## 落點

- **草約**（`research_harness/contracts.py`）：對每條 ready 的免費 probe 路由加一條 `verification` 階段的 mapping，各 `FREE_PROBE_CEILING = 40` 次，probe 實體上限同步加總。成本預算對 free 類別本來就不設限，40 是 request boundary 的防線不是計畫。demo 路由不支援 verification 階段，自然排除。`free_routes` 參數可縮小名單，名單外或非免費的路由拒絕。
- **CLI**（`scripts/research_state.py`）：`draft --free-route`（可重複）對應上述參數。卡片 Free 行改為「Free（不限次，本合約實際啟用）：{名單}；查詢會送到這些端點，不含本機檔案；不在名單上的免費路由不能呼叫」，名單仍從 light 草約算出，現在會列出 11 條。
- **HARNESS**：Provider Routing 加一段說明草約啟用哪些免費路由、卡片會列、`--free-route` 縮小、不在草約的路由不在快照。
- **README 兩語版**：Quickstart 與示範卡片的 Parallax 改為「本專案」；Profiles 表後加一句免費路由說明；Field Acceptance 標明四個 package 是 2026 年 7 月單一專案、較早合約層級的紀錄，並指向 `examples/explore`。
- **SCENARIOS**：Expected Behavior 加「沒有既定邊界的問題 → explore 姿態，交付 EXPLORED」一列；Interaction Shape 第二步補「或先問一句」；驗收題拿掉專案名，加第四題 explore 姿態（第六輪的問題）與通過條件。
- **examples/field/README**：頂端一段標籤，package 內容不動。
- **CHANGELOG**：Added 一則（`--free-route`），Changed 兩則。

## 測試

- `test_contracts`：light 與 standard 草約都含八條免費 probe、都在 verification、各 40 次、實體上限正確、確認後 `validate_contract` 無錯、引用紀錄含這八條；`free_routes=["scholar"]` 只剩一條，`["sonar"]` 被拒；用真實草約初始化的 session 透過 `execute_probe` 以 scholar fixture 執行成功。
- `test_cli`：卡片列出 11 條免費路由；`draft --free-route crossref --free-route ietf` 只剩兩條免費 probe。
- `test_docs`：SCENARIOS 釘死改為四題、不含 Parallax、含 `EXPLORED`。
- 全套 `pytest -q`：634 passed, 1 skipped, 248 subtests；`uvx ruff check .` 通過。
- 真實煙霧（工作樹 CLI，暫存 session，light、explore）：卡片列 11 條；草約 probe mapping 為 openalex 5、sonar 5、八條免費各 40，實體上限 330；`execute --route crossref` 成功回 20 筆；`execute --route scholar` 到達端點後上游回 HTTP 429（Semantic Scholar 無金鑰共用池限流，與 `tests/test_scholar.py` 記錄的情況一致），action 依規則燒掉不重試；free 用量 2，validate 無 ERROR。

## 沒做的、留著的

- Semantic Scholar 無金鑰時不可靠；registry 不要求 `S2_API_KEY`，金鑰仍是選用。見下方追加段。
- `tests/test_scholar.py` 裡「registry 出貨時 scholar 是關閉的」那句註解已過時（現況為開啟），未改。
- `tests/test_cli.py` 的卡片測試輸入字串仍有 Parallax 一詞，只是輸入不是釘死的輸出，未改。
- SKILL.md 方法核心未動；範例與情境放在 SCENARIOS。
- 打分裡另外三項未動：真跑驗進度回報、切一版 2.0.0b11、其他不在本輪。

## 追加：scholar 金鑰與節流（同日）

使用者提供 Semantic Scholar 金鑰與其條款：有金鑰時全端點合計每秒 1 次請求。

- **金鑰不進 repo。** adapter 本來就會在環境變數 `S2_API_KEY` 存在時送 `x-api-key` 標頭；request fingerprint 對 `api-key` 類標頭一律遮罩，事件日誌與 spool 不含金鑰。金鑰由使用者自己設在 host 環境，FABLE 不寫進任何檔案或設定。
- **節流**（`research_harness/boundary.py`）：registry 新增 `transport.min_interval_s`；`execute_probe` 在送出前找同路由最近一筆 `permit_acquired` 的時間，睡到間隔滿足為止。日誌時間戳只有秒級精度，所以多留 1 秒；多睡一秒無害，429 會永久燒掉 action。scholar 宣告 1 秒，其他路由沒宣告就不睡。
- **registry**：scholar 的 metering 註記改為「共用池常回 429；S2_API_KEY 給每秒 1 次」，verified_at 2026-09-10（依使用者提供的條款，未另行查文件）。
- **HARNESS**：Provider Routing 補一段：設 `S2_API_KEY`、boundary 依宣告節流、同一路由不要平行打。
- **測試**：以真實 host-led 草約建 session，連續兩次 scholar 執行，第一次不睡、第二次睡 1.6 秒（1 + 1 − 0.4）；沒宣告間隔或沒有前一筆時回 0。全套 636 passed, 1 skipped。
- **真實驗證**：使用者以 `setx` 自行設定 `S2_API_KEY` 並重啟 host 後，同一支煙霧腳本在工作樹重跑：`execute --route scholar` 成功回 20 筆、crossref 成功回 20 筆，free 用量 2，validate 無 ERROR。金鑰只存在於 host 環境，FABLE 未經手。同一分鐘內接著的四次帶金鑰呼叫（A3–A6，間隔 1 秒以上）全部上游 429，直接以 urllib 對照：帶金鑰 429、不帶金鑰先 200 後 429；等 60 秒再試，search 與 paper 端點帶金鑰都 429。結論：Semantic Scholar 當下對這把金鑰與共用池都在限流，屬上游狀態，不是快照或節流的問題；harness 行為正確（路由可達、429 依規則燒掉 action、不重試）。
