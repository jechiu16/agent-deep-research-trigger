# Beta 5 Productization Design

Date: 2026-07-12
Status: approved

## Purpose

Make Agent Deep Research Trigger pleasant to adopt without weakening its
machine-enforced research boundaries. Beta 5 closes the gap between a strong
runtime and a coherent first-use experience: a human can see which routes are
usable, install the skill for either host, invoke `/deep`, understand the
confirmation boundary, and verify a release without reading internal JSON.

The release remains a beta. It does not claim that the harness outperforms a
host's built-in Deep Research until a separately authorized paired evaluation
produces that evidence.

## Current Problems

1. `deep-research-state providers` prints the entire registry-shaped payload
   even without `--json`. It is correct but not useful as a human readiness
   check.
2. The README quickstart proves only the no-network demo. It does not carry a
   new user through discovery, route readiness, host restart, and the first
   `/deep` contract card.
3. User-facing documentation says the release gate runs golden transcript
   validation even though that legacy surface was removed.
4. `CHANGELOG.md` contains an obsolete Unreleased section below released
   versions and describes a retired release candidate.
5. The OpenAI Deep Research registry record is enabled and validated, but its
   storage-rights note still says adoption is pending.
6. `master` contains security hardening and the Traditional Chinese report
   work after `v2.0.0-beta.4`, but no matching package or GitHub release.

## Product Boundary

### Human readiness view

`deep-research-state providers` becomes a deterministic text view intended for
people. It prints one row per non-test route with these columns:

- `ROUTE`: provider id;
- `STATE`: `ready`, `missing-key`, `disabled`, or `unbound`;
- `AUTH`: `none`, `configured`, or the comma-separated missing environment
  variable names;
- `ROLES`: comma-separated registry roles.

Rows follow registry order. Routes whose roles contain `contract-test`, and
routes whose ids begin with `test-only-`, are omitted from the default view and
counted in a final hidden-test-routes note. The final lines summarize ready,
missing-key, disabled, and hidden counts and point machine consumers to
`providers --json`.

Readiness is presentation derived from the resolved registry and environment:

- `disabled` when `enabled` is false;
- `unbound` when an enabled route's execution binding is not one of
  `v2_request_boundary`, `host_native_observed`, `local`, or
  `no_network_demo`; registry validation already rejects enabled routes whose
  lifecycle is not active;
- `missing-key` when the route is enabled and bound but any `required_env`
  value is absent;
- `ready` only when all three checks pass.

The view never prints a credential value. Optional credentials such as
`S2_API_KEY` remain adapter concerns and do not become required readiness
conditions.

### Machine compatibility

`deep-research-state providers --json` remains byte-contract compatible at the
JSON data-model level: the same top-level keys, provider fields, secret-free
`required_env` booleans, sorting, compact single-object output, and exit codes.
No registry schema or canonical session schema changes.

All other subcommands retain their current default pretty-JSON and `--json`
behavior. Beta 5 does not generalize a text formatter across the 22-command
surface.

### First-use documentation

Both READMEs use one user journey:

1. clone and create the project virtual environment;
2. run the no-network demo as an optional health check;
3. run `providers` and configure only intended credentials;
4. link the same checkout into Claude Code and/or Codex discovery;
5. restart or begin a new host session;
6. invoke `/deep <question>`;
7. inspect and explicitly confirm the exact contract card before spend.

The English README remains at or below 260 lines. English and Traditional
Chinese claims stay equivalent. The development section lists only checks the
release gate actually runs.

### Release coherence

The package and runtime version become `2.0.0b5`. `CHANGELOG.md` starts with a
`2.0.0b5` entry describing the human readiness view, first-use documentation,
Traditional Chinese HTML, security hardening, and metadata corrections. It
does not preserve an inaccurate active Unreleased section.

The OpenAI Deep Research storage note records that the route was enabled after
the 2026-07-12 live adoption occurrence. Updating the registry changes its
hash by design; contracts prepared against the old record must be prepared and
confirmed again.

## Non-Goals

- No paid provider request or paired quality evaluation.
- No claim of superiority over built-in Deep Research.
- No installer, setup wizard, credential doctor, or second orchestration path.
- No new provider, route, dependency, schema field, or canonical report form.
- No automatic credential rotation or modification of ignored `.env` files.
- No screenshot, hosted demo, or generated report committed to the repository.

## Error Handling

Registry load or overlay failures continue through the existing CLI error
contract. In human mode they produce the existing stderr error and non-zero
exit. In `--json` mode they also produce the existing single JSON error
envelope. The text formatter receives only a validated command payload and
does not catch or reinterpret registry errors.

Terminal layout uses fixed minimum widths derived from visible values, not the
current terminal width. Long role or environment lists remain on one line so
redirected output is deterministic and testable.

## Verification

Automated evidence must prove:

1. default `providers` output is a stable table, excludes internal test routes,
   distinguishes ready and missing-key routes, and contains no secret values;
2. `providers --json` retains the existing shape and compact one-object output;
3. version declarations agree and the changelog starts with Beta 5;
4. both READMEs encode the same first-use path and no longer mention golden
   transcript validation;
5. the OpenAI registry record no longer contradicts its enabled status;
6. the full unit suite, branch coverage floor, Ruff, installed CLI demo,
   distribution build, Twine metadata, and dependency audit pass;
7. an independent whole-branch review reports no unresolved issue;
8. GitHub CI passes on Python 3.9, 3.12, and 3.13;
9. tag `v2.0.0-beta.5` produces a GitHub prerelease whose wheel and source
   archive pass metadata checks;
10. Claude Code and the legacy Codex installation each pass the full unit
    suite and have identical checksums for the skill contract, harness,
    renderer, CLI, and related tests; official Codex discovery resolves to the
    Claude Code checkout symlink.

## External Follow-Up

Keys previously pasted into conversation are treated as exposed and must be
rotated in their provider dashboards. Brave remains an optional missing
credential on the current machine; host-native search and other confirmed
routes keep the skill usable. A future paired evaluation requires a new,
explicit physical deep-call count before any request is sent.
