---
id: tonality-live-conform-bound
from: Tonality
to: Tonality-Live
status: filed
ball: consumer (a contract test on your side pins the old claim)
filed: 2026-08-15
---

> **Origin:** Tonality resident session, 2026-08-15, from audit issue #262.
> Motivating decision: ROADMAP Phase 7 slice 0 correction (same date).
> Authored by an agent; the human merges.

# Notice: the "≤ 6 semitones" conform guarantee was overstated — corrected

## What was wrong

We told you, in `response.md` and in the accepted contract tests, that a
conform snap can never exceed 6 semitones, "by construction." **That claim was
false at the MIDI boundary**, and one of your three pinned contract tests
(contract 1) asserts the false version.

The mechanism: near MIDI 0/127 the nearer snap candidate can fall outside
0..127. The engine then takes the in-range candidate — and that one can be
further than 6 away. Worked case, reproducible:

```python
conform_to_scale(seq_with_one_note_at_midi_0, [11], 0)   # scale = {pc 11}
# -> delta = +11, to_midi = 11, tie_resolution = "range"
```

**A ≤ 6 move does not exist there.** The nearest in-range scale tone to MIDI 0
in a pc-11 collection *is* MIDI 11. So this is not a bug we could fix by
snapping differently — the promise was impossible, not unimplemented.

## What is actually guaranteed (both verified exhaustively over the boundary)

1. **Every snap lands on the nearest in-range scale tone.** Unconditional. We
   brute-forced this against every legal target across MIDI 0–13 and 114–127
   for dense and sparse collections: the engine's choice always equals the
   true nearest legal tone.
2. **`abs(delta) <= 6` for every edit whose `tie_resolution` is not
   `"range"`.** The bound holds everywhere the register does not forbid it,
   and `"range"` is the exact, already-shipped flag marking where it cannot.

Nothing in the code changed. The docstrings, ROADMAP, and our tests changed —
plus a new exhaustive boundary test covering what the original contract test
missed (it swept MIDI 30–89 and never touched the edge its own docstring
discussed).

## What we suggest on your side (no rush, nothing breaks today)

Your contract test 1 currently asserts `|delta| <= 6` unconditionally. In
practice it cannot fail for you — Live clips are in normal instrument ranges
and your scale picker serves catalog scales, whose max gap is 4 — so this is
correctness hygiene, not an incident. When convenient, relax it to the real
invariant:

```
assert abs(delta) <= 6 or edit.tie_resolution == "range"
```

and, if you want the stronger check, assert `0 <= to_midi <= 127` always.

**If your UI ever surfaces the snap distance**, `"range"` is the case where a
note moves further than a user might expect — worth the same treatment as your
collision reporting, since a large unexplained jump reads as a bug even when it
is the only legal answer.

We would rather send you a correction to a promise we made than let a pinned
test keep asserting something we now know is false.

Ball: consumer — adjust the contract test at leisure.
