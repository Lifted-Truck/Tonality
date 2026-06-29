# AUDIOLOGY → Tonality: brief-15 (chord-anatomy maths — expose DFT phase + a representation descriptor)

> Filed 2026-06-28 by Audiology's agent. Audiology now ships a **Chord Anatomy** view
> (interval-vector / colour-wheel / harmony-map surfaces). All the maths is currently
> computed client-side in `src/lib/theory/chord-anatomy.ts`. This brief hands that maths
> to Tonality so the engine can expose it and **other systems can compute the same
> surfaces** — the north-star is for Audiology to *consume* the engine, not own this.
> Documentation + data-exposure ask; no behaviour change requested beyond surfacing
> `DFT` **phase** and (optionally) a renderer-agnostic descriptor. No `mts/` patch attached
> — this is the brief; Tonality owns the engine implementation.

## Why now

The whole Chord Anatomy view is derived from a pitch-class set (and, where voicing matters,
the sounding MIDI). Today Audiology recomputes interval vector / DFT / set-class locally. Per
the division of labor (Tonality owns *determinations*; Audiology owns *rendering*), these
should come from the engine. The one piece the engine doesn't currently expose over the
bridge is **DFT phase** — and phase is load-bearing here (it drives the colour hue and the
major/minor chirality). Everything else is "please expose what you already compute."

## The surfaces and their maths (all verified)

Conventions: pitch classes `p ∈ 0..11`; `f_k = Σ_{p∈set} e^(-2πi k p/12)` for `k=0..6`
(`f0` = cardinality). Interval class `ic(a,b) = min(|a−b| mod 12, 12 − |a−b| mod 12)`.

### 1. Interval vector — `[ic1..ic6]` (already computed)
Inversion-invariant. ic1=m2/M7 … ic6=tritone. Just confirming this is the canonical
"clinical" fingerprint and is exposed.

### 2. DFT magnitude **and phase** — the ask
`|f_k|` is the transposition- and inversion-invariant "harmonic quality" (Quinn/Amiot/
Tymoczko/Yust); `arg(f_k)` rotates under transposition and **negates under inversion**.
**Ask: expose both `mag` and `phase` for `f1..f6`** on the set-class / `name_pcs` path (and
any future `pcset_info`). Phase is what makes the next two items possible. Sanity values:
- augmented `{0,4,8}` → a pure 3-cycle: `|f3| = |f6| = 3`, all others 0.
- major `{0,4,7}` and minor `{0,3,7}` → identical magnitudes `f1..f6 ≈ 0.52, 1.41(*), 2.24, …`
  (magnitudes can't tell them apart) but **opposite phase handedness** (see chirality).

### 3. Somatic colour (Audiology's *encoding*; the inputs are the engine's)
Two colours, both resultant-vector constructions. The **hue mapping and OKLCH encoding are
Audiology's rendering** and stay ours; the engine just needs to expose the inputs.
- **Root-aware (circle-of-fifths):** place each pc at angle `(pc·7 mod 12)·30°`, take the
  circular mean; hue = its angle, saturation = its length ("focus"), register → OKLCH
  lightness. (This is essentially `arg/|·|` of a fifths-rotated f5-like sum.)
- **Root-blind (interval-content):** rim = the five inversion-paired interval classes
  weighted by `[ic1..ic5]`, the tritone (`ic6`) sits at the centre (no direction), resultant
  = transposition-invariant "interval colour". Inversional pairs collapse (maj = min,
  dom7 = m7♭5); symmetric chords that grey out on the pitch wheel turn vivid (aug = pure M3).

### 4. Harmony map — consonance × chirality (Tymoczko trichord geometry)
- **Consonance axis = `|f5|`** (perfect-fifth content). High for triads/sus, 0 for aug/
  whole-tone, low for clusters. Generalizes to any chord directly from the DFT.
- **Chirality (trichord-native) = `(a−b)(b−c)(c−a)`** on the three step-gaps `a,b,c`
  (`a+b+c=12`). Rotation-invariant; **flips sign under inversion** → major (−) and minor (+)
  on opposite sides of a symmetric spine (achiral chords = 0). This is the natural "handedness"
  that separates maj/min — which magnitudes alone cannot.
- **Insight worth carrying:** consonance and major/minor are *orthogonal* axes, not one scale.

### 5. Set-class identity
Prime form + 12-bit pc bitmask + interval vector. Mostly already available via `set_class_info`;
just flagging that the anatomy view consumes prime form and would prefer engine-canonical
prime form over our local one when available.

## Open theory problem (genuinely engine territory — flagging, not yet a hard ask)

The chirality in §4 is **trichord-native**. For 4+ note chords the handedness lives in the DFT
**phases**, but a *single, sign-consistent* chirality scalar is subtle: the natural
transposition-invariant, inversion-odd phase invariants (e.g. `5·φ3 − 3·φ5`) are near-degenerate
for triads and miss some tetrachord pairs (we verified the f3/f5 invariant fails to separate
dom7 from m7♭5, which *are* an inversional mirror pair). A principled **general chirality**
(probably: minimal inversional-asymmetry residual over a best-fit symmetry axis, with a
consistent sign convention) would let the harmony map generalize past trichords. This feels
like real Tonality math if it interests you; if so it could become its own brief.

## A documented property you may want in the engine's test corpus

Enumerating all 4083 pc-sets (|S|≥2) through the root-blind interval-content map: only **199
distinct interval vectors → 185 distinct wheel positions**, a sparse finite cloud heavily
massed near grey (109 of 185 at focus < 0.15); **only the five pure dyads and the augmented
triad reach full saturation** (richness and saturation are in tension). Useful as a regression
fixture if the engine ever exposes the interval-content resultant.

## Division of labor (proposed)

| Piece | Owner |
|---|---|
| Interval vector, DFT **mag + phase**, set-class, prime form, `|f5|` | **Tonality** (determinations) |
| Step-gap chirality (trichord) + the general-chirality theory | **Tonality** (it's maths) |
| Hue mapping, OKLCH encoding, the wheels/histogram/ladder/map **rendering** | **Audiology** |
| A renderer-agnostic "interval/colour-content" **descriptor** | **Tonality Representation layer** (cf. brief-2's bracelet/Tonnetz descriptors) |

## Concrete asks (smallest first)

1. **Expose DFT `phase` alongside `mag`** for `f1..f6` on the set-class / `name_pcs` path. (This
   alone unblocks Audiology consuming colour + the chirality inputs instead of recomputing.)
2. Confirm prime form + bitmask are (or can be) returned by `set_class_info`.
3. *(Optional, larger)* a Representation-layer "interval/colour-content" descriptor so other
   renderers get the resultant constructions, not just raw components.
4. *(Optional, research)* the general n-note chirality above.

— Audiology
