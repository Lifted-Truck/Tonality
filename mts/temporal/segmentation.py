"""Segmentation + harmonic rhythm: deriving the identity stream from events.

A :class:`Sequence` is a stream of overlapping notes; segmentation collapses it
into a sequence of :class:`Segment`s — maximal spans over which the sounding
**pitch-class set is constant**. Each segment reduces to an identity key, which
:func:`~mts.analysis.equivalence.interpret_chord` can name — the full
core-data-model chain across time: events → realization → key → name.

Segmentation here is by the *literal* sounding PC set: every note entering or
leaving that changes the set starts a new segment (melody/passing tones included).
Harmonic (chord-level) segmentation that filters non-harmonic tones by metric
salience is a future refinement; this is the honest, well-defined baseline.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..analysis.equivalence import interpret_chord
from ..analysis.results import ChordInterpretations
from ..core.bitmask import mask_from_pcs
from ..core.realization import Realization
from .sequence import Sequence

_EPS = 1e-9


@dataclass(frozen=True)
class Segment:
    """A span over which the sounding pitch-class set is constant."""

    start: float
    end: float
    pcs: tuple[int, ...]
    mask: int
    realization: Realization  # representative voicing (sounding pitches mid-span)

    @property
    def duration_beats(self) -> float:
        return self.end - self.start

    def interpret(self) -> ChordInterpretations:
        """Name this segment's identity via :func:`interpret_chord`."""

        return interpret_chord(self.pcs)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class HarmonicRhythm:
    """Summary of how quickly the harmony (identity stream) changes."""

    segment_count: int
    mean_duration_beats: float
    mean_duration_seconds: float
    changes_per_bar: float
    durations_beats: list[float]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def segment(sequence: Sequence) -> list[Segment]:
    """Partition ``sequence`` into stable-pitch-class-set segments.

    Silent spans are dropped (not represented as segments). Adjacent spans with
    the same PC set are merged, so a held harmony under a moving doubling stays
    one segment.
    """

    events = sequence.events
    if not events:
        return []

    boundaries = sorted({e.onset for e in events} | {e.offset for e in events})

    raw: list[tuple[float, float, tuple[int, ...]]] = []
    for start, end in zip(boundaries, boundaries[1:]):
        if end - start <= _EPS:
            continue
        sounding = sequence.sounding_at((start + end) / 2.0)
        if not sounding:
            continue  # silence
        pcs = tuple(sorted({e.pitch.pc for e in sounding}))
        if raw and raw[-1][2] == pcs and abs(raw[-1][1] - start) <= _EPS:
            raw[-1] = (raw[-1][0], end, pcs)  # merge contiguous same-PC span
        else:
            raw.append((start, end, pcs))

    segments: list[Segment] = []
    for start, end, pcs in raw:
        realization = sequence.realization_at((start + end) / 2.0)
        assert realization is not None  # non-silent by construction
        segments.append(Segment(start, end, pcs, mask_from_pcs(pcs), realization))
    return segments


def harmonic_rhythm(sequence: Sequence) -> HarmonicRhythm:
    """Compute harmonic-rhythm metrics from the segmented identity stream.

    ``changes_per_bar`` counts harmony *changes* — segment boundaries, i.e.
    ``segment_count - 1`` (RE-3g: it used to count segments, so a one-chord
    piece reported a nonzero "change" rate). Uses the time signature in
    effect at the start (constant meter assumed for this single scalar).
    """

    segments = segment(sequence)
    count = len(segments)
    durations = [s.duration_beats for s in segments]
    mean_beats = sum(durations) / count if count else 0.0
    seconds = [
        sequence.seconds_at(s.end) - sequence.seconds_at(s.start) for s in segments
    ]
    mean_seconds = sum(seconds) / count if count else 0.0

    beats_per_bar = sequence.meter.changes[0].signature.beats_per_bar
    total_beats = sequence.duration_beats
    total_bars = total_beats / beats_per_bar if beats_per_bar > 0 else 0.0
    changes = max(0, count - 1)
    changes_per_bar = changes / total_bars if total_bars > _EPS else 0.0

    return HarmonicRhythm(
        segment_count=count,
        mean_duration_beats=mean_beats,
        mean_duration_seconds=mean_seconds,
        changes_per_bar=changes_per_bar,
        durations_beats=durations,
    )


__all__ = ["Segment", "HarmonicRhythm", "segment", "harmonic_rhythm"]
