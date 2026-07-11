# Changelog

All notable changes to this project are documented here. The project follows
Semantic Versioning once the v2 runtime leaves development status.

## [Unreleased]

### Added

- Standard `pyproject.toml` packaging with installed runtime and doctor CLIs.
- A `gemini` optional dependency that requires the current `google-genai` 2.x API.
- Installed-CLI verification in the Python 3.9, 3.12, and 3.13 CI matrix.
- Distribution build verification, vulnerability auditing, and weekly
  dependency update checks.
- An 80% core branch-coverage floor and one-command no-network release gate.

### Fixed

- CI now installs declared dependencies before testing `.env` behavior.
- The doctor reports incompatible package versions instead of treating every
  importable Gemini SDK as ready.
- `.env.example` documents the v2 Brave adapter's actual
  `BRAVE_SEARCH_API_KEY` variable.
- Legacy async-worker tests now cover Gemini terminal extraction and pending-job
  ledger clearing without calling a provider.
