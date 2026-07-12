# Beta 5 Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Beta 5 with a concise provider-readiness view, a coherent first-use path, accurate release metadata, and verified global installations without changing machine JSON contracts or spending on provider calls.

**Architecture:** Keep `command_providers()` as the sole producer of the secret-free provider payload. Add one presentation-only formatter used only when the `providers` command omits `--json`; preserve the common JSON printer for every machine path. Documentation and release metadata are updated together and protected by deterministic tests.

**Tech Stack:** Python 3.9+, `argparse`, `unittest`, JSON provider registry, Markdown, GitHub Actions, GitHub CLI.

## Global Constraints

- `providers --json` MUST retain the existing top-level and per-provider data model, compact one-object stdout, and exit codes.
- No credential value, `.env` content, paid request, schema field, dependency, installer, wizard, or credential doctor may be added.
- Default human output MUST omit routes with `contract-test` roles and ids beginning with `test-only-`, but `--json` MUST retain them.
- Readiness states are exactly `ready`, `missing-key`, `disabled`, and `unbound`.
- Accepted bindings are exactly `v2_request_boundary`, `host_native_observed`, `local`, and `no_network_demo`.
- English README MUST remain at or below 260 lines; English and Traditional Chinese claims MUST stay equivalent.
- Package version MUST be `2.0.0b5`; release tag MUST be `v2.0.0-beta.5`.
- A future paired evaluation remains unrun until a separate physical deep-call count is explicitly authorized.

---

### Task 1: Human Provider Readiness View

**Files:**
- Modify: `scripts/research_state.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `command_providers(args) -> tuple[dict[str, Any], int]` and the existing `args.json` flag.
- Produces: `_format_provider_readiness(payload: dict[str, Any]) -> str`, used only for non-JSON `providers` output.

- [ ] **Step 1: Write failing behavior tests**

Add tests that run the installed-style CLI subprocess without `--json` and assert:

```python
result = subprocess.run(
    [sys.executable, str(self.cli), "providers"],
    cwd=self.root,
    text=True,
    capture_output=True,
    env={**os.environ, "EXA_API_KEY": "secret-value", "BRAVE_SEARCH_API_KEY": ""},
)
self.assertEqual(result.returncode, 0, result.stderr)
self.assertIn("ROUTE", result.stdout)
self.assertIn("STATE", result.stdout)
self.assertIn("exa", result.stdout)
self.assertIn("ready", result.stdout)
self.assertIn("brave", result.stdout)
self.assertIn("missing-key", result.stdout)
self.assertIn("BRAVE_SEARCH_API_KEY", result.stdout)
self.assertNotIn("secret-value", result.stdout)
self.assertNotIn("demo-probe", result.stdout)
self.assertNotIn("test-only-unbound-candidate", result.stdout)
self.assertIn("Machine output: providers --json", result.stdout)
```

Add a second test that uses a restrictive overlay to disable an enabled route
and confirms `disabled`, and a direct formatter unit test for an enabled route
with an unsupported binding that confirms `unbound`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_cli.CliTests.test_providers_default_is_human_readiness_table -q
```

Expected: FAIL because stdout is still pretty JSON and has no `ROUTE` header.

- [ ] **Step 3: Implement the minimal formatter**

In `scripts/research_state.py`, add constants and pure helpers:

```python
READY_BINDINGS = frozenset(
    {"v2_request_boundary", "host_native_observed", "local", "no_network_demo"}
)


def _provider_readiness(provider: dict[str, Any]) -> tuple[str, str]:
    missing = [item["name"] for item in provider["required_env"] if not item["present"]]
    if not provider["enabled"]:
        return "disabled", "-"
    if provider["execution_binding"] not in READY_BINDINGS:
        return "unbound", "-"
    if missing:
        return "missing-key", ",".join(missing)
    return "ready", "configured" if provider["required_env"] else "none"
```

Build aligned columns from visible rows, append deterministic counts and the
machine-output hint, and return one newline-terminated string. Do not read the
environment in the formatter; consume only `command_providers()` output.

In `main()`, special-case only the non-JSON `providers` command:

```python
if args.command == "providers" and not args.json:
    print(_format_provider_readiness(payload), end="")
elif args.json:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
else:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_cli -q
```

Expected: all CLI tests pass, including existing `providers --json` shape and secret-redaction cases.

- [ ] **Step 5: Commit Task 1**

```bash
git add scripts/research_state.py tests/test_cli.py
git commit -m "feat(cli): add human provider readiness view"
```

---

### Task 2: First-Use and Release Coherence

**Files:**
- Modify: `tests/test_docs.py`
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `research_harness/__init__.py`
- Modify: `research_harness/provider_registry.json`

**Interfaces:**
- Consumes: Task 1's `providers` human view and existing `/deep` host discovery paths.
- Produces: Beta 5 package metadata and synchronized English/Traditional Chinese adoption instructions.

- [ ] **Step 1: Write failing documentation and metadata tests**

Extend `tests/test_docs.py` with exact assertions:

