# Changelog

All notable changes to this project are documented here. The project follows
Semantic Versioning once the v2 runtime leaves development status.

## Unreleased

### Added

- An `explore` posture for "what is worth exploring?" questions, accepted by
  `card` and `draft`, and an `EXPLORED` terminal status handled consistently
  by state validation, `validate`, `finalize`, `render`, and `status`. An
  exploration delivers tentative directions (`hypotheses`, with optional
  `basis`, `next_check`, `excluded_reason`, `source_ids`, `artifact_ids`),
  `planned_checks`, and `open_questions`; it needs no load-bearing claim
  set, bounded decision, safe action, acceptance test, or targeted
  re-verification record, and finalize no longer seals their absence as
  `BLOCKED`. An empty package is still delivery-incomplete.
- `pure_trigger_v5` contract semantics. Only a package recorded under it
  knows the explore posture, the `EXPLORED` status, and the hypothesis-shape
  rules; older packages (including `examples/field/`) keep their recorded
  verdict vocabulary unchanged.
- A deterministic exploration first screen (directions, exclusions with
  reasons, unknowns, next check) that never renders a lead as verified and
  omits the engineering-decision blocks; HARNESS.md states the same
  semantics for host-authored reports.
- `examples/explore/01-framework-evolution-directions`: an offline,
  demonstration-only exploration package produced with the new flow.
- `excerpt`: a free, read-only subcommand that locates verbatim text in an
  available raw artifact and returns the exact `excerpt_start`,
  `excerpt_end`, and `excerpt` an evidence record needs. It matches bytes
  as they are (no dash, quote, or whitespace normalization) and refuses a
  missing or ambiguous match instead of guessing; `--nth` picks one of
  several occurrences and `--text-file` carries text the shell cannot.
- `pdf-text`: a free, local subcommand that extracts a captured PDF's text
  layer (pypdf, an optional extra) into a derived `local_output` artifact
  whose provenance names the PDF artifact, its sha256, the extractor
  version, and page byte offsets. `excerpt` and evidence records then work
  on the derived text, and the validator resolves such an artifact's
  source key and upstream to the PDF capture it was derived from (one hop,
  hash-bound). A scanned PDF with no text layer is refused and stays
  provenance only. Several PDFs may share one local action.
- `draft --free-route`: narrows the free probe routes a host-led draft
  enables.
- `transport.min_interval_s` in the provider registry: the request boundary
  sleeps before a sync probe so consecutive requests to one route stay at
  least that far apart (journal timestamps have second precision, so it
  allows one extra second). `scholar` declares 1 s, the Semantic Scholar
  key terms as of 2026-09-10; `S2_API_KEY` remains optional and is only
  ever sent as a header, never journaled.

### Changed

- A host-led draft now enables every ready free probe route (`scholar`,
  `crossref`, `europe-pmc`, `github`, `pypi`, `osv`, `nvd`, `ietf`) at
  `verification`, each with a physical ceiling of 40 calls, so they are in
  the capability snapshot and callable. Before, only `host`, `host-web`, and
  `local` were, and `execute --route scholar` was refused as not enabled.
  The card lists the enabled free routes and says their queries leave to
  those endpoints.
- README, SCENARIOS, and the field-example notes no longer present one
  project's questions as the framework's demo; SCENARIOS adds an
  explore-posture acceptance question and admits a clarifying question
  before the card.
- Five evidence rules from the 2026-09-10 live run (package
  `deep-runs/2026-09-10-evidence-rules`, claims C1-C33) are now one clause
  each in `SKILL.md` and `HARNESS.md`: a search that finds nothing supports
  "not found this round", never "does not exist"; an excerpt match proves
  the words exist, support at the claim's scope is the host's judgment and
  the neighbouring sentences can reverse it; an unread source supports
  nothing beyond its existence and a captured PDF stays provenance until
  extracted or read; a search returning only what you already knew is a
  reason to change angle; next steps serve the confirmed purpose only.
  `HARNESS.md` also says the host sets `summary.status` before `finalize`,
  which only downgrades.
