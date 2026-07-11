"""Adapter registry: one module per provider, registered here.

Keys are exactly "<adapter>@<adapter_version>" as bound by the capability
registry. Each module exposes two pure functions:

    build(query, env) -> RequestSpec   # no network, no side effects
    parse(payload)    -> ParsedResult  # raises AdapterParseError on mismatch

Keep every adapter stdlib-only. Credentials come in through ``env`` and must
never appear in fixtures, occurrences, or fingerprints.
"""

from __future__ import annotations

from . import sonar

ADAPTERS = {
    "perplexity-chat-completions@v1": {"build": sonar.build, "parse": sonar.parse},
}
