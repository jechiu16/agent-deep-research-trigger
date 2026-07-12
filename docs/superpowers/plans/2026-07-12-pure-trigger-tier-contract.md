# Pure Trigger Tier Contract Plan

**Goal:** Make `/deep` a simple host-native product while retaining mechanical
safety only where the repository controls durable evidence or external spend.

## Constraints

- Implement with tests first; use the repository venv only.
- Preserve external async at-most-once, raw-before-parse, recovery, and hashes.
- Do not add providers, dependencies, commands, or another report format.
- Keep machine and human claims narrower than what the runtime can prove.

## Task 1: Lock the Host Interaction

**Files:** `SKILL.md`, `AGENTS.md`, host discovery wrappers, `HARNESS.md`,
`tests/test_docs.py`.

- Add sentence-level tests for the shared seven-line tier card, one selection,
  phase progress, and absence of hashes/routes/permits in the happy path.
- Rewrite the root skill as the complete default protocol; make the harness
  optional reference material rather than a mandatory read.
- Keep Claude Code and Codex semantics identical; only their control surfaces
  may differ.

## Task 2: Separate Host Captures from External Transactions

**Files:** canonical state/artifact/validation/rendering modules and focused
tests.

- Add the minimal host observation/capture representation needed for Medium and
  High packages without creating host permits, attempts, or quotas.
- Preserve exact bytes, canonical source key, capture fidelity, content hash,
  timestamp, supporting excerpt, and marginal purpose.
- Validate Medium direct-capture linkage and High two-capture diversity.
- Split integrity, tier fulfillment, and human recommendation in JSON and HTML.
- Render a human-first Traditional Chinese first screen for success and
  evidence-insufficient cases; always render Medium/High packages.

## Task 3: Close the Two External-Boundary Blockers

**Files:** `contracts.py`, `state.py`, `quota.py`, `boundary.py`, CLI glue, and
focused tests.

- Bind the normalized question and all user-visible external semantics into one
  hidden authorization digest; remove the independent init question input.
- Replace caller-supplied authoritative fingerprints with a boundary operation
  that builds the actual request, derives its redacted fingerprint, reserves
  exact budget, and journals `attempted` under the session lock before send.
- Cover sync, async submit, and poll paths. Preserve timeout uncertainty,
  at-most-once submission, and raw spooling before parse.
- Add adversarial tests for question substitution, request mismatch, duplicate
  submit, crash recovery, timeout, HTTP error, and parse failure.

## Task 4: Simplify Adoption and Verify

**Files:** `README.md`, `README.zh-TW.md`, `CHANGELOG.md`, release tests.

- Put the four-step single-host happy path before glossary or operator details:
  install, link one host, start a new session, invoke `/deep` and choose a tier.
- State that Low is chat-only, Medium/High produce Traditional Chinese HTML, and
  no provider key is required by default. Move demo, providers, credentials,
  CLI, second-host, and release material later.
- Run focused tests after each task, then the complete release gate from a clean
  worktree. Require dual Sol review and dialogue on the final diff before push.
