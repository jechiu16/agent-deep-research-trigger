## 建議

固定條件下選 **B：SQLite WAL**，設定 `journal_mode=WAL`、`synchronous=FULL` 與有限 `busy_timeout`；event 和 canonical state 在同一 transaction 提交。人類可讀性改由 deterministic JSON/HTML export 提供。

啟動時記錄 runtime `sqlite3.sqlite_version`。已修補 WAL-reset race 的版本可直接進測試；舊版只有在單一 connection 能序列化所有 write/checkpoint、排除官方描述的 race 時才放行。

## 關鍵理由

WAL 正好支援單 writer 與 concurrent readers。單一 transaction 可消除 JSONL 與 snapshot 之間需自行維護的跨檔案 commit ordering；Python standard library 已提供 `sqlite3`，不增加第三方 dependency。

A 的 `os.replace()` 只保證成功時 replacement 的原子可見性，不等於 power-loss durability。完整 protocol 還要 flush/fsync 新檔、同 filesystem replace、同步 parent directory，並處理 JSONL partial tail、writer exclusion、hash/replay 與 snapshot/event 分歧。

## Failure modes

- **SQLite WAL：** `-wal` 是 persistent state；只複製主 DB 可能遺失 committed transaction。長 reader 會阻礙 checkpoint、讓 WAL 增長；recovery/關閉期間仍可能 `SQLITE_BUSY`。wal-index 使用 shared memory，因此不能跨 network filesystem。
- **版本：** SQLite 官方揭露低機率 WAL-reset race：影響到 3.51.2，修於 3.51.3，另有 3.44.6/3.50.7 backport；觸發需要多 connection 的 write/checkpoint 競爭，不可把「舊版」直接等同「必然不安全」。
- **JSONL：** crash 可留下半行或「新 event、舊 snapshot」；缺少 file/directory sync 與 replay invariant 時，atomic rename 只會製造錯誤安全感。

## 切換條件

若資料在 network filesystem，或舊 SQLite 又無法保證單 connection 序列化 write/checkpoint，選 A。若文字可 diff/修復比 transaction consistency 更重要且 replay 很便宜，也選 A。只有 process-crash consistency、不要求 power-loss durability時，B 可評估 `synchronous=NORMAL`；本題預設 `FULL`。

## 可逆下一步

先保留 JSONL 為 source of truth，以 feature flag 建立可刪除、可重播的 SQLite shadow store；每批 event 與 materialized state 同 transaction 寫入，逐 revision 比 canonical hash。通過 crash matrix 才反轉 authority；回滾只需關 flag、刪 derived DB。

## Acceptance tests

1. 記錄 runtime SQLite；已知舊版若無單 connection write/checkpoint 證明則 fail closed。
2. 在 transaction 與 checkpoint 各階段注入 `SIGKILL`；重開後執行 `PRAGMA integrity_check` 並要求回傳 `ok`，再另查 event/state 必須全有或全無。
3. 長 read transaction 下持續寫入，驗證 checkpoint、WAL 上限與 `SQLITE_BUSY` retry boundary。
4. 對比只複製主 DB 與「關閉 connection、完成 checkpoint 後封裝」；只有後者可宣稱完整。
5. 同一事件序列重播兩個 backend，逐 revision 比 canonical hash；對 JSONL 每個尾端 byte 做 truncation，只能回到最後完整且 hash-valid record。
6. `SIGKILL` 不證明 power-loss durability；另以 VM/power-cut 驗證 `FULL/xSync`，結論限定於受測 filesystem/hardware contract。

## Sources

- [SQLite WAL、checkpoint、sidecar 與 2026 bug](https://www.sqlite.org/wal.html)
- [SQLite synchronous 與 integrity check](https://www.sqlite.org/pragma.html)
- [SQLite atomic commit assumptions](https://www.sqlite.org/atomiccommit.html)
- [Python `sqlite3`](https://docs.python.org/3/library/sqlite3.html)
- [Python `os.replace` / `os.fsync`](https://docs.python.org/3/library/os.html)
- [POSIX filesystem cache與 rename durability](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap04.html)
