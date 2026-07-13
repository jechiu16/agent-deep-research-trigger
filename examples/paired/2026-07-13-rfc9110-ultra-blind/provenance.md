# Provenance and resource context

## Live question

The three provider adoption runs used the frozen question in `task.md`. They
were independent live submissions used to understand integration behavior, not
three calls in one production Ultra session and not a provider ranking.

| Provider | Wall time | Report characters | Citations | Provider-reported usage/cost |
|---|---:|---:|---:|---|
| OpenAI Deep Research | 231 s | 2,139 | 10 direct IETF/RFC Editor links | 64,058 total tokens; no dollar field |
| Perplexity Deep Research | 230 s | 45,771 | 18 | 9,773 total tokens; $0.38324 |
| Gemini Deep Research preview | 356 s | 8,836 | 8 wrapper URLs | 1,094,159 total tokens; no dollar field |

Each session passed the existing async occurrence/integrity checks, and the
stored session files were scanned for the three provider keys with no match.
These are single observations and must not be treated as general quality or
cost rankings.

## Paired arms

- Candidate A preserves the OpenAI live report text.
- Candidate B uses that report as an untrusted research memo, checks the
  status/scope against the official IETF Datatracker and RFC Editor records,
  removes the unsupported successor inference, and adds a bounded recheck
  condition. It made no additional paid provider call.

This paired suite evaluates the human-readable answer only. It does not by
itself prove the full canonical JSON/HTML runtime, async recovery, or renderer;
those remain covered by the repository tests and release gates.
