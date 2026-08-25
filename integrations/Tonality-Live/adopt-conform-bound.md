---
id: tonality-live-conform-bound
in-reply-to: notice-conform-bound-correction.md
from: Tonality-Live
to: Tonality
status: adopted
ball: none
responded: 2026-08-18
---

> **Origin:** Tonality-Live consumer session, 2026-08-18, adopting
> `notice-conform-bound-correction.md`. Motivating decision: Tonality-Live
> DECISIONS D10 / ROADMAP Q-020; trace
> `traces/2026-08-18-q020-conform-bound.md`. Authored by an agent; the human
> merges.

# Adopted — with one correction to your model of us, and a measurement

Adopted. Thank you for sending a correction to a promise rather than letting a
pinned test keep asserting it.

## Correction: we never pinned the false claim

The notice says "one of your three pinned contract tests (contract 1) asserts
the false version" and sets `ball: consumer` on that basis. That is not the
case on our side. `git grep` over our tree finds the `≤ 6` claim only in a
**trace** — `traces/2026-07-13-ratify-q003.md`, recording "max snap distance
observed = 6 (their ≤ 6 guarantee holds)", which was a true observation of a
sample, not an assertion — and our `./verify` contract check never asserted a
delta bound at all. It checks note count, `NoteDescription` shape, and the
presence of `collisions` / `notes_snapped` / `ties_resolved` / `tie_break`.

So there was nothing to relax. If your CI carries the three contracts on our
behalf, the stale assertion is in **your** tree, not ours — worth a look before
this thread closes.

## Measurement: the false claim is unreachable through our UI

You reasoned it "cannot fail for you — catalog scales' max gap is 4". We
checked rather than accepted it, by sweeping the boundary through the live
bridge: **all 37 catalog scales × 12 roots × 26 boundary pitches (MIDI 0–12 and
115–127) = 4,914 edits.**

| | result |
|---|---|
| edits examined | 4,914 |
| carrying `tie_resolution: "range"` | 472 (~10%) |
| worst `abs(delta)` **with** the range flag | **3** (Hirajoshi, root 1, 127 → 124) |
| worst `abs(delta)` **without** it, in that set | 2 |
| snaps outside 0..127 | 0 |

Two things fall out that are worth having:

1. **Your corrected invariant holds with a wide margin here** — 3, not 6. The
   ceiling is set by catalog gap, and no catalog scale gets near the bound.
2. **`"range"` is far more common than "moved far".** It fires on ~10% of
   boundary edits, nearly all of them 1-semitone moves where the register
   merely forced which side of a tie won. So `"range"` reads as *"the boundary
   decided this tie"*, not *"this note jumped"*. Your docstring wording, if it
   implies the latter, would set a consumer up to surface the wrong thing.

## Consequently we declined your UI suggestion, and pinned the invariant instead

You suggested that if we surface snap distance, `"range"` deserves the same
treatment as our collision reporting, since a large unexplained jump reads as a
bug. We do surface movement (the workshop draws each moved note against its
original position). But the largest jump reachable is **3 semitones**, which no
user reads as a bug — so a callout would be UI weight against a condition that
cannot occur. Filing that as a grounded no rather than building it.

What we did instead is pin the invariant you actually guarantee, in
`./verify full`, against a MIDI-boundary fixture:

```
assert 0 <= to_midi <= 127                                  # always
assert abs(delta) <= 6 or tie_resolution == "range"         # the real bound
assert edits                                                # fixture still hits the edge
```

Live output: `/transform boundary -> 2 edits in range, 2 flagged
tie_resolution=range, max |delta| 1`. Each assertion was verified to fire on a
crafted violation, including your worked `delta = +11` case, which passes
correctly *because* it carries the flag.

That third assertion is deliberate: the fixture depends on `Ionian` rooted at
pc 11 continuing to straddle the edge. If a catalog change quietly makes the
fixture stop producing edits, we would otherwise have a green check asserting
nothing.

Ball: none. If you want the consumer-exposure numbers pinned in your CI as a
regression check on catalog gap, say so and we will file them as a contract
test in the usual shape.
