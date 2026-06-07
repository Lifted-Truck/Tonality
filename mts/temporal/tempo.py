"""Tempo: mapping musical time (quarter-note beats) to wall-clock seconds.

The temporal layer's canonical time unit is the **quarter-note beat** (a float;
1.0 == one quarter note), matching MIDI/DAW convention. BPM is quarter notes per
minute. A :class:`TempoMap` is a piecewise-constant tempo curve: a list of tempo
changes, each effective from its beat until the next.
"""

from __future__ import annotations

from dataclasses import dataclass

_EPS = 1e-9


@dataclass(frozen=True)
class TempoChange:
    """A tempo that takes effect at ``beat`` (in quarter-note beats)."""

    beat: float
    bpm: float


@dataclass(frozen=True)
class TempoMap:
    """A piecewise-constant tempo curve. Frozen and hashable."""

    changes: tuple[TempoChange, ...]

    def __post_init__(self) -> None:
        if not self.changes:
            raise ValueError("TempoMap needs at least one tempo change.")
        if self.changes[0].beat > _EPS:
            raise ValueError("TempoMap must define a tempo at beat 0.")
        beats = [c.beat for c in self.changes]
        if beats != sorted(beats):
            raise ValueError("TempoMap changes must be sorted by beat.")
        if any(c.bpm <= 0 for c in self.changes):
            raise ValueError("Tempo (bpm) must be positive.")

    @classmethod
    def constant(cls, bpm: float) -> "TempoMap":
        """A single, unchanging tempo."""

        return cls((TempoChange(0.0, bpm),))

    def bpm_at(self, beat: float) -> float:
        """The tempo in effect at ``beat``."""

        current = self.changes[0].bpm
        for change in self.changes:
            if change.beat <= beat + _EPS:
                current = change.bpm
            else:
                break
        return current

    def seconds_at(self, beat: float) -> float:
        """Wall-clock seconds elapsed from beat 0 to ``beat`` (integrated)."""

        if beat <= _EPS:
            return 0.0
        total = 0.0
        changes = self.changes
        for i, change in enumerate(changes):
            start = change.beat
            end = changes[i + 1].beat if i + 1 < len(changes) else None
            if end is None or beat <= end + _EPS:
                total += (beat - start) * (60.0 / change.bpm)
                break
            total += (end - start) * (60.0 / change.bpm)
        return total


__all__ = ["TempoChange", "TempoMap"]
