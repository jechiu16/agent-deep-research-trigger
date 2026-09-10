# 第九輪交付：真實研究「研究方法指引的文獻依據」（FABLE，2026-09-10）

第八輪 merge 後，使用者裁定下一題是「研究方法指引」，並選擇先研究一輪、standard 檔位。這是第二次真跑，也是第七、八輪功能（pdf-text、免費路由、進度回報、節流）的第一次實戰。研究途中未改 SKILL、HARNESS、runtime、測試。未 commit。

## 題目與確認

「模型在研究過程中，對單一證據的判讀（找到字句是否等於支持主張、沒找到是否等於不存在、沒讀過的來源能支持什麼）與決定下一步（何時換角度、何時停），既有研究方法學（情報分析、實證醫學、資訊搜尋行為等）怎麼規定？哪些可以直接寫成給強模型的規則？」

九行卡片建議 standard，使用者回覆 Standard（2026-09-10）。姿態 explore。CLI 為工作樹 `scripts/research_state.py`（含第七、八輪程式碼），系統 Python 加 pypdf。

## Package

`Desktop/研究/deep-runs/2026-09-10-evidence-rules/session/`，工作檔在 `../work/`。

| 項目 | 數字 |
|---|---|
| 狀態 | EXPLORED，validate 通過（僅 Windows 的兩個 degraded 警告） |
| state sha256 | `9734a5c9…`，revision 53 |
| report sha256 | `e0fef509…`，host 撰寫並綁定 |
| 文獻陳述（claims） | 33，全部 corroborated、非承重 |
| 摘錄（evidence） | 74，逐位元組比對 |
| 來源 | 27；host 擷取 32 份，其中 11 份 PDF 以 pdf-text 抽出文字層 |
| 推論（observations） | 7；方向 6；未解問題 5；下一個檢查 4 |
| 外部呼叫 | D1 perplexity sonar-deep-research 0.6484 USD；sonar 兩次 0.0365 USD；Europe PMC 兩次、Crossref 一次（免費） |
| 總花費 | 0.6849 USD |
| 時間 | 08:01Z 起，08:26Z 封存，約 25 分鐘 |

## 找到什麼

五條起始規則，四條有多個獨立方法學來源直接支持，第五條只有相鄰規範：

1. **沒找到只能寫「本輪未找到」**（OB1）：Altman 與 Bland 1995（C1）、Cochrane 15.6.4（C2）、Heuer 的 absence of evidence 與 unproven／disproved 之分（C3、C4）；「未找到」要有意義須說明 what／when／how：PRISMA 第 7 項與說明文件（C5、C6）、Cochrane 4.5（C7）、ICD 203 資訊缺口（C8）。
2. **找到字句不等於支持主張**（OB2）：ICMJE「能證明所引文獻支持所附陳述」（C9）、Heuer 診斷力（C10）、ICD 203 區分資訊與判斷（C11）、GRADE 直接證據（C12）；量測到的落差：醫學文獻引用錯誤率 14.5%–25.4%，主要類型是「未能支持、無關、牴觸」（C13–C15）；引用把假說變事實（C16）；描述被當規範 50.7%（C17，二手轉述）。
3. **沒讀過的來源只證明它存在**（OB3）：約 20% 引用者讀過原文、70–90% 引用是抄的（C19、C20）；MLA 與 ORI 明文禁止以摘要或二手摘述代替閱讀（C30、C31）。
4. **何時停、何時換角度，文獻給判準不給數字**（OB4）：Cochrane 4.4.11（C21）、Pirolli 與 Card 的探索／利用取捨（C22）、Bates 演化式搜尋（C23）、Simon 滿意即止（C24）、Guest 2020 新資訊門檻且不保證（C25）、Francis 2010 的 10+3（C32）、Leese 2021 未達飽和不等於無效（C33）、Heuer ACH 步驟（C26）、DeepSearchQA 的過早停止與撒網過寬（C27）。Heuer 的診斷力就是 SKILL「what could change your mind」的文獻名稱。
5. **下一步只服務確認過的目的**（OB5）：只找到 ICD 203 客戶相關性（C29）與 Horvitz「不確定就問、考慮打擾代價」（C28）；沒有直接規範文本，依據主要是第六輪經驗。

**D1 的表現**（OB6）：指出 ICMJE、Simon、Bates、飽和文獻四類我沒想到的來源；但它引的 ICMJE 三句只有一句在現行版找得到，把 Heuer 的 ACH 標為未驗證而原書就有，資訊覓食公式未經原文核對未採用。**文字層限制**（OB7）：連字脫落、斷行保留，摘錄照原樣。

**反例探測**：S1 問「是否有規範明文允許只憑摘要引用」，回報未找到並指向 MLA 與 ORI 的反向規定，已抓取核對；S2 列出飽和判準的批評與替代方案，只核對了 Francis 與 Leese，其餘是線索（Q4、Q5）。

## 沒查到、留著的

- Pirolli 與 Card 1999、Guest 2006、Malterud 2016、Glenton 與 Carlsen 2019 原文未抓到（Q1、Q2、Q5、C17 的範圍）。
- 引用錯誤率數字全來自醫學文獻；對模型研究沒有量測（Q3）。
- 飽和與資料庫檢索的停止規則能否移植到模型研究的「一個 patch」，沒有文獻直接回答（OB4）。
- APA Style 兩頁被擋（212 位元組），未用；Semantic Scholar 當日限流，本輪未用。

## 摩擦

細節在 `work/friction.md`。會影響下一輪的兩件：

- **finalize 不會自己把 explore 包設成 EXPLORED**：host 要先 patch `summary.status`，finalize 只負責降級。第一次 finalize 把包封成 BLOCKED 並蓋掉 human_status，補 patch 後才正常。HARNESS 缺這一句。
- **open_questions 兩種欄位名都收**（`question`／`text`），兩輪 package 不一致。

其餘：PMC 網頁對非瀏覽器只回殼、Europe PMC REST 全部成功；74 段摘錄 73 段一次命中，失敗的一段是 HTML 片語中夾 `<i>`；進度回報依第七輪規則做了三次，沒有遇到需要問的困惑；免費路由第一次實戰三次全成功。

## 下一步（P4，待使用者裁定）

把 OB1–OB5 各寫成一句進 SKILL／HARNESS，附本 package 的主張編號為出處；不新增流程、欄位或 gate。以下是 FABLE 的草擬措辭，**不是研究結論**：

- SKILL「Checking follows use」：A search that finds nothing supports "not found this round", never "does not exist"; say what was searched, where, and when. （C1–C8）
- HARNESS「A checked fact」：`excerpt` finding the words shows the words exist; whether they support the claim at its scope is your judgment, recorded as `entailment`, and the sentences around the excerpt can narrow or reverse it -- read them before you record. （C9–C17）
- HARNESS 同段：A source you have not read supports nothing beyond its existence and title; a PDF you only captured stays provenance until `pdf-text` or reading. （C19、C20、C30、C31）
- SKILL「Breadth」：Finding only the sources you already knew is a sign the search is biased toward them, not that the field is small. （C21）
- SKILL「Before you deliver」：...and do not add next steps that serve a purpose other than the confirmed one. （C28、C29；主要依據為第六輪經驗）

另外一句給 HARNESS「Execution And Delivery」：Set `summary.status` yourself (`EXPLORED`, `PASS`, or `PARTIAL`) before `finalize`; it only downgrades to `BLOCKED`. （本輪摩擦）
