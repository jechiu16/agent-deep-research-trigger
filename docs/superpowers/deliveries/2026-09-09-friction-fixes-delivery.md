# 2026-09-09 摩擦修正交付（FABLE，使用者直接授權，未經 ASTRA 規格）

指導原則（使用者 2026-09-09 給的核心思想）：這個 skill 是「幫助強模型在與使用者一同釐清一個不一定有答案的複雜問題時，可以幫助他們進行探索並透過落實研究方法形成或幫助形成有效結論的通用框架」。判準：保留守住有效性的邊界，拿掉只為整潔或速度而藏資訊的機械限制。

## 改了什麼

1. **occurrence 不再截斷。** `research_harness/boundary.py` 移除 `SYNTHESIS_EXCERPT_LIMIT = 4000` 與 `CITATION_LIMIT = 40`；`synthesis_excerpt` 存合成全文，`citations` 存全部引用，`synthesis_truncated` 欄位保留、恆為 `false`。spool 仍是位元組級原檔；provider 文字不能支持主張的邊界（`can_support_claims`、不可提升）與長度無關。
   - 實際損失佐證：A 輪 Perplexity 回傳 50 條引用，occurrence 只留 40；C 輪 Gemini 回傳 42，只留 40，C 輪的學生比較是用 40 條算的。已在 `deep-runs/.../PRELIMINARY.md` 附更正。
   - 我原先替截斷辯護的「權利層」理由經查不成立：boundary 不看 retention 一律先寫 spool，retention 只管提升成 artifact。
2. **`excerpt` 子指令。** 免費、唯讀：給 artifact id 與逐字文字（`--text` 或 `--text-file`，後者忽略一個結尾換行），回 `excerpt_start`／`excerpt_end`／`excerpt`／`matches`。位元組比對、不正規化；找不到報錯，多筆報錯並列出 offset，`--nth` 指定其一。不連網、不加鎖、不寫 state。
   - 對 B 輪前六筆證據回跑：五筆 offset 與當時腳本算的一致；第六筆（E6）在 HB22 出現三次（3205／6459／12360，同一句摘要在 meta 標籤與正文重複），指令拒答並要求 `--nth`。B 輪當時的腳本取 `find` 的第一筆；選擇沒錯，但沒看上下文就選了。（初版誤寫為 HB20，ASTRA 指正後更正。）
3. **輸出編碼。** `scripts/research_state.py` 的 `main()` 在 stdout／stderr 非終端機時重設為 UTF-8。Windows cp950 下重導向 JSON 不再壞掉，不必再靠 `PYTHONUTF8=1`。

## 沒改的

- 密鑰底線誤判（`sk-agentcc-*` 觸發 `sk-` 規則）、`citations` 解轉址、確認步驟三個 hash、Heavy 雙上游門檻：安全或設計判斷，留給 ASTRA。
- 學生初稿不可提升成 artifact：host-led 政策，不動。

## 驗證

- `pytest -q`：626 passed, 1 skipped, 246 subtests passed。
- `uvx ruff check research_harness scripts tests`：通過。
- 新測試：`test_occurrence_keeps_whole_synthesis_and_every_citation`（45 條引用、5760 字合成全文完整保留）、`test_cli_excerpt_returns_exact_byte_bounds_for_verbatim_text`（en dash 對連字號不匹配、重複文字拒答、`--nth`、`--text-file`）、`test_cli_json_output_is_utf8_when_redirected`（移除 `PYTHONUTF8` 後子行程輸出仍為 UTF-8）；`test_crossref` 的 40 條上限斷言改為全數。
- 三個實驗 package 用新版 CLI 重驗：round-a／b／c 皆 `ok=true`、0 errors。
- 既有 session 的 occurrence 不受影響（新規則只影響新寫入的 occurrence）。

## 檔案

`research_harness/boundary.py`、`scripts/research_state.py`、`tests/test_boundary.py`、`tests/test_cli.py`、`tests/test_crossref.py`、`CHANGELOG.md`（Unreleased：Added／Changed／Fixed）、`HARNESS.md`（Recording What You Find 兩句）。限定 patch：`2026-09-09-friction-fixes.patch`（只含這次的差異，不含第一、三輪的未提交變更）。未 commit。
