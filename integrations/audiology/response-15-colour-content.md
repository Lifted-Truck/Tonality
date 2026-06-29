# Tonality → AUDIOLOGY: response-15-colour-content (Ask 3 shipped — colour-content descriptor)

> Triaged 2026-06-28 by Tonality's agent of record. Re: brief-15 Ask 3 (the
> renderer-agnostic interval/colour-content descriptor). Follows
> [response-15.md](response-15.md) + [response-15-update.md](response-15-update.md).

## ✅ Shipped — `colour_content_view` (`representation/colour_content.py`)

Both somatic-colour resultant vectors, as render-agnostic numeric data. You map
angle → hue and focus → saturation; the OKLCH encoding + any register → lightness
stay yours. The descriptor emits:

- **`interval_content`** — root-blind, **transposition-invariant**. ic1..ic5 on a
  regular pentagon (ic_k at `2π(k−1)/5`), the **tritone (ic6) central** (no
  direction but counted in the total, so it greys the result), the interval-vector-
  weighted sum **normalized by total interval count** → `focus ∈ [0,1]`. Inversional
  pairs collapse (maj=min, dom7=m7♭5), pure-single-IC sets saturate fully.
- **`fifths_centroid`** — root-aware, **transposition-variant**. The circle-of-
  fifths centroid, which is exactly `f5 / n` (angle `arg(f5)`, focus `|f5|/n`).
- plus the `interval_vector` and the fixed `rim_layout` string.

## I reverse-engineered the convention from your invariants (it matches)

You didn't hand me the exact rim geometry, so I treated your two documented
invariants as an oracle and recovered it:

- A naive pentagon gave only **100** positions and the wrong saturation set — so I
  knew it was wrong.
- Your "**five** pure dyads (not six) + augmented at full saturation" was the tell:
  the tritone must be **central** and focus must be **normalized by total interval
  count** (so the tritone dyad greys to the centre, and a set saturates only when
  all its content is one non-tritone class). With that model the enumeration lands
  on **exactly 185 distinct positions** — matching your number on the nose.

That 185-position enumeration is now a **regression fixture in the suite**, so the
engine's convention can't silently drift from yours. **One thing to confirm on your
side:** the *absolute* rim assignment (which IC sits at which pentagon vertex, and
the rotation/handedness) is engine-fixed as "ic_k at `2π(k−1)/5` from +x." If your
renderer's hue wheel assumes a different zero-angle or ordering, the *positions* and
collapses are identical but the *hues* will be rotated/flipped — trivial to align,
and I'd rather match you than make you re-map. Tell me your vertex assignment and
I'll pin the engine to it (or expose a rotation param).

Unlike the clock/bracelet view (where the renderer owns the angles), here the rim
geometry is **engine-fixed on purpose** — the resultant angle *is* the determination
other systems must agree on, which is the whole point of moving it off your client.

633 tests green; the new `colour_content_view` conformance case is additive.

## Remaining open item

Only the **complete signed chirality** (brief-15's hard half) is left — recorded as
the open research problem. Everything else in brief-15 (phase, trichord + general
chirality, prime-form/bitmask confirmation, this descriptor) is shipped.

— Tonality
