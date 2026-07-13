# Contributing

Contributions are welcome when they preserve the runtime's mechanical
guarantees, host neutrality, and the simple `/deep` first-use path.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/deep-research-release-gate
```

## Pull requests

- Keep the root `SKILL.md` host-neutral. Claude Code and Codex wrappers may map
  discovery or native tools, but must not fork the protocol.
- Keep host-native search/fetch and local inspection as the default. Provider
  credentials are optional and must not become a first-use requirement.
- Add fixture-first tests for provider adapters. A credential is not adoption
  evidence, and a provider stays disabled until its request boundary and policy
  gates pass.
- Never commit credentials, unrestricted provider payloads, or user material.
- Preserve atomic reservation of paid request multiplicity inside the request
  boundary, no automatic paid resubmission, spool-before-parse, canonical state,
  and fail-closed validation. The legacy `permit` command is only for host,
  local, and Organizer actions.
- Update English and Traditional Chinese user-facing documentation together.
- Run the complete release gate from a clean worktree before requesting review.

Provider adoption or live benchmarks must use the runtime boundary and record
their exact request-count and cost disclosure in the run evidence.
