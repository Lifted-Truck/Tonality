# AUDIOLOGY → Tonality: brief-15 (chord-anatomy maths — expose DFT phase; general chirality)

> Filed 2026-06-28 by Audiology's agent. Audiology now ships a **Chord Anatomy** view
> (interval-vector / colour-wheel / harmony-map surfaces). All the maths is computed
> client-side in `src/lib/theory/chord-anatomy.ts`; this brief hands it to Tonality so the
> engine can expose it and **other systems can compute the same surfaces**. Documentation +
> data-exposure ask. The one real code ask is surfacing **DFT phase** over the bridge; the
> rest is "expose what you already compute" + two research items. No `mts/` patch attached —
> Tonality owns the engine implementation.
>
> NB this is a re-file: the previous untracked copy was wiped (looks like a `git clean` from
> the concurrent worktree work). Please commit promptly.

## Why now

The whole view derives from a pitch-class set (+ the sounding MIDI where voicing matters). Per
the division of labor (Tonality owns *determinations*, Audiology owns *rendering*), these should
come from the engine. The only piece not exposed over the bridge today is **DFT phase** — and
phase is load-bearing (it drives the colour hue *and* the major/minor chirality).

Conventions: pc `p ∈ 0..11`; `f_k = Σ_{p∈set} e^(-2πi k p/12)`, `k=0..6` (`f0`=cardinality).
`ic(a,b) = min(|a−b| mod 12, 12−|a−b| mod 12)`.

## The surfaces and their maths (all verified)

### 1. Interval vector `[ic1..ic6]` — already exposed; confirming it's the clinical fingerprint.

### 2. DFT magnitude **and phase** — the one code ask
`|f_k|` = transposition- and inversion-invariant harmonic quality (Quinn/Amiot/Tymoczko/Yust);
`arg(f_k)` rotates under transposition, **negates under inversion**. **Ask: expose both `mag`
and `phase` for `f1..f6`** on the set-class / `name_pcs` path (and any future `pcset_info`).
Sanity: augmented `{0,4,8}` → `|f3|=|f6|=3`, rest 0; maj `{0,4,7}` and min `{0,3,7}` have
identical magnitudes but opposite phase handedness (see §4).

### 3. Somatic colour (Audiology's *encoding*; inputs are the engine's)
Two resultant-vector constructions. Hue mapping + OKLCH encoding stay ours.
- *Root-aware:* each pc at circle-of-fifths angle `(pc·7 mod 12)·30°`, circular mean → hue/focus.
- *Root-blind:* rim = the five inversion-paired interval classes weighted by `[ic1..ic5]`, tritone
  at centre → transposition-invariant interval colour (maj=min, dom7=m7♭5 collapse).
- *Documented property* (regression-fixture candidate): enumerating all 4083 pc-sets, the root-blind
  resultant reaches only **185 distinct points**, massed near grey; only the five pure dyads + the
  augmented triad hit full saturation.

### 4. Harmony map — consonance × chirality
- **Consonance = `|f5|`** (perfect-fifth content). Generalizes to any chord from the DFT.
- **Chirality:** trichord-exact `(a−b)(b−c)(c−a)` on the step-gaps; **general** = `Im(f1·f2·conj(f3))`
  (see below). Major < 0, minor > 0; symmetric chords = 0.
- **Insight:** consonance and major/minor are *orthogonal* axes, not one scale.

## General chirality — what we derived (you may want this in the engine)

For 4+ note chords the handedness lives in the DFT **phases**. We worked it out enough to ship:

- The phase invariants `m·φ_j + n·φ_k` (e.g. `5·φ3 − 3·φ5`) are near-degenerate for triads and
  **miss** mirror pairs — verified the f3/f5 invariant cannot separate dom7 from m7♭5.
- The right tool is the **bispectrum** `B(a,b) = f_a · f_b · conj(f_{(a+b) mod 12})` — the canonical
  shift-invariant phase descriptor; `Im(B)` is transposition-invariant and **inversion-odd**.
  - The *full* symmetric sum `Σ Im(B(a,b))` is **identically 0** (each term cancels its conjugate
    partner `B(12−a,12−b)=conj(B(a,b))`). Don't sum the whole thing.
  - **`Im(B(1,2)) = Im(f1·f2·conj(f3))`** is what Audiology ships: `0` for **every** inversionally-
    symmetric chord, opposite for mirror pairs, `major<0/minor>0` (matches the trichord convention),
    and it **separates dom7 ↔ m7♭5**. Enumeration over all 350 set classes: 0 false-nonzeros on
    achiral sets; clean over the whole chord vocabulary and all 168 chiral trichords; false-zeros only
    on **28 exotic 5–7-note set classes** (none musical). It is *not* identical to the step-gap
    chirality (they diverge in sign on ~29% of trichords) — both are legitimate; pick one, be consistent.

- **Open problem (yours if it interests you):** a *complete*, sign-consistent chirality with **no**
  false zeros. The magnitude is clean — `‖Im(B(a,b))‖` over the independent slices is `0` **iff**
  achiral (the bispectrum is complete up to translation+reflection). The hard part is a globally
  consistent **sign** across all set classes (a single slice gives a clean sign but 28 blind spots;
  the norm gives completeness but no sign). A resolution would let `pcset_info` expose a canonical
  chirality scalar for any chord.

## Division of labor

| Piece | Owner |
|---|---|
| Interval vector, DFT **mag + phase**, set-class, prime form, `|f5|` | **Tonality** |
| General chirality theory (complete signed invariant) | **Tonality** (it's maths) |
| Hue mapping, OKLCH encoding, the wheels/histogram/ladder/map rendering | **Audiology** |
| Renderer-agnostic "interval/colour-content" descriptor | **Tonality Representation layer** (cf. brief-2) |

## Concrete asks (smallest first)

1. **Expose DFT `phase` alongside `mag`** for `f1..f6` on the set-class / `name_pcs` path. (Unblocks
   Audiology consuming colour + chirality inputs instead of recomputing.)
2. Confirm prime form + bitmask are (or can be) returned by `set_class_info`.
3. *(Optional, larger)* a Representation-layer "interval/colour-content" descriptor.
4. *(Optional, research)* the complete general chirality above.

— Audiology
