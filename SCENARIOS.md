# Agent Deep Research Trigger — Scenario Calibration

Use these scenarios to evaluate `/deep` behavior. They are posture and tier
calibrations, not fixed provider pipelines. Host-native search/fetch and local
inspection are the default; provider keys are optional.

## Expected decisions

| Scenario | Posture | Typical tier | Required behavior |
|---|---|---|---|
| `/deep What license does this repo use?` | `lookup` | `low` | Prefer the local source of record; do not broaden the question |
| `/deep Summarize the literature on RAG hallucination` | `synthesis` | `medium` | Use scholarly discovery, separate paper claims from model summaries, audit coverage |
| `/deep Which mechanism explains this regression?` | `scientific` | `medium` or `high` | Preserve competing hypotheses and seek a discriminating observation |
| `/deep Should we approve this vendor for healthcare support?` | `decision` | `high` | Verify load-bearing premises across source families and use context-separated verification |
| `/deep` after a long conversation | inferred | inferred | Infer the likely target; ask only when ambiguity would change the contract |
| Missing provider keys | unchanged | unchanged | Continue with host-native/local work when sufficient; otherwise explain the unavailable evidence and offer a substitution |
| Local files plus web context | task-dependent | task-dependent | Obtain explicit external-egress authority before sending local content |
| Conflicting sources | unchanged | unchanged | Mark the claim disputed and spend only if the dispute is load-bearing |
| Host crash during async research | unchanged | unchanged | If an accepted or uncertain job has a provider token, resume it with a new poll action. A recovered attempted job without a token is consumed, non-pollable, requires manual inspection, and must never be resubmitted |

## Required interaction shape

Every scenario follows the same public interaction shape:

1. The literal `/deep` trigger identifies the research target.
2. The Organizer recommends a tier with one reason and waits for exactly one
   `Low`, `Medium`, or `High` choice.
3. Host-native and local actions are preferred; Medium adapts to the named gap,
   while High obtains multiple direct sources.
4. Paid requests reserve their exact physical multiplicity atomically inside the
   request boundary. The legacy `permit` command is only for host, local, and
   Organizer actions.
5. Semantic truth lives only in canonical `state.json`; events and raw bytes
   retain their own operational roles.
6. `validate` must pass before `render` can deliver a `PASS` report.

## Evaluation prompts

```text
/deep Compare SQLite and DuckDB as the default local analytics engine for a
Python desktop application.
```

Pass condition: recommends a decision-appropriate bounded tier, checks
local applicability, separates evidence from inference, and names a flip
condition.

```text
/deep What does the literature say about whether retrieval-augmented generation
reduces hallucinations in question-answering systems?
```

Pass condition: uses a synthesis posture, distinguishes discovery metadata from
direct evidence, audits source concentration, and keeps unresolved disputes.

```text
/deep Is this AI vendor safe enough for a HIPAA-adjacent support workflow?
```

Pass condition: recommends a high decision tier, verifies compliance and data
handling claims against source-of-record material, and requires a
context-separated verifier before `PASS`.

## Anti-patterns

- Triggering on ordinary research language when the user did not type `/deep`.
- Starting research before the user chooses one tier.
- Treating a present credential as execution readiness.
- Treating a credential or provider route as required when host-native work is
  sufficient.
- Treating a failed or uncertain paid request as refundable.
- Resubmitting an accepted async job instead of resuming its provider token.
- Treating model agreement or shared aggregators as source independence.
- Letting the Organizer write retrieval occurrences as prose.
- Maintaining a second full Markdown state beside canonical `state.json`.
- Delivering `PASS` when validation is false or lineage is incomplete.
