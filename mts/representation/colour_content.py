"""Colour-content descriptor (Phase 5 — Audiology brief-15 Ask 3).

The two resultant-vector constructions behind Audiology's "somatic colour" wheels,
as render-agnostic numeric data. The engine owns the **resultant** (a 2D vector);
the consumer maps its angle → hue and its focus → saturation (the OKLCH encoding
stays at the display edge). Exposing the resultant — not just the raw components —
is what lets *other* systems compute the same surfaces (brief-15's north star).

Two resultants:

- **Interval-content (root-blind, transposition-invariant).** The five
  inversion-paired interval classes ic1..ic5 sit on a regular pentagon (ic_k at
  ``2π(k−1)/5`` from +x); the tritone (ic6) is **central** — it has no direction,
  but it still counts toward the total, so tritone-heavy sets pull toward the grey
  centre. The resultant is the interval-vector-weighted sum of the rim unit
  vectors, **normalized by the total interval count**, so ``focus ∈ [0,1]``: a set
  whose intervals are all one (non-tritone) class points fully at that rim with
  focus 1 (the five non-tritone dyad classes + the augmented triad), a mix greys
  toward centre. Inversional pairs collapse (major = minor, dom7 = m7♭5). Verified
  against brief-15's enumeration: all 4083 pc-sets (|S|≥2) land on exactly **185
  distinct wheel positions**.

- **Fifths-centroid (root-aware, transposition-variant).** Each pc placed at its
  circle-of-fifths angle ``(7p mod 12)·30°``, circular mean. This equals ``f5 / n``
  (a clean DFT identity), so its angle is ``arg(f5)`` and its focus ``|f5|/n`` —
  the diatonic/fifthiness centroid. Rotates under transposition (it carries
  absolute position, like the DFT phase).

**Unlike the clock/bracelet view, the rim geometry here is engine-fixed**, not the
renderer's choice — the resultant angle is the determination a consumer reads as
hue, so it must be canonical. Register-less (``spec_level="identity_only"``); the
hue/OKLCH mapping and any register → lightness stay the consumer's rendering.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from collections.abc import Iterable

from ..analysis.pcset_math import interval_vector
from ..core.bitmask import mask_from_pcs, pcs_from_mask
from ..core.setclass import dft_components

# Canonical rim: ic_k (k=1..5) at angle 2π(k−1)/5 from +x. Engine-fixed so every
# consumer computes the same hue; the tritone (ic6) is central (no entry here).
_RIM = tuple((math.cos(2 * math.pi * k / 5), math.sin(2 * math.pi * k / 5)) for k in range(5))
RIM_LAYOUT = "pentagon: ic1..ic5 at 2π(k-1)/5 from +x; tritone (ic6) central (no direction)"


@dataclass(frozen=True)
class ColourResultant:
    """A 2D resultant as render-agnostic data — map ``angle_radians`` → hue,
    ``focus`` → saturation. ``x``/``y`` are the normalized components (``focus`` is
    their length, in ``[0, 1]``); ``angle_radians`` is ``atan2(y, x)`` in (−π, π]."""

    x: float
    y: float
    angle_radians: float
    focus: float


@dataclass(frozen=True)
class ColourContentDescriptor:
    """Both colour resultants for a pitch-class set, plus the inputs + the fixed
    rim convention so a consumer can reproduce or re-map them."""

    spec_level: str  # always "identity_only" — pc-level, register-less
    interval_vector: list[int]
    interval_content: ColourResultant  # root-blind, transposition-INVARIANT
    fifths_centroid: ColourResultant  # root-aware, transposition-VARIANT (from f5)
    rim_layout: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _resultant(x: float, y: float) -> ColourResultant:
    return ColourResultant(
        x=round(x, 10) + 0.0,
        y=round(y, 10) + 0.0,
        angle_radians=math.atan2(y, x) if (x or y) else 0.0,
        focus=round(math.hypot(x, y), 10) + 0.0,
    )


def colour_content_descriptor(pcs: Iterable[int]) -> ColourContentDescriptor:
    """Build the colour-content descriptor for a pitch-class set.

    Accepts any iterable of pitch classes (mod 12, deduped). Raises ``ValueError``
    on an empty set — there is no colour without content.
    """

    mask = mask_from_pcs({int(pc) % 12 for pc in pcs})
    if mask == 0:
        raise ValueError("colour_content_descriptor needs at least one pitch class.")

    iv = interval_vector(pcs)  # [ic1..ic6]
    total = sum(iv)  # ALL interval content, incl. tritone (it pulls toward centre)
    if total:
        ix = sum(iv[k] * _RIM[k][0] for k in range(5)) / total
        iy = sum(iv[k] * _RIM[k][1] for k in range(5)) / total
    else:
        ix = iy = 0.0  # a single pc has no intervals → dead centre

    n = len(pcs_from_mask(mask))
    f5 = dft_components(mask)[5]
    fifths = _resultant(f5.real / n, f5.imag / n)

    return ColourContentDescriptor(
        spec_level="identity_only",
        interval_vector=list(iv),
        interval_content=_resultant(ix, iy),
        fifths_centroid=fifths,
        rim_layout=RIM_LAYOUT,
    )


__all__ = [
    "ColourResultant",
    "ColourContentDescriptor",
    "colour_content_descriptor",
    "RIM_LAYOUT",
]