```python
def test_beta5_release_metadata_is_coherent(self) -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    registry = (ROOT / "research_harness/provider_registry.json").read_text(encoding="utf-8")
    self.assertTrue(changelog.startswith("# Changelog\n"))
    self.assertIn("## 2.0.0b5", changelog.split("## 2.0.0b4", 1)[0])
    self.assertNotIn("current package version is the `2.0.0b2`", changelog)
    self.assertNotIn("not yet enabled pending a live occurrence", registry)


def test_readmes_document_one_real_first_use_path(self) -> None:
    expected_session_copy = {
        "README.md": "start a new Claude Code or Codex session",
        "README.zh-TW.md": "開啟新的 Claude Code 或 Codex session",
    }
    for relative, session_copy in expected_session_copy.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        self.assertIn("deep-research-state providers", text)
        self.assertIn("/deep", text)
        self.assertIn(session_copy, text)
        self.assertNotIn("golden transcript", text.lower())
```

Update the version consistency test to assert `2.0.0b5` explicitly.

- [ ] **Step 2: Run documentation tests and verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_docs -q
```

Expected: FAIL on version `2.0.0b4`, obsolete changelog prose, stale registry note, and golden transcript claims.

- [ ] **Step 3: Update package and registry metadata**

Set both version declarations to `2.0.0b5`. Replace the stale OpenAI storage
note with wording that records enablement after the 2026-07-12 live adoption
occurrence without changing storage rights or any other route policy.

- [ ] **Step 4: Rewrite the first-use path without adding a second workflow**

In both READMEs, keep one clone/install block and make the user journey explicit:

```text
optional demo -> providers readiness -> configure intended keys -> link host(s)
-> start a new host session -> /deep <question> -> inspect/confirm contract
```

Correct the release-gate list to Ruff static checks only. Keep the English
README at or below 260 lines by removing duplicated CLI and install prose rather
than compressing safety guarantees.

- [ ] **Step 5: Replace obsolete changelog state with Beta 5 notes**

Insert `## 2.0.0b5` above `2.0.0b4` with Added/Changed/Fixed entries for:

- human provider readiness view;
- real first-use documentation;
- Traditional Chinese deterministic HTML;
- permit/action-id traversal hardening;
- corrected OpenAI adoption and release-gate metadata.

Remove the stale active `## [Unreleased]` block that describes Beta 2-era
surfaces already removed in Beta 3. Do not rewrite released Beta 3/4 entries.

- [ ] **Step 6: Run focused documentation and registry tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_docs tests.test_cli tests.test_boundary tests.test_contracts -q
```

Expected: all focused tests pass; English README is no more than 260 lines.

- [ ] **Step 7: Commit Task 2**

```bash
git add README.md README.zh-TW.md CHANGELOG.md pyproject.toml \
  research_harness/__init__.py research_harness/provider_registry.json tests/test_docs.py
git commit -m "docs: prepare beta 5 product release"
```

---

### Task 3: Verification, Review, Release, and Global Synchronization

**Files:**
- Verify: all tracked files
- Synchronize after merge: `$HOME/.claude/skills/deep`, `$HOME/.agents/skills/deep`, and `$HOME/.codex/skills/claude-research-cascade`

**Interfaces:**
- Consumes: clean Task 1 and Task 2 commits.
- Produces: merged Beta 5 source, GitHub prerelease artifacts, and verified global installations.

- [ ] **Step 1: Run the complete local release gate**

```bash
.venv/bin/deep-research-release-gate
```

Expected: JSON `{"ok": true, ...}` after 80%+ branch coverage, Ruff, installed CLI demo, build, Twine, and dependency audit all pass from a clean worktree.

- [ ] **Step 2: Exercise the human and machine CLI paths directly**

```bash
.venv/bin/deep-research-state providers
.venv/bin/deep-research-state providers --json > /tmp/beta5-providers.json
.venv/bin/python -m json.tool /tmp/beta5-providers.json >/dev/null
```

Expected: first command is a concise table with no secret values; second is one valid JSON object with the full registry view.

- [ ] **Step 3: Request independent whole-branch review**

Provide the design, plan, base commit, complete diff, and release-gate evidence to a fresh reviewer. Resolve every Critical, Important, and Minor finding through a new TDD cycle, rerun the complete gate after any fix, and require `Ready to merge: Yes`.

- [ ] **Step 4: Push, open PR, and wait for hosted CI**

```bash
git push -u origin codex/beta5-productization
gh pr create --base master --head codex/beta5-productization
gh pr checks --watch
```

Expected: all Python 3.9, 3.12, and 3.13 checks pass before merge.

- [ ] **Step 5: Merge and publish Beta 5**

Merge without force-push, fast-forward the main checkout to merged `master`,
rerun the release gate on the merged commit, then create and push annotated tag
`v2.0.0-beta.5`. Wait for the Release workflow and verify the prerelease has
both `.whl` and `.tar.gz` assets.

- [ ] **Step 6: Synchronize and verify global installations**

Preserve every ignored `.env`. Keep `$HOME/.agents/skills/deep` as a symlink to
the Claude checkout. Rsync merged source into the legacy Codex copy while
excluding `.git`, `.worktrees`, `.venv`, `.env`, caches, build, and dist.

Run the full unit suite from the Claude and legacy Codex venvs. Compare SHA-256
for `SKILL.md`, `HARNESS.md`, `AGENTS.md`, `scripts/research_state.py`,
`research_harness/provider_registry.json`, and their focused tests. Validate all
three skill discovery paths with the official `quick_validate.py`.

- [ ] **Step 7: Clean the feature worktree and report residual external gates**

Remove only the worktree created for this plan and delete its merged local
branch. Report the release URL, merge/tag commit, exact test counts, assets,
global paths, missing Brave credential, exposed-key rotation requirement, and
the still-unrun paid paired evaluation.
