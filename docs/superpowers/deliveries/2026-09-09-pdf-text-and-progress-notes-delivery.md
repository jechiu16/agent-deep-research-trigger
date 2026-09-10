# 第七輪交付：PDF 抽字進證據鏈、關鍵節點回報進度、卡片列出實際啟用的免費路由（FABLE，2026-09-09）

這輪由使用者直接指示，不是 ASTRA 提案。起因是第六輪真實研究後，FABLE 以兩個北極星檢視專案提出五點，使用者裁定：PDF 抽字成文本後走同樣的稽核程序；沒有超時問題就加進度回報；卡片預算誠實列出；「已查核」標籤不動；密鑰門檻照舊。基準：master `a11266e`。未 commit。

## 落點

- **`pdf-text` 子命令**（`scripts/research_state.py`）：讀一份已擷取的 PDF artifact，用 pypdf 抽出文字層，以 `local_output` 衍生產物入庫；provenance 記來源 artifact id 與 sha256、抽字工具與版本、頁數、各頁位元組起點、頁分隔符。之後 `excerpt` 與 evidence 直接指向衍生產物。沒有文字層的掃描 PDF 會被拒絕，只當出處。一個本機 action 可以給多份 PDF 共用；沒有 permit 時自動取得。
- **`ingest_local_bytes`**（`research_harness/artifacts.py`）：從記憶體位元組入庫的 local_output 路徑，規則與 `ingest_local_artifact` 相同（permit 檢查、儲存上限、密鑰門檻）。
- **validator**（`research_harness/validation.py`）：`_qualifying_profile_capture` 把「一跳、hash 綁定、來源是 host capture」的衍生產物解析回該 capture 的 canonical_source_key 與 upstream_key；其他 local_output 照舊不算。不放寬任何 gate，只是把出處多解析一跳。
- **卡片**：CLI 卡片新增一行「Free（不限次，本合約實際啟用）：host, host-web, local；registry 裡其他免費路由不在本合約內」，名單取自 light 草約的 `stage_permit_map`，有沒有金鑰都一樣。交付那行改為「背景執行，關鍵節點回報進度」；SKILL 九行模板、README 示範與 test_docs 釘死同步。
- **SKILL／HARNESS**：「Advance on grounds」與 HARNESS「Review progress」各加一句：在本來就要回顧的節點，給使用者幾行標為暫定的進度（現在知道什麼、接下來做什麼、哪裡可以轉向），不等回答，不是確認。HARNESS「A checked fact」加 PDF 路徑說明；Runtime Bridge 命令清單加 `pdf-text`。
- **依賴**：`pyproject.toml` 新增選裝 `pdf = ["pypdf>=4,<7"]`；README 兩語版本說明。本機 clone 的 venv 已裝 pypdf 6.18.0。
- **CHANGELOG**：Added 一則、Changed 一則。

## 測試

- 新增三個 CLI 測試：`pdf-text` 對手工建構的單頁 PDF 產生可搜尋的衍生產物、`excerpt` 能定位、以它建的 evidence 與 claim 沒有 ERROR、validator 把衍生產物的上游解析回 PDF capture、第二份 PDF 共用同一個 action；非 PDF 被拒且不留產物；卡片列出 `host, host-web, local`。
- 全套 `pytest -q`：630 passed, 1 skipped, 246 subtests；`uvx ruff check .` 通過。
- 真實 PDF 煙霧測試：第六輪的四份 PDF（Horvitz CHI'99、Pirolli 與 Card 2005、Heuer、DeepSearchQA）在暫存 session 走 host-capture → pdf-text → excerpt，結果見交接摘要。

## 沒做的、留著的

- 「已查核」標籤不動（使用者：只給人看意義不大）。密鑰門檻不動。`excerpt --text-file` 在 Windows 的換行正規化未修。
- 上次真跑 05:29–08:13 共 2 小時 44 分，事件紀錄沒有 timeout、deadline 或超限；合約的 7200 秒是外部呼叫層的防線，不是整場時限。所以進度回報只是文字規則，沒有加任何機制。
- 第六輪 package 已結案，不回頭補抽字；P3 留給下一次真跑。
- 掃描 PDF 的 OCR／VL 轉錄沒有做；若要做，應標為「模型轉錄」並記模型版本，另開一輪。
