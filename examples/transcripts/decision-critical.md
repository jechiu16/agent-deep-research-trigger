---
scenario: decision-critical
preset: decision
contract: depth=deep | independence=cross-family-blind | strictness=chase
state: required
verification: completed
---

# Golden Transcript: Decision-Critical Research

This transcript calibrates a high-stakes `/deep` run. It demonstrates cross-family evidence, blind isolated verification, explicit disputes, and a recommendation separated from evidence. The vendor is hypothetical; this is a behavior transcript, not a factual vendor report.

## Transcript

**User:** `/deep Should we approve AcmeAI Support Copilot for a HIPAA-adjacent customer support workflow?`

**Organizer:** I infer the target: decide whether a hypothetical vendor is safe enough for a regulated customer-support workflow. Because the stakes are compliance/security, I will recommend a strict contract. One framing question matters before worker spend: is the decision about full PHI processing or only de-identified support tickets?

**User:** Assume de-identified tickets by default, but accidental PHI leakage is possible.

**Organizer:** Framing recorded: de-identified tickets are intended, accidental PHI leakage remains a load-bearing risk.

Before spending, choose the three-axis research contract:

| Preset | Depth | Independence | Strictness | Tradeoff |
|---|---|---|---|---|
| `decision` (Recommended) | deep | cross-family-blind | chase | Cross-family evidence plus blind checks before recommendation. |
| `standard` | medium | two-source | gaps | Too weak for compliance/security approval. |
| `fast` | shallow | single | first | Not appropriate for a regulated workflow. |

**User:** Use `decision`.

**Organizer:** Contract confirmed: `depth=deep | independence=cross-family-blind | strictness=chase`.

Created Research State: `reports/deep_state_20260709_acmeai_hipaa.md`

Initial state snapshot:

```md
# Research State: AcmeAI Support Copilot HIPAA-adjacent workflow
contract: depth=deep | independence=cross-family-blind | strictness=chase | status=running | started=2026-07-09T12:00:00
framing: de-identified support tickets; accidental PHI possible; approval decision for regulated workflow
hypothesis: do not approve until BAA, retention, audit logging, and model-training terms are verified
next action: collect vendor docs, independent security evidence, and blind checks
spend: running total $0.00; ledger=reports/deep_state_acmeai_hipaa.ledger.jsonl
claims: C1 | BAA availability | compliance blocker | unverified | source-of-record
claims: C2 | no training on customer data | data governance blocker | unverified | source-of-record + blind check
claims: C3 | audit logs and retention controls | operational blocker | unverified | docs + independent check
evidence: none yet
open: gaps=BAA, subprocessors, retention, audit logs, breach process; disputes=none
log: 1: initialized state after decision contract
```

## Actions

Batch 1:

- `host-fetch`: vendor security page, DPA, subprocessors page, pricing/enterprise docs.
- `cascade`: broad scout over public claims, counter-evidence, landscape, falsifier.
- `openai --effort high`: independent long report over vendor/compliance posture.

Reason: decision contract needs source-of-record evidence plus cross-family retrieval.

Batch 2:

- `isolated`: `Verify or refute: AcmeAI offers a signed BAA for the support copilot product. What is the primary evidence for and against?`
- `isolated`: `Verify or refute: AcmeAI does not train foundation models on customer support tickets by default. What is the primary evidence for and against?`
- `sonar`: targeted lookup on "AcmeAI audit logs retention controls enterprise support copilot".

Reason: BAA and model-training terms are load-bearing and must be blind-checked.

## Evidence Status

