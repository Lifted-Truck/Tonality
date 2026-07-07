"""Rhythmic atoms: metric placement, syncopation, duration patterns (WS0).

The third and last Phase 4.6 Workstream 0 vocabulary: where notes fall in
the metric grid and how they relate to it — the atoms rhythm rules quantify
over. Same line discipline as :mod:`melodic`: a rhythm stream is **one
voice's** monophonic line (polyphonic rhythm is per-voice; pass ``voice=``).

**Beat unit** is derived from the time signature in effect at each note's
onset (the meter map handles changes): compound meters — numerator > 3 and
divisible by 3 — group three notated units into one felt beat (6/8 → the
dotted quarter, 1.5 quarter-note beats); simple meters use the notated unit
(4/4 → 1.0, 2/2 → 2.0). Definitional, like the step/skip/leap mapping —
not an empirical knob.

**Metric placement** classes an onset against that grid:

- ``downbeat`` — the bar line;
- ``beat`` — on a felt beat (non-downbeat);
- ``offbeat`` — on the half-beat subdivision;
- ``subdivision`` — anything finer or off-grid.

**Syncopation** is a precise predicate, not a vibe: a note is syncopated
when its onset's metric level is contradicted by its length —

- an ``offbeat``/``subdivision`` onset that sounds *through* the next beat
  line, or
- a non-downbeat ``beat`` onset that sounds *through* the next downbeat.

Downbeat onsets are never syncopated. Notes are judged against the
signature at their onset (a mid-note meter change does not retroactively
re-class the onset).

Duration patterns ship as the raw material: per-note ``duration_beats`` and
``ioi_to_next`` (inter-onset interval; ``None`` for the last note), plus the
line-level sequences. Pattern *mining* (which patterns recur) is Phase 4.5/
4.6 statistics territory, not this vocabulary layer.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .meter import TimeSignature
from .melodic import _line_events
from .sequence import Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..io.loaders import SwingFeelPriors

_EPS = 1e-9


def beat_unit_of(signature: TimeSignature) -> float:
    """The felt beat in quarter-note beats (compound meters beat in threes)."""

    notated = 4.0 / signature.denominator
    if signature.numerator > 3 and signature.numerator % 3 == 0:
        return 3.0 * notated
    return notated


@dataclass(frozen=True)
class RhythmicNoteAtoms:
    """One note's rhythmic atoms (times in quarter-note beats)."""

    onset: float
    duration_beats: float
    midi: int
    bar: int
    beat_in_bar: float
    beat_unit: float
    placement: str  # downbeat | beat | offbeat | subdivision
    is_syncopated: bool
    ioi_to_next: float | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class RhythmicAnalysis:
    """A line's rhythmic atoms: per-note detail plus line-level sequences."""

    voice: str | None
    notes: tuple[RhythmicNoteAtoms, ...]
    durations: tuple[float, ...]
    iois: tuple[float, ...]
    placements: tuple[str, ...]
    syncopation_count: int

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def _is_near_multiple(value: float, unit: float) -> bool:
    ratio = value / unit
    return abs(ratio - round(ratio)) < _EPS * 10


