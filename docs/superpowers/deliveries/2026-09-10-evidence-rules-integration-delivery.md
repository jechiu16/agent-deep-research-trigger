# 第十輪交付：把第九輪的證據規則整合進 SKILL／HARNESS（FABLE，2026-09-10）

使用者指示：對照現有 HARNESS 與 SKILL 通盤檢討、整合第九輪的發現，原則守住，但不要冗長又機械。基準：master `584a5e5` 加第八輪未 commit 的變更。未 commit。

## 檢討結論

先對照，再動筆。第九輪找到的五條規則裡，SKILL 已經有三條的骨幹：

- 「Choose each step by what could change your mind」就是 Heuer 的證據診斷力（C10），不重寫。
- 「One run holds three kinds of statement」與 HARNESS 的 claims／observations／hypotheses 分層，就是 ICD 203「區分資訊與判斷」（C11）和 Heuer「未證明與被推翻不同」（C4），不重寫。
- 「Advance on grounds」已列出「a quotation that matches in several places」這類使用限制，只缺「前後句會改變意思」這一項。

所以整合是補子句，不是加段落。每處一句以內，共 SKILL 四處、HARNESS 四處，沒有新段落、流程、欄位或 gate。

## 落點

SKILL.md（How To Research）：

- **Breadth**：換角度的觸發條件加「a search returns only what you already knew」（C21，Cochrane 4.4.11）。
- **Advance on grounds**：使用限制加「or whose neighbouring sentences change its meaning」（第六輪漏讀下一句的錯；C9、C17）。
- **Checking follows use**：「a fact is a claim traced to a captured source」補成「you have read -- an unread source supports nothing beyond its existence, and a search that finds nothing supports "not found this round", with what was searched, never "does not exist"」（C1–C8、C19、C20、C30、C31）。被釘死的片語「traced to a captured source」保留。
- **Before you deliver**：「Do not pad a report to look complete」補「or add next steps that serve a purpose other than the confirmed one」（C28、C29；主要依據為第六輪經驗，OB5 已註明文獻支持弱）。

HARNESS.md：

- **Set aside for now**：`open_questions` 也收「not found this round」，附搜了什麼、在哪裡。
- **A checked fact**：`excerpt` 命中只證明字存在，支持與否是 host 判讀、記在 `entailment`，前後句可能收窄或推翻，記錄前先讀；PDF 摘錄照文字層原樣（連字、斷行）；抓到的 PDF 在抽字或讀過之前只是出處。
- **Execution And Delivery**：host 要先自己設 `summary.status`，`finalize` 只降級不升級（第九輪摩擦：第一次 finalize 把 explore 包封成 BLOCKED）。

其他：CHANGELOG 一則；`tests/test_docs.py` 新增一個測試釘住九個片語。

## 沒做的

- 沒有寫進任何數字（引用錯誤率、飽和門檻、10+3）：文獻給的是判準，數字來自醫學與訪談研究，OB4、Q3 已說明不能借用。
- 沒有把 PRISMA 的 what／when／how 寫成表單；「with what was searched」一句已足。
- 沒有動 SKILL 方法核心的其他措辭；沒有加範例。
- open_questions 的 `question`／`text` 兩種欄位名照舊都收，未統一。
