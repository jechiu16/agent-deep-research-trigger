# Deep Research Report

**Query:** smoke test
**Time:** 2026-07-09 12:00:00
**Provider:** demo (demo-local)
**Effort:** medium
**Wall time:** 0s
**Usage:** `{"demo": true, "input_chars": 10, "files": 0}`
**Cost estimate:** $0.0000

---

# Demo Worker Result

This is a local smoke test for `scripts/deep_research.py`. It proves that the worker can:

- parse CLI arguments
- write a report under `<cwd>/reports/`
- print one JSON object on stdout
- append a ledger record when `--ledger` is supplied

It does **not** perform research and must not be used as evidence.

## Echo

Query: smoke test
Effort: medium