- The per-claim evidence-chain checks are shared (`_validate_claim_chain`):
  a PASS package runs them on every load-bearing claim as before, and an
  EXPLORED package runs them on any claim it marks `load_bearing` or
  `corroborated`, so finishing an exploration confers no verified
  semantics. Hypotheses cannot carry `status`, `load_bearing`,
  `supporting_evidence_ids`, or `claim_type`.
- `explore` contracts draft with `minimum_load_bearing_claims: 0`; every
  other posture keeps its positive floor. An explore run cannot end `PASS`
  or `PARTIAL`, and `EXPLORED` is rejected on any other posture.
- `SKILL.md` now opens with a research-behaviour core (how to pick the next
  step, when to continue, what needs checking, what is not authorized)
  followed by Boundaries and Delivery; the card's Query Brief line asks what
  this round is meant to find out. `HARNESS.md` replaces the fixed
  seven-step Research Loop and the separate Exploration Runs section with
  shared Recording What You Find, Checking What Carries Weight, and status
  sections that describe the current gates as they are. The
  pre-confirmation prohibition, statuses, gates, runtime, and CLI are
  unchanged; `tests/test_docs.py` follows the new sections and no longer
  pins `SKILL.md` to 60 lines.
- A retrieval occurrence now keeps the provider's whole synthesis text and
  every citation. The 4000-character `synthesis_excerpt` cut and the
  40-entry `citations` cut had no stated reason and hid data from the
  host: a 50-citation deep report showed 40 to `citations`. The spool file
  remains the byte-exact original, and provider text still cannot support
  a claim at any length. `synthesis_truncated` stays in the record and is
  always `false`.
- Before confirmation, `SKILL.md` now allows read-only orientation inside
  the session's project and the files the user named -- as far as it takes
  to understand the situation, ask a necessary question, or write the
  brief -- and asks the host to ask the user, before the card, when it is
  confused about what they mean, want, or value instead of filling in a
  reading for them. The prohibition on search, providers, workers, project
  code, and package creation before confirmation is unchanged; what
  orientation read is not evidence and does not widen egress
  (`local_file_egress` stays `false`). The research core's
  re-authorization sentence now says it bounds authorization, not
  questions: a mid-run confusion is settled by asking, with the package
  left `IN_PROGRESS`. `HARNESS.md`, `SCENARIOS.md`, and the README demo
  line follow. Round 3 kept the pre-confirmation prohibition; round 5
  enables in-scope orientation by the user's decision in that round.
- The card names the free routes the host-led draft actually enables
  (`Free（不限次，本合約實際啟用）`, taken from a light draft's
  `stage_permit_map`), because `free: unlimited` is a count and the
  registry lists free routes no draft enables. The card's delivery line
  and the public template now say the host reports progress at key
  points; `SKILL.md` and `HARNESS.md` ask for a short tentative progress
  note at the review points the host already takes, waiting for nothing.

### Fixed

- CLI output redirected to a file or pipe is written as UTF-8 on every
  platform. On a Traditional Chinese Windows locale the JSON payloads
  (`ensure_ascii=False`) were encoded as cp950 unless `PYTHONUTF8` was set,
  which corrupted or crashed on non-ASCII text.

## 2.0.0b10

### Added

- A `windows-latest` matrix leg in CI, alongside the existing Linux/macOS jobs.
- `.gitattributes` pinning raw evidence files and fixture payloads to binary
  checkout, so Git's line-ending translation can no longer corrupt
  hash-pinned bytes on a Windows checkout.
- `rejected_unbilled` permit accounting for gateway refusals a provider never
  billed for (`invalid_request_error`, `insufficient_quota`,
  `authentication_error`): these no longer consume a metered permit.
- An `observations` section for host-synthesized notes that are explicitly
  not byte-backed evidence, kept separate from the canonical claim/evidence
  record so a report can never cite one as if it were.
- `pure_trigger_v4` contract semantics. A package created under it with
  `posture: "decision"` now requires a `coverage_audit` verification record
  at every profile, including Standard; a package on an older semantics
  keeps the prior warning-only behavior, so already-shipped packages
  (including the four `examples/field/` packages) are not retroactively
  invalidated. `init` records the new semantics on every session it creates.

### Changed