| id | claim | status | sources | independence |
|---|---|---|---|---|
| C1 | A signed BAA is available only on Enterprise plan after legal review. | disputed | vendor docs say "available"; blind check found no public signed template | host fetch + Perplexity |
| C2 | Customer tickets are not used to train foundation models by default. | corroborated | DPA; independent report; blind isolated check | host fetch + OpenAI + Perplexity |
| C3 | Audit logs exist, but retention period and export format are not publicly specified. | single-source | vendor security docs | host fetch |
| C4 | Subprocessor list includes external cloud and model providers. | corroborated | vendor subprocessor page; independent report | host fetch + OpenAI |
| C5 | Accidental PHI exposure remains plausible if de-identification is imperfect. | corroborated | framing risk; compliance analysis; blind check | Organizer judgment + OpenAI + Perplexity |

## Reconciliation

The headline recommendation is blocked by `C1` and `C3`. `C2` is strong enough under the contract. `C1` remains `disputed` because public language says BAA availability, but the evidence does not prove coverage for the exact product and workflow. `C3` is `single-source` and operationally load-bearing.

Updated Research State:

```md
hypothesis: conditional no-go until BAA scope and audit/retention controls are contractually verified
next action: ask vendor for BAA scope, retention/export docs, and audit-log evidence
spend: running total $4.70; ledger=reports/deep_state_acmeai_hipaa.ledger.jsonl
claims: C1 | BAA availability/scope | compliance blocker | disputed | vendor legal confirmation
claims: C2 | no default model training | data governance blocker | corroborated | none
claims: C3 | audit logs retention/export | operational blocker | single-source | vendor admin docs or SOC evidence
claims: C4 | subprocessors listed | procurement blocker | corroborated | none
claims: C5 | accidental PHI risk remains | workflow blocker | corroborated | mitigation design
evidence: E1 | vendor docs | mixed | reports/deep_..._host_fallback.md | host fetch
evidence: E2 | independent long report | corroborated | reports/deep_..._openai.md | OpenAI
evidence: E3 | blind checks | mixed | reports/deep_..._sonar.md | Perplexity
open: gaps=BAA scope, retention/export, audit-log granularity; disputes=C1
log: 2: blind checks downgraded BAA from assumed to disputed
```

## Verification

Verification floor completed:

- `C1` BAA scope: blind isolated check disagreed with the broad interpretation. Marked `disputed`.
- `C2` model-training default: cross-family evidence agreed. Kept `corroborated`.
- `C3` audit logs/retention: only vendor docs found. Kept `single-source`.

## Delivery

Executive answer: do **not** approve AcmeAI Support Copilot yet for a HIPAA-adjacent workflow. It may become approvable after vendor legal/security review, but current public evidence does not clear the `decision` contract.

Research contract: `depth=deep | independence=cross-family-blind | strictness=chase`; framing assumption: tickets are intended to be de-identified, but accidental PHI leakage is possible.

Key findings:

- `C1` BAA availability/scope: `disputed`; must be verified by vendor legal docs.
- `C2` no default model training on tickets: `corroborated`.
- `C3` audit logs/retention/export controls: `single-source`; not enough for approval.
- `C4` subprocessors listed: `corroborated`.
- `C5` accidental PHI risk remains: `corroborated`.

Load-bearing claims:

- If `C1` is resolved with a signed BAA covering this product and workflow, the decision may move from no-go to conditional pilot.
- If `C3` is resolved with adequate retention/export controls, operational risk drops.

Unresolved disputes:

- `C1`: public language says BAA availability, but blind verification did not prove exact product/workflow coverage.

Spend and artifacts:

- Spend: about `$4.70`
- State: `reports/deep_state_20260709_acmeai_hipaa.md`
- Ledger: `reports/deep_state_acmeai_hipaa.ledger.jsonl`
- Reports: `reports/deep_..._openai.md`, `reports/deep_..._cascade.md`, `reports/deep_..._sonar.md`, `reports/host_fallback_acmeai_docs.md`

Recommendation: reject for production approval now; allow only a sandbox pilot with synthetic/de-identified data after receiving BAA scope, retention/export documentation, audit-log evidence, and subprocessor review.

Handoff: next Agent should request vendor legal/security packet and update `C1`/`C3` before re-evaluating. Do not spend more on general web research until those vendor artifacts exist.
