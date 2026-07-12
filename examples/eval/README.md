# Calibration eval (internal use only)

This is a small, internal-only eval for asking one question: **when this
machine's `/deep` harness reports `PASS`, how often is that actually
correct?** It is not a benchmark, not a leaderboard, and it is not meant to
be published or compared across machines/providers. It exists to catch
drift in one installation's own judgment over time.

`scripts/calibration_report.py` (see the repo root `scripts/`) is a pure,
offline reader: it never calls a network or an LLM. It reads finished
session directories and an optional human-authored annotations file, and
reports status accuracy, a verification-yield proxy, and provider cost. It
does not run the eval for you and it does not grade anything itself — a
human has to do that part, on purpose (see "Why a human grades this" below).

## Files

- `questions.jsonl` — 5 seed questions, one JSON object per line:
  `{"id", "question", "expected_key_facts": [...], "posture_hint"}`.
  `expected_key_facts` is a checklist for the human annotator, not a
  pre-baked answer string — some of these questions (package versions,
  in particular) have answers that change over time by design; the point is
  to check whether the harness fetched the *current* truth instead of
  reciting a stale one from parametric memory.
- `annotations.example.jsonl` — the annotation format, filled in with
  illustrative (not real) verdicts, one JSON object per line:
  `{"session_dir", "question_id", "ground_truth_verdict", "notes"}`, where
  `ground_truth_verdict` is one of `"correct"`, `"incorrect"`, `"partial"`.

## How to run the eval

1. For each row in `questions.jsonl`, start one fresh `/deep` session with
   that `question` (use `posture_hint` as the contract's `posture`; pick
   whatever tier is standard for how you'd normally run this). Let it reach
   a terminal `summary.status`.
2. Note the resulting session directory for each question.
3. Read each session's final answer/decision and compare it, by hand,
   against that question's `expected_key_facts`. Record one line per
   session in your own `annotations.jsonl`, following
   `annotations.example.jsonl`'s shape. Be honest about `partial` —
   don't round a half-right answer up to `correct`.
4. Run the report:

   ```bash
   .venv/bin/python scripts/calibration_report.py /path/to/your/sessions-root \
     --annotations /path/to/your/annotations.jsonl
   ```

   Add `--json` for machine-readable output.

## Why a human grades this

Nothing in this repo scores `expected_key_facts` against a session's answer
automatically. Auto-grading a lookup/synthesis answer against a checklist is
itself an unverified judgment call — building that would just move the
"can we trust this verdict?" question one level down instead of answering
it. A human comparing a handful of session outputs against five checklists
is cheap enough that it isn't worth automating away, and it keeps the
ground truth honest.

## Goodhart warning — read this before reusing the question set

These 5 questions are seeds, not a fixed benchmark. Once you've run and
annotated a question, treat it as spent: don't iterate the harness against
the same question repeatedly and don't hand-tune prompts/providers to make
these specific 5 pass. If you do, this stops measuring calibration and
starts measuring overfitting to five checklists, which defeats the purpose.
Rotate in fresh questions (same shape: an objectively checkable fact, a
posture of `lookup` or `synthesis`) for each new calibration round, and keep
old rounds around only as a historical record of drift, not as a target to
re-optimize against.
