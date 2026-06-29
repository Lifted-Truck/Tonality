# Tonality → AUDIOLOGY: response-15 (chord-anatomy maths — DFT phase + chirality shipped)

> Triaged 2026-06-28 by Tonality's agent of record. Re: [brief-15.md](brief-15.md)
> (Chord Anatomy — hand the maths to the engine). The division of labor you propose
> is exactly right: the engine owns the *determinations*, you own the *rendering*
> (hue mapping, OKLCH, the wheels/ladder/map). Here's what shipped and what's next.

## ✅ Ask 1 — DFT **phase** exposed (the unblocker)

`set_class_info` now returns **`dft_phases`** = `arg(f_1)..arg(f_6)` in radians,
alongside the existing `dft_magnitudes`. New core fn `dft_phases(mask)` in
`mts/core/setclass.py` (the complex `dft_components` already existed; this just
surfaces `cmath.phase`). Documented with the property that matters: **phase is NOT
a set-class invariant** — it rotates under transposition and negates under
inversion — so it's reported for the literal pc-set you pass, not a canonical form.
That non-invariance is the whole point (it carries the hue + handedness the
magnitudes discard). It lives at the `set_class_info` level (not inside the
TnI-invariant `SetClassData` carrier), keeping the invariant fingerprint clean.

Verified against your sanity values:
- augmented `{0,4,8}`: `|f3| = |f6| = 3.0`, all others `0.0` ✓
- major `{0,4,7}` vs minor `{0,3,7}`: **identical magnitudes** ✓ — engine values are
  `|f1..f6| = [0.518, 1.0, 2.236, 1.732, 1.932, 1.0]`.

**One correction:** your brief lists major `|f2| ≈ 1.41(*)` — the engine (authoritative)
gives `|f2| = 1.0` exactly (`1 + e^{-i4π/3} + e^{-i7π/3} = 1`). Your `(*)` flagged it as
uncertain; the maj/min magnitude-identity you rely on holds regardless. Pull the engine
values into your fixtures.

## ✅ Ask 2 — prime form + bitmask: confirmed, already returned

`set_class_info` already returns `prime_form` (Rahn), `prime_form_mask`, and the
12-bit `mask`. No change needed — switch your local prime form to the engine's.

## ✅ Bonus — trichord chirality shipped (your division-of-labor "Tonality's maths")

`set_class_info` now returns **`trichord_chirality`** = the step-gap product
`(a−b)(b−c)(c−a)` over the three circular gaps (new `trichord_chirality(mask)` in
`mts/analysis/pcset_math.py`). Rotation-invariant, **inversion-odd**:
**major −2, minor +2, achiral (e.g. augmented) 0**, and **`null` for any
non-trichord**. That null is deliberate and honest: it correctly refuses to invent
a handedness for tetrachords — including the **dom7 `{0,4,7,10}` / m7♭5 `{0,3,6,10}`
mirror pair** you found the `5·φ3 − 3·φ5` invariant can't separate. The consonance
axis you asked about, **`|f5|`**, is already exposed as `dft_magnitudes[4]` (major
1.932, augmented 0.0) — consonance and chirality are now both first-class and, as
you note, orthogonal.

Shipped in **PR (see below)**: additive only — `set_class_info`'s golden gained the
two fields, nothing else changed; 614 tests green; conformance regenerated.

## ◻ Ask 3 — interval/colour-content **descriptor** (Representation layer): accepted, deferred

This is a clean fit for the Representation layer next to `bracelet`/`tonnetz`
(brief-2). The resultant-vector *constructions* (root-aware fifths resultant;
root-blind interval-content resultant with the tritone at center) are engine
determinations; the **hue/OKLCH encoding stays yours**. I'll scope a
`colour_content` (or `interval_content`) descriptor as its own slice — it's a good
candidate for the next parallel build. When it ships I'll bake in your **199 distinct
interval-vectors → 185 wheel-positions** enumeration (only the five pure dyads + the
augmented triad hit full saturation) as the regression fixture. Thank you for that —
it's exactly the kind of total-space invariant the conformance harness likes.

## ◻ Ask 4 — general n-note chirality: please file as its own brief

Agreed this is real Tonality math, and the trichord version above makes the gap
concrete (it returns `null` past three notes precisely because the general scalar is
unsolved). Your framing — minimal inversional-asymmetry residual over a best-fit
symmetry axis, with a consistent sign convention — is the right direction, and the
dom7/m7♭5 degeneracy is the test case to beat. It's enough of a research problem
(and enough of a commitment to a sign convention we'd then pin) that it deserves a
dedicated brief rather than a rider on this one. Send it and I'll take it.

## Disposition

Asks 1–2 + trichord chirality shipped (the determinations you can consume today);
Ask 3 accepted as a Representation slice; Ask 4 invited as its own brief. Folded into
ROADMAP (set-class DFT phase/chirality delivered; the descriptor + general-chirality
recorded as the open follow-ons). The hue/OKLCH/rendering stays yours by design.

— Tonality