- Quality gates that used to key on the retired `low`/`medium`/`high`/`ultra`
  tier vocabulary now key on the live `profile`/`posture` vocabulary the CLI
  actually emits: anti-lock-in and coverage-audit reinforcement bind to the
  Heavy profile, and evidence-diversity requirements bind to Standard/Heavy.
  A previously-passing defective package (a Heavy, decision-posture package
  whose load-bearing claims each rested on a single upstream) now correctly
  fails.
- Report delivery is split into a host-authored track and a deterministic
  fallback track; both are bound to the exact `state_sha256` they were
  generated from.
- Windows evidence writes open in binary mode (`O_BINARY`) so raw artifact
  bytes cannot be silently translated on write.

### Fixed

- A Windows liveness probe (`os.kill(pid, 0)`) fired a real console Ctrl+C
  event on the target process instead of just checking whether it was
  running, since Windows has no signal-free equivalent of POSIX's null
  signal.
- `openai-deep` is marked sunset (its backing models were shut down
  2026-07-23) and is no longer preflight-selectable even with a credential
  present.
- `openalex` no longer lists a required credential it never needed; the
  live API serves anonymous requests, so the route was reporting
  permanently unavailable for anyone without a key they didn't need.

### Removed

- The `low`/`medium`/`high`/`ultra` tier vocabulary and every gate keyed
  on it: the Medium/High "reserved post-result reinforcement" and
  "context-separated verifier capacity" checks, the Ultra bounded
  one-or-two-shot deep submission validator, the tier/durability pairing
  rule, and the host-native Medium/High capture-tier and verifier-
  attestation gates (`tier.capture_missing`, `tier.medium_direct_capture_
  missing`, `tier.high_capture_diversity`, `tier.high_verifier_*`,
  `tier.ultra_deep_*`). The CLI has emitted only `tier: "custom"` since
  2.0.0b9, so this machinery was unreachable through any public path;
  `profile`/`posture` gates added in b9 are its live replacement. The
  `tier.`-prefixed names still in use (`tier.anti_lock_in_missing`,
  `tier.coverage_audit_missing`, `tier.targeted_reverification_missing`,
  `tier.human_status_missing`, the `tier_contract_met` field) are kept
  unchanged: they are a public, versioned diagnostic surface, and the
  prefix no longer implies the retired tier enum.

## 2.0.0b9

### Added

- User-controlled Light, Standard, and Heavy call-count profiles over `deep`,
  `search`, and unlimited `free` cost classes. Provider choice remains in the
  registry and Deep candidates are price-ranked.
- A host-led contract draft path, targeted re-verification records, and
  budget-exhaustion annotations that stop further external calls without
  withholding the existing package.
- Four retained Parallax field packages: three Light runs plus one Standard
  end-to-end run with a real Deep call, targeted Search, direct captures, and
  a recorded decision delta.

### Changed

- The host is explicitly the sole conclusion author. D1/D2 reports are
  discovery-only and buy breadth or structure, never claim authority.
- The public skill and harness are shorter; delivery is canonical JSON plus a
  deterministic Traditional Chinese HTML report, without a second full
  Markdown report.
- HTML verification now renders each checked claim's accepted, corrected, or
  unverified disposition instead of hiding that decision in canonical JSON.
- The first interaction is one Query Brief confirmation card with the exact
  budget vectors and ready provider candidates.

### Fixed

- Cost enforcement now counts actual event classes and records a single
  machine-readable gap when a `deep` or `search` limit is exhausted.
- Bound host-led contracts can persist exact host WebSearch/fetch bytes through
  `host-capture`; unrelated external-managed contracts remain rejected.
- CLI test isolation no longer depends on a side-effect import alias.

## 2.0.0b8

### Fixed

- Restored the documented Python 3.9 test compatibility by avoiding a
  Python 3.10-only `zip` argument in the Ultra fixture helper.

## 2.0.0b7

### Added

- Ultra is a fourth tier: High plus at most two sequential Deep submits, with
  exact D1 and optional D2 routes authorized upfront. The Organizer may stop or
  run D2 for a material gap or expansion before one final verifier.
- A validated Gemini Interactions Deep Research adapter, with preview,
  estimated-cost, remote-retention, and no-ZDR disclosure plus a discovery-only
  evidence boundary.
- Three live adoption observations and an RFC 9110 blind output-level
  comparison. These observations are explicitly non-ranking and do not establish
  general superiority.

