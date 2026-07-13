---
name: deep
description: Portable /deep research trigger for Claude Code and OpenAI Codex. Use only when the user explicitly types /deep to start a bounded, evidence-gated research session.
---

<!-- PURE_TRIGGER_CARD_START -->
問題：{正規化後的問題}
建議：{層級}，因為{一個理由}
Low：只在對話中回答，附上連結。
Medium：為具名缺口補上直接取得的來源，並交付套件。
High：直接取得至少兩個不同來源，並交付套件。
Ultra：完整 High 證據與驗證，並交付套件。
付費上限：Low {N/routes}｜Medium {N/routes}｜High {N/routes}｜Ultra {1/2 total；D1=route；D2=route/無；cost/privacy=disclosure}；本機外送：{否/是：範圍}。
開始：Low｜Medium｜High｜Ultra｜調整
<!-- PURE_TRIGGER_CARD_END -->

# Agent Deep Research Trigger
SKILL.md is the sole human protocol shared by Claude Code and OpenAI Codex.
The first `/deep` response is exactly the eight card lines above, with no prose before or after; normalize and recommend from conversation text only.
The card's route/count is a precise, unverified authorization proposal from conversation text plus static policy; it is not route readiness.
Render every `{...}` token in the card as a concrete value before showing it;
the confirmed Ultra card contains one exact total, never an unresolved range.
If no research question is recognizable, still show the card with
`問題：尚未提供研究問題` and `建議：調整，因為需要先提供研究問題`; do not ask first.
額外付費請求只計 provider/API paid calls；host-native retrieval、local、Organizer 不計，無計畫 external paid route 時預設為 0。

## Before Selection
Host discovery may read the wrapper and canonical SKILL.md to load this
instruction; that is not a research action. Before selection, do not call tools
or inspect research, project, runtime, or source material; do not search the web,
run scripts, start workers, or preflight registry routes. Low never reads or invokes the runtime.
Each concrete card's tier choice is the only confirmation for that run/contract; re-card requires a new choice. `調整` starts no research.

## After Selection
After Medium, High, or Ultra is selected, read [HARNESS.md](HARNESS.md) beside this canonical skill and follow its internal runtime bridge; do not expose bridge commands as user steps.
Only local-preflight the exact routes/counts on the confirmed card. If any route is unavailable, make no paid call: terminate or return to a new concrete card.
Never silently fallback or use a runtime-resolved wildcard; any route, count, or egress change requires a new concrete card and tier confirmation.
When a concrete route is Gemini, it must be explicitly disclosed as D1 or D2 in the initial Ultra card; choosing Ultra authorizes it, and the label must disclose preview, ~$1-3, remote 55d/1d retention, and no ZDR; local egress remains the card field.
Ultra D2 may use only the optional D2 route named on the initial card; the Organizer decides stop/run D2 and its material next question without a second confirmation. A different route, count, egress, privacy, or cost scope requires a new card and run.
Report only: 界定問題 -> 蒐集資料 -> 交叉檢查 -> 形成結論 -> 交付結果.

Low returns a bounded Traditional Chinese chat answer and links. Medium adds a
direct source for a named gap, conflict, or decision risk. High directly gets at
least two different sources. Medium, High, and Ultra always deliver canonical JSON and
`zh-Hant-TW` HTML, including blocked results.

## Evidence And Delivery
Medium load-bearing claims require a directly captured source and a named
marginal purpose. High requires two qualifying captures with distinct canonical
source keys and content hashes, exact excerpts, and shared-upstream disclosure;
agreement never proves independence or truth.
Ultra combines High with an adaptive Deep loop; one choice authorizes at most two submits, and the Organizer may stop or use D2 after the High checkpoint, never a parallel provider bundle. The full report is consumed with bounded session context; useful decision deltas MAY go in existing observations/notes.

Fail closed: an evidence-floor gap yields canonical `BLOCKED`/`證據不足` and HTML
`EVIDENCE_INSUFFICIENT`; a terminal/handoff/completeness gap yields canonical
`BLOCKED`/`交付不完整` and HTML `DELIVERY_INCOMPLETE`.

Write human-facing canonical narrative fields in Traditional Chinese when it is
the user's working language. Preserve exact excerpts, source titles, identifiers,
URLs, and machine diagnostics in their original form.
