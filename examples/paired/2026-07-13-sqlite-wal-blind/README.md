# SQLite WAL persistence blind comparison

這是 2026-07-13 執行的一次 exploratory evaluation，不是通用 benchmark。
題目要求在固定條件下選擇 JSONL + JSON snapshot 或 SQLite WAL。

## Protocol

- 題目與 adjudication brief 在執行前凍結。
- Reviewer 只讀匿名的 Candidate A、B，不知道 model、provider 或 workflow。
- 不計分，也不以篇幅、引用數或 token 數作為品質代理。
- Verdict 完成後才解盲：A 是 direct OpenAI Deep Research API；B 是 `/deep High`。

## Resource context

| Arm | Calls | Observed output |
|---|---|---|
| Direct Deep Research (`o4-mini-deep-research-2025-06-26`) | 1 paid Deep Research submission | 61,954 API tokens; 5,102 characters |
| `/deep High` | 0 external paid API calls; host web retrieval + Luna verifier | 2,709 characters |

Provider 沒有回傳 dollar cost。這些數字只記錄本次資源背景，未交給 reviewer 當評分依據。

## Result

Reviewer 偏好 B（`/deep High`）。High 的 verifier 在送審前抓到四個 draft
問題：WAL-reset 切換條件過寬、`PRAGMA integrity_check` 語法錯誤、把 VFS
`xSync` 泛稱為 `fsync`，以及缺少 Python `sqlite3` 官方來源。修訂後通過。

Direct baseline 的決定性問題是把 atomic rename 當成足夠的 durability、
把 WAL database 描述成可只複製主 DB 的 single file，以及沿用已過時的
large-transaction 限制。`/deep High` final 沒有命中凍結的 fatal errors。

這只支持「本題中 `/deep High` 較可靠且更可直接交給下一個 coding
session」，不能推論普遍優於所有 Deep Research；baseline 測的是 direct
OpenAI API，不是完整 ChatGPT UI wrapper。

## Artifacts

- [Frozen task](task.md)
- [Frozen adjudication brief](adjudication.md)
- [Direct Deep Research output](direct-deep-research.md)
- [`/deep High` output](deep-high.md)
- [Blind verdict and reveal](blind-verdict.md)