def analyze_rhythm(sequence: Sequence, *, voice: str | None = None) -> RhythmicAnalysis:
    """Rhythmic atoms for one line: placement, syncopation, durations, IOIs.

    Same extraction contract as :func:`analyze_melody`: explicit ``voice``,
    or a sequence carrying at most one voice; multi-voice without ``voice=``
    errors, as do overlapping notes (not a line).
    """

    events = _line_events(sequence, voice)
    onsets = [e.onset for e in events]
    iois = [b - a for a, b in zip(onsets, onsets[1:])]

    notes: list[RhythmicNoteAtoms] = []
    syncopation_count = 0
    for i, event in enumerate(events):
        position = sequence.metric_position(event.onset)
        unit = beat_unit_of(position.signature)
        pos = position.beat_in_bar
        bar_start = event.onset - pos

        if position.is_downbeat:
            placement = "downbeat"
        elif _is_near_multiple(pos, unit):
            placement = "beat"
        elif _is_near_multiple(pos, unit / 2.0):
            placement = "offbeat"
        else:
            placement = "subdivision"

        if placement == "downbeat":
            syncopated = False
        elif placement == "beat":
            next_downbeat = bar_start + position.signature.beats_per_bar
            syncopated = event.offset > next_downbeat + _EPS
        else:
            beats_in = int((pos + _EPS) // unit)
            next_beat_line = bar_start + (beats_in + 1) * unit
            syncopated = event.offset > next_beat_line + _EPS
        syncopation_count += syncopated

        notes.append(
            RhythmicNoteAtoms(
                onset=event.onset,
                duration_beats=event.duration,
                midi=event.pitch.midi,
                bar=position.bar,
                beat_in_bar=pos,
                beat_unit=unit,
                placement=placement,
                is_syncopated=syncopated,
                ioi_to_next=iois[i] if i < len(iois) else None,
            )
        )

    return RhythmicAnalysis(
        voice=voice,
        notes=tuple(notes),
        durations=tuple(e.duration for e in events),
        iois=tuple(iois),
        placements=tuple(n.placement for n in notes),
        syncopation_count=syncopation_count,
    )


# --- swing feel (symbolically-encoded timing only) -----------------------------------
#
# Swing usually lives in performance timing and is gone from quantized MIDI or
# notation; this estimator reads the cases where it *is* in the symbolic data
# (triplet-position or otherwise unevenly encoded onsets). It measures where
# each two-way beat division places its interior onset: the division fraction
# is (interior onset - beat line) / beat unit — 0.5 is straight, 2/3 is
# triplet swing (2:1), 0.75 is dotted shuffle (3:1), below 0.5 is reversed
# (short-long). Only beats with exactly one interior onset count (a beat
# divided in three or four is not a swing pair); classification thresholds
# are a versioned empirical prior (``data/swing_feel.json``), cited in the
# result, and too few divisions raises rather than guessing.


@dataclass(frozen=True)
class SwingDivision:
    """One two-way beat division: the evidence behind the feel estimate."""

    onset: float  # the interior onset, in absolute beats
    fraction: float  # its position within the beat, in (0, 1)


@dataclass(frozen=True)
class SwingAnalysis:
    """A line's swing-feel estimate, with per-division evidence.

    ``feel`` is one of ``straight`` / ``swung`` / ``reversed`` / ``mixed``
    (mixed = the fractions are too dispersed to claim one feel).
    ``swing_ratio`` is long:short, derived from ``mean_fraction``
    (0.5 → 1.0 straight, 2/3 → 2.0 triplet swing, 0.75 → 3.0 dotted).
    """

    voice: str | None
    feel: str
    mean_fraction: float
    swing_ratio: float
    fraction_stddev: float
    divisions: tuple[SwingDivision, ...]
    divided_beats: int  # beats with any interior onset (incl. ineligible)
    eligible_divisions: int  # beats with exactly one interior onset
    prior_version: str

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return dataclasses.asdict(self)


def analyze_swing(
    sequence: Sequence,
    *,
    voice: str | None = None,
    priors: "SwingFeelPriors | None" = None,
) -> SwingAnalysis:
    """Estimate a line's swing feel from its two-way beat divisions.

    Same line contract as :func:`analyze_rhythm`. Raises ``ValueError`` when
    the line has fewer than the prior's ``min_divisions`` eligible two-way
    divisions — too little evidence is not a feel.
    """

    events = _line_events(sequence, voice)
    if priors is None:
        from ..io.loaders import load_swing_priors

        priors = load_swing_priors()

    interior_by_beat: dict[tuple[int, int], list[SwingDivision]] = {}
    for event in events:
        position = sequence.metric_position(event.onset)
        unit = beat_unit_of(position.signature)
        beat_index = int((position.beat_in_bar + _EPS) // unit)
        pos_in_beat = position.beat_in_bar - beat_index * unit
        if pos_in_beat < _EPS or unit - pos_in_beat < _EPS:
            continue  # on a beat line: not an interior onset
        interior_by_beat.setdefault((position.bar, beat_index), []).append(
            SwingDivision(onset=event.onset, fraction=pos_in_beat / unit)
        )

    divisions = sorted(
        (group[0] for group in interior_by_beat.values() if len(group) == 1),
        key=lambda d: d.onset,
    )
    if len(divisions) < priors.min_divisions:
        raise ValueError(
            f"Only {len(divisions)} two-way beat division(s) found; the "
            f"{priors.version} prior needs {priors.min_divisions} to claim a "
            "feel (too little evidence is not a feel)."
        )

    fractions = [d.fraction for d in divisions]
    mean = sum(fractions) / len(fractions)
    stddev = math.sqrt(sum((f - mean) ** 2 for f in fractions) / len(fractions))
    if stddev > priors.consistency_tolerance:
        feel = "mixed"
    elif abs(mean - 0.5) <= priors.straight_tolerance:
        feel = "straight"
    elif mean > 0.5:
        feel = "swung"
    else:
        feel = "reversed"

    return SwingAnalysis(
        voice=voice,
        feel=feel,
        mean_fraction=mean,
        swing_ratio=mean / (1.0 - mean),
        fraction_stddev=stddev,
        divisions=tuple(divisions),
        divided_beats=len(interior_by_beat),
        eligible_divisions=len(divisions),
        prior_version=priors.version,
    )


__all__ = [
    "RhythmicAnalysis",
    "RhythmicNoteAtoms",
    "SwingAnalysis",
    "SwingDivision",
    "analyze_rhythm",
    "analyze_swing",
    "beat_unit_of",
]
