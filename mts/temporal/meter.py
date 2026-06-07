"""Meter: time signatures, bars, beats-in-bar, and downbeats.

Built on the same quarter-note-beat time axis as :mod:`mts.temporal.tempo`. A
:class:`TimeSignature` knows how many quarter-note beats fill a bar; a
:class:`MeterMap` is a piecewise-constant sequence of signatures (changes are
anchored to *bar* indices) and converts an absolute beat position into a
:class:`MetricPosition` (bar, beat-in-bar, downbeat).
"""

from __future__ import annotations

from dataclasses import dataclass

_EPS = 1e-9


@dataclass(frozen=True)
class TimeSignature:
    """A time signature, e.g. ``TimeSignature(6, 8)``."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator <= 0 or self.denominator <= 0:
            raise ValueError("Time signature numerator/denominator must be positive.")

    @property
    def beats_per_bar(self) -> float:
        """Bar length in quarter-note beats (e.g. 6/8 -> 3.0, 4/4 -> 4.0)."""

        return self.numerator * (4.0 / self.denominator)


@dataclass(frozen=True)
class MetricPosition:
    """Where an absolute beat falls in the metric grid."""

    bar: int               # 0-based bar index
    beat_in_bar: float     # 0.0 == downbeat
    signature: TimeSignature
    is_downbeat: bool


@dataclass(frozen=True)
class MeterChange:
    """A time signature taking effect at bar index ``bar`` (0-based)."""

    bar: int
    signature: TimeSignature


@dataclass(frozen=True)
class MeterMap:
    """A piecewise-constant meter. Frozen and hashable."""

    changes: tuple[MeterChange, ...]

    def __post_init__(self) -> None:
        if not self.changes:
            raise ValueError("MeterMap needs at least one meter change.")
        if self.changes[0].bar != 0:
            raise ValueError("MeterMap must define a signature at bar 0.")
        bars = [c.bar for c in self.changes]
        if bars != sorted(bars) or len(bars) != len(set(bars)):
            raise ValueError("MeterMap changes must be sorted by distinct bar.")

    @classmethod
    def constant(cls, numerator: int, denominator: int) -> "MeterMap":
        """A single, unchanging time signature."""

        return cls((MeterChange(0, TimeSignature(numerator, denominator)),))

    def _segments(self) -> list[tuple[float, int, TimeSignature, int | None]]:
        """(start_beat, start_bar, signature, next_bar) for each meter segment."""

        segments: list[tuple[float, int, TimeSignature, int | None]] = []
        beat = 0.0
        for i, change in enumerate(self.changes):
            next_bar = self.changes[i + 1].bar if i + 1 < len(self.changes) else None
            segments.append((beat, change.bar, change.signature, next_bar))
            if next_bar is not None:
                beat += (next_bar - change.bar) * change.signature.beats_per_bar
        return segments

    def metric_position(self, beat: float) -> MetricPosition:
        """Convert an absolute quarter-note beat into a :class:`MetricPosition`."""

        if beat < -_EPS:
            raise ValueError("beat must be non-negative.")
        for start_beat, start_bar, signature, next_bar in self._segments():
            bpb = signature.beats_per_bar
            segment_beats = None if next_bar is None else (next_bar - start_bar) * bpb
            if segment_beats is None or beat < start_beat + segment_beats - _EPS:
                rel = beat - start_beat
                bars_in = int((rel + _EPS) // bpb)
                beat_in_bar = rel - bars_in * bpb
                if beat_in_bar < _EPS:
                    beat_in_bar = 0.0
                return MetricPosition(
                    bar=start_bar + bars_in,
                    beat_in_bar=beat_in_bar,
                    signature=signature,
                    is_downbeat=beat_in_bar < _EPS,
                )
        raise AssertionError("unreachable: final segment is open-ended")


__all__ = ["TimeSignature", "MetricPosition", "MeterChange", "MeterMap"]
