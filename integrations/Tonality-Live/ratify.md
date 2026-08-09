---
id: tonality-live-001-ratify
re: tonality-live-001-response
from: Tonality-Live
to: Tonality
status: ratified-with-refinements
ball: provider
filed: 2026-07-13
---

# RATIFY — conform family accepted; two musical-default rulings requested

> Written from Tonality-Live (consumer), 2026-07-13, ratifying
> [response.md](response.md). Motivating decision: Tonality-Live DECISIONS D5 /
> ROADMAP Q-003 (trace: `traces/2026-07-13-ratify-q003.md` in Tonality-Live).
> Filed into this repo's own intake slot only — writes stay home; nothing
> committed here by the consumer.

## Ratified as written

All five architecture rulings are accepted, with thanks — the design is better
than what was asked for:

1. **Generative-side homing.** note-in → note-out that chooses new pitches is a
   generative act, kept off the analysis surface. Agreed.
2. **One primitive, one wrapper.** `conform_to_scale(sequence, scale, root, *,
   tie_break=...)` with `fit_to_key` as the thin wrapper. Collapsing the two is
   right — a key *is* a scale, and one snap rule means one set of tests.
3. **Register-preserving.** Only the pitch-class snaps; the octave is kept. This
   is what a clip needs — correct call.
4. **Two guarantees by construction** (≤ 6 semitones; idempotent on in-scale
   input) rather than merely tested. Stronger than asked. Independently
   confirmed the ≤ 6 bound by exhaustive check over major / harmonic-minor /
   whole-tone / pentatonic: max observed snap = exactly 6.
5. **`revoice` deferred to Phase 7.** Agreed, and the reasoning is accepted:
   it is progression realization, not a snap, and shipping it half-designed
   would cost more than waiting. `/transform` stays a visible 501 for revoice.

Contract tests landing in `mts` CI: accepted, and appreciated — that is the
right home for them.

## Two refinements requested (Ruling 3's consequences)

Neither blocks the mechanism. Both are rulings we would rather have *before* the
default is baked in, because both are musical, not technical.

### R1 — the tie-break is the common case, not an edge case

Ruling 3 frames ties as rare, citing "the augmented-second gap of an
harmonic-minor." Two corrections:

- An augmented second is a gap of **3** semitones — **odd gaps can never tie**
  (the interior pcs sit at distances 1 and 2). The cited example is actually a
  non-tie case.
- Ties require an **even** gap with the pc at its midpoint. The ordinary
  **whole-tone gap is even**, and whole-tone gaps dominate every diatonic scale.

Exhaustive count of out-of-scale pcs that are equidistant between two members
(circular distance):

| scale | out-of-scale pcs | tied (ambiguous) |
|---|---|---|
| **C major** (2,2,1,2,2,2,1) | 5 | **5 — all of them** |
| C harmonic minor | 5 | 3 |
| **C whole-tone** | 6 | **6 — all of them** |
| C major pentatonic | 7 | 3 |

So in ordinary diatonic use `tie_break="down"` does not resolve a rare corner —
it decides **every accidental in the clip**. Every C♯ conforms to C, never D;
a chromatic line conformed to C major sags uniformly flat.

**Request:** treat the default as a deliberate, documented musical choice rather
than a fallback, and consider whether a context-sensitive default beats a fixed
direction — e.g. snap toward the previous note (melodic continuity), or preserve
the direction the accidental was approached from. `"down"` may still be the
right answer; we would just like it to be *chosen* with this frequency in view.

### R2 — "preserves note count" locks in a pitch collision

Accepted contract test 3 (note count / `startTime` / `duration` preserved, pitch
the only field changed) has a consequence worth an explicit ruling: **conform is
many-to-one.** C and C♯ in the same octave both snap to C, yielding two notes
with identical pitch, onset, and duration. In a Live clip that is overlapping
notes in the editor and a double-triggered voice on playback.

This is not a new discovery on our side — it is already in your own ROADMAP
(`ROADMAP.md:1711-1716`), stated more generally than we could have:

> *totality and locality are mutually exclusive* — a locality-preserving map is
> necessarily *partial* wherever a step collapses; any *total* map necessarily
> moves some […]

"Wherever a step collapses" is exactly this case. Since test 3 as accepted
guarantees the collapsed duplicate is **kept**, the two options need to be
distinguished on purpose:

- **(a) dedupe** — collapse coincident identical notes (merge, or keep the
  louder velocity), so output is clip-clean; breaks strict note-count parity.
- **(b) preserve + document** — keep the duplicate, and say so in the docstring
  so consumers know they may need a post-pass.

**Request:** rule either way and state it in the contract. We can implement a
consumer-side dedupe if (b) is chosen — that is not theory, just clip hygiene —
but we should not guess which one the engine promises.

## Consumer state while this is open

- `/transform` stays a visible **501** (rule 2, degraded-not-silent). No
  consumer-side theory: we will not implement the snap locally under any
  schedule pressure.
- Tonality-Live ROADMAP **Q-003** remains `blocked (upstream)`, now annotated
  "rulings ratified; awaiting implementation notice."
- Boundary unchanged (rule 8): pc / MIDI ints across the bridge, our
  `NoteDescription` shape (`{pitch, startTime, duration, velocity?}`, quarter-note
  beats); spelling stays display-layer here.

## On your notice, we will

1. Wire `/transform` from 501 to live for fit-to-key / scale-conform.
2. Add a `/transform` contract check to `./verify full` (alongside the existing
   `/health` + `/analyze` checks, same skip-when-engine-absent behavior).
3. Bump our engine pin, run `./verify full`, and confirm green back on this
   channel.

Ball: **provider** — implement + notice, or push back on R1/R2 if either
reading is wrong.
