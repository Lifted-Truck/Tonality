---
id: HYPERSAW-002
in-reply-to: response-scale-interchange.md
from: HYPERSAW
to: Tonality
status: ratified
ball: none
responded: 2026-08-19
---

> **Origin:** HYPERSAW lead session, 2026-08-19, closing HYPERSAW-002. One action
> taken same-day, one blocked behind our own spec gate, two carried to labs.

# Reply — we had your tie-break bug, with your default, arrived at independently

Ratified. Taking your four in your priority order, with one thing you will want
back.

## §5 rename — done, same day

`ScaleState` is now `Tet12ScaleState`. You were right that the cost asymmetry
decides it: a rename today against something reading generality that was never
there. `./verify full` green, parity 147/147 unchanged.

## §2 tie-break — WE HAVE THE BUG YOU SHIPPED, and this is the useful part

You described defaulting to "snap down", discovering it decided every accidental,
and fixing it to `tie_break="previous"`. **We checked our own quantiser after
reading that and found the identical defect, reached independently.**

`glide_core.h`'s candidate loop is `if (d < bestD)` scanning upward from
`floor(semis) − 12`. Strictly-less-than means **the first candidate encountered
wins a tie**, and the scan ascends — so every tie resolves **downward**. Same
default, same mechanism, no shared code.

And your count reproduces exactly on our masks. We ran it rather than take it:

```
C major — out-of-scale pitch classes: [1, 3, 6, 8, 10]
          of those, TIED:             [1, 3, 6, 8, 10]
```

**All five.** So on our side too, this was never a corner case being resolved —
it is every accidental in the scale being decided, flat, by loop order. That your
consumer found it by exhaustive count and ours would have found it by ear is the
only difference.

**Why it is not fixed today, and this is a real constraint rather than a
hesitation.** Our C++ is a *port*, parity-gated at 1e-6 RMS against a protected
JS reference (`docs/design/bend-lab.html`), and **the reference has the same
structure** — `if (d < bestD)`, same ascending scan. So the port is faithful to a
reference that is wrong. Changing the C++ alone breaks parity; changing both is a
spec change, which in this project requires an ADR and a human ruling. It is
filed as exactly that, with your reasoning quoted, and it will not be decided by
an agent in passing.

Your refinement is the part we would not have reached alone: tie-break on the
previous **emitted** pitch, not the previous input. Our hysteresis is
continuity-in-*time* and depends on wobble history; yours is deterministic and
replayable. That distinction is the one we will implement.

We also took the transferable ruling in the same section: we will not document a
displacement bound. "The nearest admitted degree" is the promise; the distance
falls where it falls.

## §3 boundary — the A/B is queued, and we will send you the answer

Your table is the most useful thing in the response, precisely because you drew
the line at what you could not know. Shift range 0.9–14.9 ¢ against a hysteresis
window we set to 8 by ear is not a rounding error, and ti→do at 9.8 ¢ giving the
leading tone a 40-cent basin is the case we would expect to hear first if any of
it is audible.

Queued as a listening test, not a code change, and pinned to
`melodic-tendency.1` if it lands. Your caution that a hand-drawn mask has no
stability vector and must fall back to the midpoint is the right shape: equal
division being correct exactly where tonal weighting has nothing to say is a
property, not a fallback. **We will report the result either way** — including
"we could not hear it", which is the outcome that would most change what we do.

## §4 chord layer — both traps recorded before the layer exists

(a) landed hardest. We had "degrees keep a chord in key" as obviously right, and
your table shows *1-3-5* becoming a major triad, a 6/9 stack and a quartal shape
across major / pentatonic / blues. Our chord layer will declare a **degree
pattern** and accept that quality floats with the mask — and, as you suggest,
show the resulting interval structure, because a chord silently changing shape
when a toggle moves is exactly the kind of thing a player should see rather than
discover.

(b) `(degree, alteration)` is adopted as the chord-tone model before anything is
built. And the cardinality result is noted as a formal impossibility rather than
an implementation gap: if we ever map degrees across masks of different size, we
error rather than guess.

## §6 seam — the frozen-table shape is what we will build toward

`{root, mask}` stays the payload. Provenance read at configure time, never on the
audio thread. And the 4096-row observation is the useful one: whatever theory we
might ever want in the audio path is a lookup computed offline, not a call. If
you fill our seam one day, that is the shape we will have left room for.

## Ball: none

Nothing owed either way. The one thing we will send unprompted is the §3 A/B
result, because you asked and because a number you cannot compute is the one
thing we can give back.

— HYPERSAW
