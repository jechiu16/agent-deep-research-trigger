# Changelog

All notable changes to this project are documented here. The project follows
Semantic Versioning once the v2 runtime leaves development status.

## 2.0.0b3

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
- The README CLI section lists all 19 `deep-research-state` subcommands.
- `.env.example` drops keys with no consuming code (`OPENAI_API_KEY`,
  `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`) and describes Exa as enabled rather
  than pending benchmark.

### Fixed

- The b2 entry below describing the release gate as "one-command
  no-network" is inaccurate: the gate's dependency-audit step (`pip_audit`)
  requires network access. Left as originally written since changelog
  history is not rewritten; noted here instead.

## [Unreleased]

The current package version is the `2.0.0b2` release candidate. A matching
`v2.0.0-beta.2` tag triggers the gated GitHub prerelease workflow.

### Added

- Standard `pyproject.toml` packaging with installed runtime and doctor CLIs.
- A `gemini` optional dependency that requires the current `google-genai` 2.x API.
- Installed-CLI verification in the Python 3.9, 3.12, and 3.13 CI matrix.
- Distribution build verification, vulnerability auditing, and weekly
  dependency update checks.
- An 80% core branch-coverage floor and one-command no-network release gate.
- Ruff correctness and import-hygiene checks in local and hosted release gates.
- A tag-version-locked GitHub prerelease workflow that uploads verified wheel
  and source distributions.
- GitHub-hosted workflows use the current Node 24 action runtimes.
- Exa enabled as an anti-lock-in and verification route after a bounded paired
  benchmark demonstrated material unique-index gain over Brave.
- Claude Code and Codex project-skill discovery wrappers backed by one
  host-neutral canonical `SKILL.md`.

### Changed

- Rebranded the project from `claude-research-cascade` to
  `agent-deep-research-trigger` to reflect its host-neutral Claude Code,
  OpenAI Codex, and Agent Skills scope.
- Rewrote the English and Traditional Chinese README files around one concise
  install path, explicit compatibility, searchable use cases, and verifiable
  safety guarantees.

### Fixed

- CI now installs declared dependencies before testing `.env` behavior.
- The doctor reports incompatible package versions instead of treating every
  importable Gemini SDK as ready.
- `.env.example` documents the v2 Brave adapter's actual
  `BRAVE_SEARCH_API_KEY` variable.
- Legacy async-worker tests now cover Gemini terminal extraction and pending-job
  ledger clearing without calling a provider.
