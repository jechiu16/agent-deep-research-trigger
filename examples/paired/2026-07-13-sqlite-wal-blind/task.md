# Paired research task

為一個 Python 3.9+ 的本機研究 session runtime 選擇預設 persistence：

- A：append-only JSONL operational journal + atomically replaced JSON canonical snapshot
- B：SQLite in WAL mode

固定條件：單一 writer、偶爾多個 concurrent readers；每個 session 不超過 100 MB；必須支援 appendable journal、crash-safe canonical state update、斷網恢復；執行於 macOS/Linux；無 daemon；應盡量少 dependency；人類可讀 artifact 有價值，但不是唯一目標。

請給一個 bounded recommendation，並說明：

1. 兩個方案最重要的 failure modes 與 recovery implications；
2. 哪些條件成立時應推翻你的建議；
3. 一個 migration-safe、可逆的下一步；
4. coding agent 可直接執行的 acceptance tests；
5. 支撐關鍵結論的官方或 primary sources。

以繁體中文撰寫，保留必要英文術語。簡潔但資訊完整，正文以約 1,800 個中文字內為目標。不得假設能讀取任何未提供的 repository 或本機檔案。

統一輸出段落：`建議`、`關鍵理由`、`Failure modes`、`切換條件`、`可逆下一步`、`Acceptance tests`、`Sources`。
