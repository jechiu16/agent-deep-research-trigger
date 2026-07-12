# Pure Trigger Tier Contract

Date: 2026-07-12
Status: approved

## Product

`/deep` is one research trigger, not a visible orchestration platform. Every
invocation first shows Low, Medium, and High; choosing a tier is the run's only
confirmation.

| Tier | Research rule | Delivery |
|---|---|---|
| Low | Shortest credible host-native path | Traditional Chinese chat and links; no package by default |
| Medium | Add a source only to resolve a named gap, conflict, or decision risk | Canonical JSON and Traditional Chinese HTML |
| High | Directly capture at least two different sources and check shared upstreams | Canonical JSON and Traditional Chinese HTML |

Host-native search, fetch, browser, local tools, model reasoning, and subagents
are the default. The runtime must not claim to count or enforce those actions.
External paid requests and local-data egress are optional semantic changes and
must be disclosed with exact enforceable counts before the tier is selected.
Unapproved changes require a new run, not a second confirmation inside the run.

## Human Contract

The first response is at most seven lines: normalized question, recommendation
with one reason, one line per tier, exact extra paid-request count, local-data
egress, and the three start choices plus Adjust. It contains no hash, route,
permit, CLI, schema, or posture terminology.

Progress is phase-only. Medium and High end with one bounded conclusion, a
human status, and an HTML link. The HTML first screen presents recommendation,
bounded conclusion, linked reasons, limitations or flip conditions, and one
reversible next step. Kernel diagnostics are collapsed at the end.

## Evidence Contract

Medium load-bearing claims require a directly captured source. Search listings,
snippets, model synthesis, and unfetched citations are discovery aids only.
Each added source records its marginal purpose.

High requires at least two qualifying captures linked to the load-bearing claim
set. A qualifying capture has a distinct canonical source key and content hash,
an immutable artifact, and an exact supporting excerpt. Shared upstreams are
disclosed. The machine proves capture diversity and lineage, not independence,
entailment, truth, or agreement. If the floor is not met, the package is still
rendered but the human status is `evidence insufficient`.

`integrity_ok`, `tier_contract_met`, and the Organizer's recommendation are
separate axes. None may impersonate the others.

## Runtime Boundary

Use two orthogonal axes:

- `execution`: `host_native` or `external_managed`;
- `durability`: `chat_only` or `canonical_package`.

Low defaults to `host_native + chat_only`; Medium and High use
`host_native + canonical_package`. Host actions create observations or captures,
never permits, attempts, or physical-request quota claims. Captures identify
whether bytes are remote raw HTTP or host-rendered output.

The transaction kernel exists only for requests the repository actually sends.
It keeps at-most-once async submission, timeout-as-consumed uncertainty, raw
spooling before parse, crash recovery, integrity hashes, and lineage.

## Release Blockers

1. Authorization must bind the normalized question, tier, durability, external
   route/count snapshot, egress, and retention in one hidden digest. Session
   initialization cannot accept a different question.
2. The boundary must derive the credential-redacted fingerprint from the actual
   `RequestSpec` and atomically reserve budget plus journal `attempted` before
   transport. The caller cannot mint an authoritative fingerprint separately.

## Non-Goals

- No new provider, installer, defense layer, or paired paid evaluation.
- No claim that different captures are independent or that `/deep` is superior
  to built-in Deep Research without a separately authorized evaluation.
- No adapter-portfolio, 22-command, or full state-schema rewrite in this wave.
- No second full Markdown report and no Low durable opt-in in this wave.

## Acceptance

Both Claude Code and Codex expose the same tier card, progress language,
evidence floors, package contract, and report semantics. Low creates no package.
Medium and High always create canonical JSON plus `zh-Hant-TW` HTML, including
partial or blocked results. Host-native runs contain zero host permits or
attempts. Question swap and permit/request mismatch regression tests fail
closed. The complete release gate remains green.