### Changed

- Full provider reports are consumed with relevant session context and preserved
  through canonical occurrence pointers. Claims still require direct capture,
  while `zh-Hant-TW` HTML remains concise.

### Fixed

- Ultra integrity handling, verifier association, contract mapping truth, and
  fixture chronology false-pass issues.

## 2.0.0b6

### Changed

- The first `/deep` response is a seven-line, tool-free trigger card; Low stays
  runtime-free, while Medium and High use the repo-local `host-capture` bridge
  only after tier selection.
- The public READMEs now present a compact four-step product path: clone the
  `v2.0.0b6` tag, prepare the runtime, link one host, and invoke `/deep`.
- Medium/High delivery is documented as `init -> host-capture -> patch as
  needed -> validate -> render`. Evidence shortfall uses human reason `證據不足`
  and HTML label `EVIDENCE_INSUFFICIENT`; terminal or handoff incompleteness uses
  human reason `交付不完整` and HTML label `DELIVERY_INCOMPLETE`.
- Medium/High terminal and handoff gates now explicitly cover both execution
  modes. High verifier guidance binds the canonical claim packet and separates
  host-only records from external-managed organizer-pass accounting.

## 2.0.0b5

### Added

- A deterministic human readiness table for `deep-research-state providers`
  that hides contract-test and test-only routes while keeping `providers --json`
  machine-compatible.
- A progressive-disclosure first-use path in the English and Traditional Chinese
  READMEs: install, link one host, start a fresh session, then type `/deep` and
  choose Low, Medium, or High. It makes host-native use and no provider key the
  default, and documents the chat-only Low result plus Medium/High package
  delivery.

### Changed

- The pure `/deep` trigger now offers one `Low`/`Medium`/`High` choice; Medium
  and High deliver canonical JSON plus a `zh-Hant-TW` package, including
  `blocked` and `evidence-insufficient` outcomes.
- Authorization is question-bound; the boundary owns actual-request
  construction and atomic reservation, v3 occurrence lineage, and legacy-marker
  compatibility.
- Async no-token and terminal-poll recovery now preserves at-most-once
  semantics and forbids resubmission.
- Traditional Chinese deterministic HTML report chrome now preserves the
  `zh-Hant-TW` presentation contract.
- The public trigger/adoption guidance now keeps optional providers, credentials,
  CLI checks, and a second host after the four-step happy path.
- Permit/action-id traversal hardening now validates request identity and refuses
  redirects that could create an unapproved physical request.

### Fixed

- The OpenAI Deep Research storage note now records enablement after the
  2026-07-12 live adoption occurrence.
- Release metadata now aligns the package version and release-gate documentation
  for Beta 5, including Ruff static checks without obsolete golden-transcript
  validation.

## 2.0.0b4

### Added

- A `promote` CLI subcommand and `promote_provider_payload` artifact
  pipeline that turns a completed provider retrieval occurrence's
  boundary-spooled payload into an indexed, provenance-bound artifact,
  without ever letting a caller name an arbitrary filesystem path for
  provider bytes.
- A `citations` CLI subcommand: a free, read-only harvest of every citation
  recorded on retrieval occurrences (optionally scoped to one action),
  deduplicated by url and flagged `directly_verified` against `sources`
  with a matching directly fetched url. Verification-stage sampling reads
  this list to choose which citation to fetch directly next.
- `scripts/calibration_report.py`, a pure offline reader that turns
  finished session directories and an optional human-authored annotations
  file into a PASS-correctness/verification-yield/cost report, plus a
  small seed question-and-annotation set under `examples/eval/` for
  running it.
- An `openai-deep` adapter (OpenAI Deep Research, `o4-mini-deep-research`,
  Responses API background mode): landed fixtures-first, then enabled the
  same day after one live adoption occurrence (RFC 9110 lookup, terminal
  success on the second poll, 4 citations, ~30k tokens) satisfied the same
  gate perplexity crossed. The deep line now has two independent vendors.

### Changed

- `synthesis` posture now shares the Medium/High coverage-audit gate with
  `scientific`/`decision`: its posture promise is itself a coverage/
  omissions declaration, so a `synthesis` PASS at those tiers requires a
  completed, dispositioned coverage-audit verification record. It still
  has no anti-lock-in requirement of its own.
