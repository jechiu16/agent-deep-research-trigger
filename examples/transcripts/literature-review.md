---
scenario: literature-review
preset: standard
contract: depth=medium | independence=two-source | strictness=gaps
state: required
verification: completed
---

# Golden Transcript: Literature Review

This transcript calibrates a medium `/deep` run where academic evidence matters. It keeps paper claims separate from model summaries and uses Research State because the run has multiple actions.

## Transcript

**User:** `/deep What does the literature say about whether retrieval-augmented generation reduces hallucinations in QA systems?`

**Organizer:** I infer the target: summarize the research position on RAG and hallucination reduction in question-answering systems. No framing question needed; the scope is academic and methods-focused.

Before spending, choose the three-axis research contract:

| Preset | Depth | Independence | Strictness | Tradeoff |
|---|---|---|---|---|
| `standard` (Recommended) | medium | two-source | gaps | Scholar plus one broad scout; enough for a literature synthesis. |
| `fast` | shallow | single | first | Too thin for a literature question. |
| `decision` | deep | cross-family-blind | chase | Use if this drives a high-stakes product claim. |

**User:** Use `standard`.

**Organizer:** Contract confirmed: `depth=medium | independence=two-source | strictness=gaps`.

Created Research State: `reports/deep_state_20260709_rag_hallucination.md`

Initial state snapshot:

```md
# Research State: RAG and hallucination reduction in QA
contract: depth=medium | independence=two-source | strictness=gaps | status=running | started=2026-07-09T12:00:00
framing: literature position on RAG reducing hallucinations in QA; exclude marketing-only claims
hypothesis: RAG generally reduces unsupported answers when retrieval is relevant, but can preserve or amplify errors when retrieval quality is poor
next action: run scholar and a broad scout in parallel
spend: running total $0.00; ledger=reports/deep_state_rag_hallucination.ledger.jsonl
claims: none yet
evidence: none yet
open: gaps=mechanisms, limits, evaluation caveats; disputes=none
log: 1: initialized state after standard contract
```

## Actions

Batch 1:

- `scholar --effort medium "retrieval augmented generation hallucination question answering"`
- `cascade "RAG hallucination reduction QA systems evidence counter evidence"`

Reason: `scholar` gets paper candidates, while `cascade` gives landscape/counter-evidence from a different retrieval shape. They are parallel-safe.

Batch 2:

- `host-fetch`: inspect primary paper abstracts/method sections for the two most load-bearing claims.
- `sonar`: targeted check for "RAG can increase hallucination when retrieval context is irrelevant".

Reason: the first batch found a consensus direction but the failure-mode claim remained load-bearing.

## Evidence Status

| id | claim | status | sources | independence |
|---|---|---|---|---|
| C1 | RAG tends to reduce unsupported QA answers when retrieved passages are relevant and grounded. | corroborated | scholar paper set; cascade landscape; primary abstract checks | Semantic Scholar + Perplexity + host fetch |
| C2 | RAG does not eliminate hallucinations; poor retrieval, stale documents, or misleading context can still produce unsupported answers. | corroborated | scholar paper set; sonar targeted check; primary abstract checks | Semantic Scholar + Perplexity + host fetch |
| C3 | Reported gains vary heavily by retrieval quality, task, citation/evaluation method, and whether abstention is allowed. | single-source | scholar paper set | Semantic Scholar |

## Reconciliation

The evidence supports a qualified answer rather than a universal claim. `C1` and `C2` meet the `two-source` bar. `C3` is still `single-source`, but it affects nuance more than the headline conclusion.

Updated Research State:

```md
hypothesis: RAG reduces hallucinations when retrieval is relevant, but retrieval failures and evaluation design limit the claim
next action: verification floor on C1 and C2
spend: running total $0.11; ledger=reports/deep_state_rag_hallucination.ledger.jsonl
claims: C1 | RAG helps with relevant retrieval | conclusion | corroborated | none
claims: C2 | retrieval failures can still hallucinate | conclusion qualifier | corroborated | none
claims: C3 | evaluation design changes measured gains | nuance | single-source | optional follow-up
evidence: E1 | paper set | corroborated | reports/deep_..._scholar.md | Semantic Scholar
evidence: E2 | landscape/counter-evidence | corroborated | reports/deep_..._cascade.md | Perplexity
open: gaps=evaluation taxonomy; disputes=none
log: 2: targeted check resolved the failure-mode claim
```

## Verification

Verification floor completed:

- Spot-checked `C1` against primary abstracts/method descriptions.
- Spot-checked `C2` with a targeted independent lookup.

No contradiction found. `C3` remains a nuance gap, not a blocker under the `standard` contract.

## Delivery

Executive answer: the literature supports a qualified "yes": retrieval-augmented generation can reduce hallucinations in QA systems when retrieval is relevant and grounded, but it does not remove hallucinations and can fail when retrieved context is wrong, stale, or mismatched.

Research contract: `depth=medium | independence=two-source | strictness=gaps`; framing assumption: summarize academic evidence, not vendor claims.

Key findings:

- `C1` RAG reduces unsupported answers under relevant retrieval: `corroborated`.
- `C2` RAG still fails under bad retrieval/context: `corroborated`.
- `C3` measured effect sizes vary by evaluation design: `single-source`, included as caveat.

Load-bearing claims:

- If `C1` were false, the headline answer would flip.
- If `C2` were false, the answer would overstate RAG reliability.

Spend and artifacts:

- Spend: about `$0.11`
- State: `reports/deep_state_20260709_rag_hallucination.md`
- Ledger: `reports/deep_state_rag_hallucination.ledger.jsonl`
- Reports: `reports/deep_..._scholar.md`, `reports/deep_..._cascade.md`, `reports/deep_..._sonar.md`

Recommendation: phrase any product or research claim as "RAG reduces hallucinations when retrieval quality is high" rather than "RAG solves hallucination."

Handoff: if another Agent resumes, inspect `C3` by building a small evaluation taxonomy across papers and separating open-domain QA from domain-specific QA.
