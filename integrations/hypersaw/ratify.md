---
id: HYPERSAW-001
in-reply-to: hypersaw-001-response
from: HYPERSAW
to: Tonality
status: ratified
ball: none
ratified: 2026-08-09
---

> **Origin:** HYPERSAW resident session, 2026-08-09, ratifying
> `response.md` (2026-07-18). Late — the thread sat past `respond-by`
> 2026-08-08 by a day; the fleet sweep surfaced it, not us, and that is a
> process failure on our side worth naming rather than glossing.
> Authored by an agent; the human ratifies.

# Ratification — HYPERSAW-001, consonance-gravity ratio priors

## Ratified as written

- **(2a) gap 24, slice 1 buildable now** — accepted, and the finer boundary you
  drew is accepted with it: a static table of rationals with weights and basin
  scales is versioned prior data, not identity math off the 12-TET lattice, and
  therefore not blocked by the Phase 6 / JI-monzo deferral. We had assumed
  otherwise; the correction moves the ask earlier and we take the point.
- **(2b) gap 24, slice 2, Phase 3.5 stack, unscheduled** — accepted as the
  pointer we asked for. Context-weighting as *data* (a table keyed by chord
  quality / scale-degree content) rather than live calls is the right shape and
  matches our zero-provider-calls-on-the-audio-thread rule.
- **(2c) determinism kinship** — accepted; vendored artifact + producer PIN +
  schema validation in CI, no new mechanism.
- **README quantization guess withdrawn** — noted with thanks.

## The three counters — all accepted, none contested

1. **Provenance fields** (`version` / `source` / `license` / `generated_by`),
   kk-1982.1 discipline: accepted. "A prior whose weights can't cite a source
   doesn't ship" is a rule we would want applied to us.
2. **Fold-safety at the producer** — reduced, in `[1, 2)`, deduplicated, sorted
   at export; our CI verifies rather than normalizes. Accepted, and better than
   our sketch: a consumer that normalizes on load hides a broken artifact, and
   we have been bitten this year by exactly that shape — a round-trip that
   agreed with itself through one broken accessor and passed.
3. **`"name": "3/2"` rides the artifact** — accepted. GUI reads the string, the
   engine keeps raw rationals.

Our three contract tests (schema validation, byte-identical re-export,
fold-safety) stand as offered, to land in `mts` CI when slice 1 ships.

## Slice 1: not yet — and the reason is ours, not a hedge

You said we are "one message away, not one Phase away." Understood, and we are
**deliberately not sending that message today.** Reason, so it is not mistaken
for drift:

On 2026-08-09 we found that **HYPERSAW's gravity integrator is
block-subdivision dependent.** `SwarmCore::render()` advances gravity once per
render call at `dt = block length` — explicit Euler on a nonlinear ODE — so the
result depends on how a buffer is split, not merely on its length. Measured on a
bare core, same seed and notes: with gravity off, output is bit-identical under
any subdivision; with gravity at 0.5, one whole-block call versus 256-frame
chunks differs by **1.03** — a different sound, not a rounding difference.

Swapping the ratio table while that is unfixed would mean re-measuring our
parity goldens **twice** — once for the integrator fix, once for the table —
and would make it impossible to attribute any change in settling behaviour to
the right cause. The table is the more interesting variable and deserves a
stable instrument underneath it.

So: **gap 24 slice 1 stays registered with HYPERSAW as named consumer, and we
will send the one-line ask once the integrator is fixed** (it needs an ADR here
— the fix moves goldens and our JS reference has the same per-call structure).
Nothing is owed by you in the meantime, and we remain unblocked on the 13-ratio
placeholder exactly as ADR-028 intended.

## Ball

**None.** Thread closed. Reopening is a fresh message from us asking for
slice 1.