- `HARNESS.md`'s anti-lock-in reinforcement step now states explicitly
  that every finding must be dispositioned (refuted, absorbed into a
  revised candidate, or recorded as an open tension with a revisit
  trigger) -- noting counter-evidence without resolving it does not
  satisfy the step.
- The README CLI section lists all 22 `deep-research-state` subcommands.

### Fixed

- `promote_provider_payload` now refuses providers whose
  `action_categories` include `"deep"`: an async deep job's result is
  spooled under `provider_spool/<poll_action_id>.raw.json`, not under the
  submitted action_id recorded on the retrieval occurrence, so promoting
  by that action_id would have ingested the submit-accept stub instead of
  the actual result.
- `scripts/calibration_report.py`'s cost extraction now also reads exa's
  `costDollars.total` and openalex's `meta.cost_usd` raw shapes; it
  previously only summed the perplexity_deep/sonar `usage.cost.total_cost`
  shape and silently undercounted sessions that used the other two
  providers.
- Validation's `provider_payload` evidence-lineage branch
  (`artifact.provenance` / `evidence.provider_claims_forbidden` /
  `artifact.storage_rights`) is reachable through the public CLI for the
  first time since 0785603: before the `promote` subcommand existed, no
  public path could create a `provider_payload`-origin artifact, so that
  branch was exercised only by hand-built test fixtures.

## 2.0.0b3

### Added

- An `attempt` CLI subcommand that journals attempt-status transitions
  (`attempted`/`accepted`/`failed`/`uncertain`/`completed`) for actions no
  request boundary executes — host, local, and organizer-pass actions.
  Illegal transitions are rejected by the existing quota transition table.

### Removed

- The legacy worker CLI (`scripts/deep_research.py`, `WORKERS.md`) and its
  `gemini` optional dependency.
- The credential doctor (`scripts/doctor.py`, `deep-research-doctor`).
- The pre-v2 state validator (`scripts/validate_state.py`).
- Golden transcript validation (`scripts/validate_transcripts.py`,
  `examples/transcripts/`) and the legacy-worker quickstart samples
  (`examples/quickstart/`).
- Seven unbound registry candidates with no adapter binding: `cascade`,
  `openai`, `gemini`, `deepseek`, `mojeek`, `jina`, `firecrawl`.
- Unused harness code: the `ingest_provider_artifact` ingestion path, the
  session-locked `record_attempt_status` wrapper, the `render_session` thin
  wrapper, the unreachable `"interrupted"` attempt status, and the dead
  `evidence_capabilities.requires_direct_fetch` registry field.

### Changed

- Documentation (`SKILL.md`, `HARNESS.md`, `AGENTS.md`, `SCENARIOS.md`, both
  READMEs) now states the resolved provider registry as the sole source of
  truth for route readiness, replacing references to the credential doctor
  and the legacy worker CLI.
- The README CLI section lists all 20 `deep-research-state` subcommands.
- `.env.example` drops keys with no consuming code (`OPENAI_API_KEY`,
  `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`) and describes Exa as enabled rather
  than pending benchmark.

### Fixed

- High-tier `PASS` was unreachable through the CLI surface: validation
  requires the context-separated verifier's organizer-pass action to reach
  attempt status `completed`, but no command could journal attempt status
  for such actions (only boundary-executed routes journal their own). The
  new `attempt` subcommand closes the gap; `HARNESS.md` documents the step.
- The redaction-review and fetched-source ingestion errors now name the
  exact CLI flags and patch step that satisfy them.
- `attempt` refuses boundary-managed categories (probe/deep/processor/
  transport): journaling "attempted" on such a permit would permanently
  void it, since the boundary refuses already-attempted actions.
- Validation now independently re-derives every action's attempt lifecycle
  (`attempt.unknown_action`/`attempt.from_status`/`attempt.transition`)
  instead of trusting writer-side enforcement of the transition table.
- The b2 entry below describing the release gate as "one-command
  no-network" is inaccurate: the gate's dependency-audit step (`pip_audit`)
  requires network access. Left as originally written since changelog
  history is not rewritten; noted here instead.
