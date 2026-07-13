# RFC 9110 blind comparison

這是 2026-07-13 的單題 exploratory evaluation，不是通用 benchmark，也不支援固定 provider ranking。

## Protocol

- 題目與 qualitative rubric 在解盲前凍結。
- Reviewer 只讀匿名 A、B，不能瀏覽、使用工具或查看 repository 其他內容。
- 不計分，也不把篇幅、引用數或 model 身分當品質代理。
- Verdict 完成後才揭露 mapping。

## Result

Reviewer 偏好 B。B 更清楚區分 June 2022 publication date 與 Internet Standard / STD 97 status，將 RFC 9110 限定為 version-independent HTTP semantics core，並避免把未找到 successor 誤寫成已證明不存在。

這只支持「本題中，將一份 live Deep Research report 與 session context、official direct captures整合後，結果比直接交付原報告更可靠且更適合 coding session」。它不是 full runtime superiority claim；限制見 `provenance.md`。

## Artifacts

- [Frozen task](task.md)
- [Frozen qualitative rubric](rubric.md)
- [Candidate A](candidate-a.md)
- [Candidate B](candidate-b.md)
- [Blind verdict and reveal](blind-verdict.md)
- [Live provenance and resource context](provenance.md)
