---
id: mcp-hardening-response
in-reply-to: response-mcp-hardening.md
from: Tonality
to: security / originating agent
status: responded
ball: julian (two decisions — the second is now unblocked)
responded: 2026-10-08
---

> **Origin:** Tonality resident session, 2026-10-08. Motivating decision:
> Decision 85 (security by enforcement; required for repos that parse untrusted
> input), applied as `kit/security/`'s method — inventory first, then guards
> proven on plants. Authored by an agent; the human merges.

# Notice — P0.2 closed: all four P0 items are now green

`response-mcp-hardening.md` (2026-07-25) left **P0.2 (strict schema validation)
partial**: unknown-field rejection verified, "fuzz set absent". Both halves now
exist, and the fuzz set found far more than the partial status implied.

| Item | 2026-07-25 | Now |
|---|---|---|
| P0.1 metadata freeze/lint | ✅ | ✅ |
| **P0.2 schema validation** | 🟡 partial | ✅ **closed** — runtime type + finiteness validation at every door; fuzz set over all 79 tools; resource budgets |
| P0.3 injection audit | ✅ | ✅ |
| P0.4 transport | ✅ | ✅ + strict `Content-Length` on the bridge |

**What the fuzz set found:** 1,905 malformed calls produced **523 defects in 65 of
79 tools**, plus **11 inputs that allocated over 1.2 GB per second until the OS
killed the process**. That last class was reachable through the official stdio
server, because pydantic accepts infinity for a float and valid JSON encodes it as
`1e999`. Now **0 and 0**. Every guard ships with a must-fail control, and all 13
were proven by removal (each turned its test red in seconds, at most 101 MB).
Full inventory, root causes and accepted residuals: `docs/security/BOUNDARIES.md`.

## Your two decisions

1. **`midi_file_analysis` path policy** — unchanged and still open.
   Recommendation stands: an env-var allowlist with an unrestricted default.
2. **Public registry listing** — **its stated precondition is now met.** The
   2026-07-25 recommendation was "do not list until P0.1 is green". P0.1 was
   already green; with P0.2 closed, every P0 item is. The evidence no longer
   argues against listing. Whether to list is still your call.

Ball: **julian** — both decisions are the human's.
