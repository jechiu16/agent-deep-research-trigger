# Async Deep-Engine Boundary (DRAFT — implement after adapter wave 2 lands)

Deep research engines (perplexity sonar-deep-research, openai deep-research,
gemini deep research) are asynchronous: submit, poll for minutes, harvest.
This spec extends the v2 request boundary to async routes without weakening
any invariant the sync path enforces.

## Non-negotiable inheritances

- One permit, one physical request: the submission consumes the `deep`
  permit; every poll consumes a `transport` permit. Nothing refunds.
- The provider job token is journaled at acceptance time in the event
  journal (`attempt_status` details) — a killed session never loses a paid
  submission. This is the v1 ledger-at-submission lesson, upgraded: the
  journal is hash-chained.
- Raw terminal payloads are spooled before extraction; extraction failure
  leaves the job harvestable at zero marginal cost.
- Submissions are NEVER auto-resubmitted. Timeout or crash → `uncertain`,
  and recovery goes through resume, not re-pay (v2 decisions ledger).

## Lifecycle

```
acquire(deep)      permit_acquired            (deep permit consumed)
submit             attempted -> accepted      details: {job: "provider:id"}
poll xN            transport permits, backoff 15s -> 30s -> 60s -> 120s cap
terminal:
  completed        occurrence written by code; raw payload spooled;
                   optional ingest_provider_artifact under storage rights
  failed           provider-terminal state; permit stays consumed
  uncertain        wall-time exhausted or poll transport died;
                   job token remains harvestable via resume
```

Poll accounting is honest: every poll GET is a physical transport request.
A 20-minute engine at the backoff schedule costs ~14 transport requests;
contract templates for deep tiers budget `transport` ceilings accordingly
(rule of thumb: 20 transport per reserved deep invocation).

## Adapter protocol extension

Sync adapters export `build/parse`. Async adapters export:

- `submit(query, env) -> RequestSpec` — the paid POST; never retried.
- `job_token(payload) -> str` — extract "provider:id" from the accept body.
- `poll(token, env) -> RequestSpec` — one status GET.
- `extract(payload) -> ParsedResult | None` — None means still running;
  raises AdapterParseError on terminal-but-malformed (payload already
  spooled by the boundary before extract is called).

The registry drives dispatch: `transport.mode: "async"` routes require the
async quadruple; `"sync"` routes require the pair. `_bound_route` refuses
mismatches.

## Resume

- `research_state.py deep-pending <session>`: scan the event journal for
  accepted-without-terminal deep actions; print job tokens. Free.
- `research_state.py deep-resume <session> --action-id A` — continue polling
  under NEW transport permits (acquired normally), same attempt chain
  (`uncertain -> accepted` is added to the attempt transition table for
  resumed jobs; the transition is journaled with the resume reason).

## Deliberately out of scope

- Provider-side cancellation (money is already spent; harvesting beats
  cancelling).
- Streaming partials (deep engines do not stream usefully today).
- Any cross-session learning (user verdict: closed).

## Acceptance

- Fixture-replay tests for submit/poll/extract per async adapter, including
  terminal-failure, still-running, malformed-terminal, and wall-timeout →
  uncertain → resume → completed.
- One live perplexity deep run (~$0.5, needs explicit budget nod) as the
  first async adoption evidence; openai/gemini follow the same pattern.
