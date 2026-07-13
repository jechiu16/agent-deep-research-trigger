# Agent Deep Research Trigger — Codex Binding

Use this thin binding only when the user explicitly invokes `/deep`. The
complete shared protocol, tier semantics, card, progress language, and
delivery contract live in the canonical [SKILL.md](SKILL.md), which is the
sole protocol source for both Claude Code and Codex.

Codex supplies the conversation surface for the canonical protocol. Do not
copy or redefine its tier or posture semantics here. The public choices are
Low, Medium, High, and Ultra; Ultra is High plus a first Deep Research pass,
with one choice authorizing at most two submits; after the High checkpoint the
Organizer may stop or use D2 for a material next question. Use the canonical
skill for confirm, validate, and render, and
preserve its Traditional Chinese human-facing fields, exact evidence excerpts,
and source titles.

`HARNESS.md` is not a second public protocol. Low does not read it; after the
user selects Medium, High, or Ultra, it is the required internal runtime bridge
for the host.
