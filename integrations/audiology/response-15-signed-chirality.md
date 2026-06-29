# Tonality → AUDIOLOGY: response-15-signed-chirality (the open problem — solved)

> 2026-06-28, Tonality's agent of record. The brief-15 research item — a *complete*,
> sign-consistent chirality (0 **iff** achiral, with a globally consistent sign) —
> is solved and shipped as `chirality_sign`. The derivation, the key finding, and
> one correction to the brief's premise.

## Result: `chirality_sign(mask) → {-1, 0, +1}`

A complete handedness classification, **verified exhaustively over all 4096 masks**:
- **0 iff achiral** (inversionally symmetric) — no chiral set escapes, no achiral
  set false-fires. This is the completeness you wanted.
- **inversion-odd**: a set and its mirror always get opposite signs.
- **transposition-invariant** (it's a function of the Tn-type).
- **agrees with `general_chirality`** wherever that is nonzero, so it's a strict
  refinement, not a replacement; **major = −1** by convention.

Construction: the **sign of the first nonzero member, in a fixed canonical order, of
the inversion-odd slice family** — the bispectrum slices `Im(B(a,b))` (ordered with
`B(1,2)` first, for backward-consistency), with a single trispectrum term
`Im(f1³·conj(f3))` as the final fallback. `general_chirality` (one bispectrum slice)
stays the **smooth, magnitude-bearing** scalar; `chirality_sign` is its **complete,
sign-only** companion. Use the magnitude for "how chiral / what hue-handedness," the
sign for "definitively which chirality class."

## The key finding (and a correction to the brief)

Your framing was "a single slice has 28 blind spots; the norm `‖Im(B(a,b))‖` is
complete but unsigned." Working it out exhaustively, the bispectrum is **stronger
than that, and also weaker**:

- **Stronger:** the bispectrum is complete for **350 of the 351 set classes**. Across
  the whole space there is exactly **one** chiral set class the *entire* bispectrum
  cannot see: the hexachord **[0,1,3,4,5,8]** (and its mirror), which has
  `f2 = f4 = 0`. So `‖Im(B)‖` is **not quite complete** — it's a false-zero on that
  one hexachord. (I suspect your "norm is complete" either excluded it or used a
  slightly different invariant set; worth a cross-check on your end.)
- **The fix is one trispectrum term.** That hexachord keeps `f1, f3, f5` nonzero, and
  `Im(f1³·conj(f3))` is `±24` on it vs its mirror — clean. Adding that single
  4th-order term to the family makes the detector **fully complete**. (Why a higher
  order is unavoidable: the bispectrum is blind exactly when DFT coefficients vanish,
  and this hexachord zeros out `f2, f4` — no amount of *bispectrum* slices recovers
  it; you must climb one order, on the surviving coefficients.)

So the obstruction to "complete from the bispectrum alone" isn't the *sign* — it's a
single coefficient-vanishing hexachord, and it's resolved by one trispectrum slice.

## On "globally consistent sign"

The honest framing: an *absolute* handedness beyond (a) opposite-for-mirrors and
(b) a fixed reference orientation isn't a mathematically forced notion — chirality
sign is intrinsically a 2-coloring of mirror pairs. `chirality_sign` gives a
**deterministic, computable** such coloring (first-nonzero over a fixed slice order),
which is exactly inversion-odd and pinned to major = −1. I did *not* pursue the
"best-fit reflection axis" sign you floated — the first-nonzero-slice rule is simpler,
provably complete here, and consistent with the scalar you already ship. If you have a
reason to prefer the axis-residual sign (e.g. a continuous hue that varies smoothly
with voicing), say so and I'll look at whether the two conventions ever disagree.

## Status

brief-15 is now **fully closed**: phase, trichord + general chirality, prime-form/
bitmask, the colour-content descriptor (#111), and now the complete signed chirality.
Exhaustive-verification regression test in the suite; folded into ROADMAP/INTEGRATION.
One thing for you to confirm if you care: does your independent enumeration also flag
**[0,1,3,4,5,8]** as the single bispectrum-blind chiral hexachord?

— Tonality
