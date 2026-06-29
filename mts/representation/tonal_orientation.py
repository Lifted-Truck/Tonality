"""Pitch-space tonal orientation (Audiology brief-17).

A continuous fifths-space orientation angle for a **voicing** (actual sounding
pitches) — the **register-aware** sibling of the pc-level fifths centroid
(``arg(f5)`` / `colour_content`'s ``fifths_centroid``). Each sounding pitch is
placed at its circle-of-fifths angle and summed with a register weight; the
argument of the resultant is an angle that **varies continuously with voicing**
(inversion, registral spread, and doublings all move it) — for a
voicing-responsive hue. The colour mapping stays the consumer's.

This is Chew's spiral-array "center of effect" projected to the fifths circle.
Properties (verified): it **reduces to ``arg(f5)``** for a neutral closed voicing
(uniform weights, one note per pc); it **rotates predictably** under transposition
(the whole resultant turns by ``2π·7·t/12`` under ``T_t`` — so it is an absolute
orientation whose *relative* value across voicings is the hue signal); and with
``octave_decay < 1`` it weights the bass more, so inversion / spread shift the angle.

The weight is **relative to the bass** (``octave_decay`` per octave above the
lowest sounding pitch), which keeps it transposition-stable; absolute register is
a separate axis the consumer maps to lightness (brief-15). ``octave_decay`` is the
one aesthetic knob, left to the caller (default ``1.0`` = uniform). Register-
required: it reads actual pitches and cannot be computed from a register-less
identity (the cardinal rule) — a pc-set has no voicing to orient.
"""

from __future__ import annotations

import cmath
import dataclasses
import math
from dataclasses import dataclass
from collections.abc import Iterable


@dataclass(frozen=True)
class TonalOrientation:
    """A voicing's fifths-space orientation as render-agnostic data — map
    ``angle_radians`` → hue, ``focus`` → saturation. ``angle_radians`` is in
    (−π, π]; ``focus`` is the resultant length / total weight, in ``[0, 1]``."""

    angle_radians: float
    focus: float
    note_count: int
    octave_decay: float
    spec_level: str  # always "registered" — it requires actual pitches

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def tonal_orientation(
    midi_pitches: Iterable[int], *, octave_decay: float = 1.0
) -> TonalOrientation:
    """Continuous fifths-space orientation angle of a voicing (Audiology brief-17).

    ``midi_pitches`` are the sounding MIDI note numbers (register-bearing — this is
    a voicing, not a pc-set). ``octave_decay`` is the weight multiplier per octave
    above the bass (``1.0`` = uniform; ``< 1`` weights the bass more, so inversion
    and spread move the angle). Raises ``ValueError`` on an empty voicing or a
    non-positive ``octave_decay``.
    """

    pitches = [int(m) for m in midi_pitches]
    if not pitches:
        raise ValueError("tonal_orientation needs at least one sounding pitch.")
    if octave_decay <= 0.0:
        raise ValueError("octave_decay must be positive.")

    bass = min(pitches)
    resultant = 0j
    total_weight = 0.0
    for midi in pitches:
        weight = octave_decay ** ((midi - bass) / 12.0)
        # circle-of-fifths angle of the pitch class (so uniform → arg(f5)).
        resultant += weight * cmath.exp(2j * math.pi * 7 * (midi % 12) / 12)
        total_weight += weight

    angle = math.atan2(resultant.imag, resultant.real) if abs(resultant) else 0.0
    focus = abs(resultant) / total_weight
    return TonalOrientation(
        angle_radians=round(angle, 10) + 0.0,
        focus=round(focus, 10) + 0.0,
        note_count=len(pitches),
        octave_decay=float(octave_decay),
        spec_level="registered",
    )


__all__ = ["TonalOrientation", "tonal_orientation"]
