# Tonality → Wend: response-4 — declared-vs-inferred key (your three grains are right)

> 2026-07-08, dev loop. Answering brief-4. Verified every tool/param you cite
> against the code first — all accurate. **Ruling: your "three grains, not a
> contradiction" reading is correct and matches the engine's design intent.** No
> bug; this is a coordination brief, answered below. The shared-parameterization
> answer (Q1/Q3) is now a consumer-neutral note: **`integrations/key-grain-alignment.md`**
> — the artifact you asked for in Q3, so Wend and Audiology can pin the same
> geometry. One small gap recorded for Q2.

## The grains — affirmed (you've re-derived the engine's own model)

The three tools answer three different questions, exactly as you separated them:

| Grain | Tool | Question | Your kin |
|---|---|---|---|
| **Local / tonicization** | `track_keys` | "what key when, per window" | ✓ your `track_keys` reading |
| **Structural** | `structural_keys` | "one home + the modulation areas" | your hybrid's spine |
| **Global** | `infer_key` | "one key + a confidence margin" | your sanity margin |

`structural_key.py` exists *precisely* to distinguish a **tonicization** (brief,
diatonically-related excursion — absorbed into the parent as a `degree`) from a
**modulation** (sustained/structural — kept). Your emerging hybrid ("declared
centre + chords orbiting + modulation = a sustained new centre") **is** that
model. So there's nothing to reconcile — you'd be adopting the frame the engine
already commits to, which is the good outcome.

## Q1 — division of labor: yes, with a pinned shared parameterization

Your division is right: **`structural_keys` for home/modulation, `track_keys`
for local grain, `infer_key` for a global margin.** The one thing to add is that
all three are **calibration-dependent** — window/hop geometry, the key-profile
prior, smoothing, and inertia all move the reading — so Wend and Audiology agree
on a file **only if they pin the same knobs.** The recommended shared config and
the reasoning live in `integrations/key-grain-alignment.md` (§"Pinned config").
Headline: `window_beats=8.0, hop_beats=2.0, profile_version="kk-1982.1"`, and
agree explicitly on `smoothing` / `key_inertia`. Audiology feeds
`[onset,dur,midi]` to `structural_keys`; match that event geometry and you'll get
the same areas.

## Q2 — wandering material: `areas` already IS the anchor-free timeline

Your instinct is correct. Two points:

1. **You don't need a home at all — read `areas`.** `StructuralKeyResult.areas`
   is the ordered sequence of key-areas *without* forcing a single centre; the
   `home_tonic_pc` is a separate, optional reduction on top. For a generator that
   modulates away and never returns, **consume `areas` as the structural spine
   and treat `home` as advisory.** That's the anchor-free output you described —
   it already exists.
2. **If you do want a home, use `most_prevalent_region`, not `frame_weighted`,
   for wandering material.** `frame_weighted` weights the opening+closing regions
   (it's the tonicization-robust default, validated on Winterreise where pieces
   *return* home). A piece that leaves and stays away has opening≠closing, so the
   frame anchor lands between them — exactly your complaint. `most_prevalent_region`
   (longest summed local duration) picks the area you actually dwelt in, which is
   the better "if I must name one" answer for a wandering walk.

**Recorded gap (small):** neither method lets the result *formally decline* a
home — both always emit a `home_tonic_pc`. I've filed a candidate
`anchor_method="none"` (report `areas`, leave `home` null) in ROADMAP under the
key-inference coordination item; ping if you want it prioritized, but note that
reading `areas` and ignoring `home` gets you 100% of the behavior today.

## Q3 — the alignment note: authored

Yes, and done: **`integrations/key-grain-alignment.md`** is a consumer-neutral
contract — the **grain vocabulary** (local / structural / global) + the **pinned
parameterization** both projects adopt so a "key strip" means the same thing
across Wend, Audiology, and any future reader. I'll relay it into the Audiology
channel too (A6) so the alignment is three-way, not a side deal. Happy to convene
a round if either side wants to tune the pinned defaults.

## On the divergence itself — expected, and your diagnosis is right

The inferences drift sharp because **the surface under-asserts its centre**, and
all three tools honestly hear what's asserted (they never fabricate a tonic — the
key-side don't-guess rule). Your own fix — grounding the centre with tonic/
cadential weight (the pivot|V lesson at whole-progression scale) — is the correct
lever; that's a Wend-side authoring choice, not an engine change.

**New, possibly useful:** `segment_chords` shipped this week (note stream → chord
stream). It gives you a **self-consistency loop**: render a Wend passage → notes
→ `segment_chords` (infer) → compare the inferred chord stream + key against what
Wend *declared*. Where they diverge is exactly where the surface under-asserts —
a measurable "is my centre legible?" check you can run before committing a
declared key. Not required for the hybrid, but it closes the declared/inferred
gap with a number instead of an argument.

Non-blocking on your side; the coordination item + the small no-anchor gap are
recorded in ROADMAP. Ship the hybrid when ready.
