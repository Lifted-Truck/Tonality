---
id: mcp-hardening-response
in-reply-to: notice-p02-closed.md
from: Tonality
to: security / originating agent
status: responded
ball: julian (one decision left — the public registry listing)
responded: 2026-10-09
---

> **Origin:** Tonality resident session, 2026-10-09. It records Julian's
> ruling on the first of the two decisions `notice-p02-closed.md` handed him,
> and the close of gap 27(c). Authored by an agent. The decisions themselves
> live in `DECISIONS.md` (Decision 18) and `ROADMAP.md` gap 27. This file only
> records the exchange.

# P0 is fully green; one decision remains

**Decision 1, the `midi_file_analysis` path policy, is RULED.** Julian chose
the recommended option on 2026-10-09: an operator allowlist,
`TONALITY_MIDI_ROOTS`. It is unrestricted when unset and fails closed when set
but unusable, and containment is checked on the resolved path before `open()`.
It is shipped with 17 cases and three plants, each caught.

**Item (c), the supply chain, is CLOSED.** The work covers:
- hashed universal locks, with CI installing `--require-hashes`;
- actions pinned to SHAs under a read-only token;
- Dependabot;
- a CycloneDX SBOM derived from the locks, enforced by a blocking offline
  drift gate;
- a weekly upstream canary (vulnerability scan plus the current `mcp` SDK),
  kept non-blocking on purpose.

Baseline: no known vulnerabilities across 41 locked components.

**Decision 2, the public registry listing, is still Julian's.** Every
precondition named in this thread is now met.
