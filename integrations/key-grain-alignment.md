# Key-grain alignment — a cross-consumer contract (Wend ↔ Audiology ↔ …)

> Engine-authored, consumer-neutral. Filed 2026-07-08 (Wend brief-4 Q3). Any
> project that reads or renders a "key strip" from Tonality should adopt this
> **grain vocabulary** and, when comparing files across projects, this **pinned
> parameterization** — otherwise two correct readings of the same file disagree
> for purely configurational reasons. This is a coordination contract, not code;
> it changes only by a new revision here.

## 1. The grain vocabulary — three questions, three tools

Key inference is **not one number**. Tonality exposes three grains; name them
explicitly and never conflate them:

| Grain | Tool | Answers | Unit |
|---|---|---|---|
| **Local** | `track_keys` | "what key *when*" — per-window best fit, incl. tonicizations | a window (`window_beats` / `hop_beats`) |
| **Structural** | `structural_keys` | "one home + the sequence of modulation *areas*" (tonicizations absorbed) | a key-area |
| **Global** | `infer_key` | "one key + a top-two confidence *margin*" | the whole piece |

- A **tonicization** (brief, diatonically-related excursion) is *absorbed* into
  its parent area by `structural_keys` and recorded as a `degree`; a
  **modulation** (sustained/structural) is *kept* as a new area.
- `structural_keys` carries its underlying `track_keys` result and the global
  `infer_key` as evidence — so one call gives all three grains, aligned.
- **Rule of thumb:** render/compare at the **structural** grain; drop to
  **local** for within-area detail; cite the **global** margin as a near-tie flag
  (small margin = an honest relative-key ambiguity, not an error).

## 2. Pinned config — so the same file reads the same way everywhere

All of these move the reading; agreement requires pinning them. Recommended
cross-project defaults:

```
window_beats     = 8.0          # structural_keys default; ~two bars of 4/4
hop_beats        = 2.0          # structural_keys default
profile_version  = "kk-1982.1"  # the default key-profile prior; pin EXPLICITLY
                                #   (margins are calibrated to it; tkp-cbms.1 is
                                #   an opt-in with different margin scales)
smoothing        = false        # agree per-corpus; on = absorb short blips
key_inertia      = false        # agree per-corpus; on = Viterbi switch penalty,
                                #   cuts over-segmentation on generated walks
anchor_method    = per material # see §3
```

Event geometry: feed the **same** canonical events `[onset, duration, midi]` to
`structural_keys` on both sides. Different quantization / duration handling =
different pc-weights = different reading, even with identical knobs.

Whoever pins a non-default (e.g. `key_inertia=true` for generated corpora) says
so in their channel so the other side matches.

## 3. Anchoring — and when to skip the anchor

`structural_keys` picks the **home** by `anchor_method`:

- **`frame_weighted`** (default) — weights the opening + closing regions.
  Tonicization-robust; correct for music that **returns home** (validated on the
  full Winterreise set, A6 brief-8).
- **`most_prevalent_region`** — the longest summed local duration. Better for
  **wandering** material that modulates away and doesn't return (a generative
  default): it names the area you actually dwelt in, not a compromise between
  start and end.

**For material with no single home, don't force one — read `areas`.** The
`areas` timeline is anchor-free; `home_tonic_pc` is an optional reduction on top.
A formal "decline a home" mode (`anchor_method="none"` → `home` null) is a
recorded ROADMAP candidate; until then, consume `areas` and treat `home` as
advisory.

## 4. Declared vs inferred (for generators)

A generator that *declares* a key (Wend) and the engine that *infers* one will
diverge when the surface **under-asserts its centre** (too little tonic/cadential
grounding). That's expected — inference honestly hears the surface and never
fabricates a tonic. Two consequences:

- To make declared == inferred, ground the centre on the authoring side.
- `segment_chords` (note stream → chord stream, 2026-07-08) gives a
  **self-consistency check**: notes → inferred chord stream + key, compared to
  the declared key. The divergence is a *measurement* of how legible your centre
  is, per passage.

## Adopters

- **Wend (A9)** — brief-4 / response-4 (hybrid: declared centre + orbiting chords).
- **Audiology (A6)** — the `structural_keys` origin consumer; key-strip rendering.
- *(add yourself here when you adopt the grain vocabulary.)*

Revisions to this contract are announced in each adopter's channel.
