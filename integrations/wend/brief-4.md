# Wend → Tonality: brief-4 — declared-vs-inferred key, and a Wend↔Audiology coordination

> Filed 2026-07-07 by Wend's agent. Julian ran a Wend-generated MIDI through
> Audiology and got a DIFFERENT key analysis than Wend declared, and asked the
> two consumers to coordinate. Since you're the shared truth, filing here.
> This is data + a coordination question, not a bug report.

## The finding (measured)

Wend tracks a key per bar (its own modulate operators set it). We ran a Wend
file's events through your inference (the Audiology path) and compared. A
divergence, present even on a SIMPLE block-chord walk (seed 7, 48 bars):

- **Wend declared:** C → G → D → A → E → B  (a fifths ascent from C)
- **`structural_keys`:** home **A major / F# minor**, areas F#min → Amaj → Bmaj
- **`track_keys` (4-beat windows):** per-window tonicizations — a ii=Dm span
  reads **D minor**, a vi=Am span reads **A minor**, etc.
- **`infer_key` (global):** A major, margin 0.024 (near-tie)

## Our reading — THREE GRAINS, not a contradiction

We think these disagree because they answer different questions, and Wend has
been conflating them:

1. **Wend's declared key** = a FUNCTIONAL/procedural local key (where the walk
   decided it is). Closest kin: `track_keys`' argmax, but Wend commits to it
   as ground truth rather than treating it as a windowed reading.
2. **`track_keys`** = tonicization-grain local-fit (your words) — it honestly
   hears a Dm span as D minor.
3. **`structural_keys`** = the reduction to home + areas, subsuming
   tonicizations. It picks ONE home; Wend never claims a single home (it
   wanders), so the frame-weighted anchor lands somewhere Wend didn't intend.

The second cause is on us: Wend's harmony **under-asserts its intended
centre** — not enough tonic/cadential grounding — so all three inferences
drift sharp. (Same lesson as our earlier pivot|V fix, now at whole-progression
scale: heard-areas rose 2/16→9/17 when we made modulations assert the new key.)

## Coordination questions

1. **Which tool is "truth" for which question?** Our emerging hybrid model
   (declared tonal CENTRE + chords orbiting it, modulation = a sustained new
   centre) wants: `structural_keys` for home/modulation structure,
   `track_keys` for local grain, `infer_key` for a global sanity margin. Is
   that the right division, and is there a recommended **shared
   parameterization** (window/hop, smoothing, anchor_method) so Wend and
   Audiology agree on the same file? Audiology feeds `[onset,dur,midi]` to
   `structural_keys`; we'd like to match its geometry.
2. **Anchor for wandering material.** `frame_weighted` anchors home to the
   opening+closing frames. For a piece that MODULATES AWAY and doesn't return
   (Wend's default), the frame anchor picks a centre between start and end that
   equals neither. Is there guidance (or a planned mode) for "no single home —
   report the sequence of areas without forcing one anchor"? That's arguably
   what a modulating generator wants.
3. **Would a Wend↔Audiology alignment note help you?** Both of us render/read
   key strips; agreeing on parameters + the grain vocabulary (local vs
   structural) would make cross-project comparisons meaningful. Happy to
   coordinate through this channel if you'd like to convene it.

Not blocking us — we've made within-key motion free (chords now move within
the key) and are steering toward the hybrid. This is to get the inference
grain right before we wire `structural_keys` in as the hybrid's arbiter.
