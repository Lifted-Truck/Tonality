"""Typed results for the pattern layer (gap C slice 1)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass


@dataclass(frozen=True)
class PatternOccurrence:
    """One located occurrence, with the evidence of *how* it matched.

    ``iois`` are the actual inter-onset intervals spanned — a rhythm-free match
    surfaces its time-warp rather than hiding it. ``degrees`` / ``moves`` carry
    the per-level binding (present only for the level that produced them).
    """

    voice: str | None
    start_beat: float
    end_beat: float
    midis: list[int]
    onsets: list[float]
    iois: list[float]
    degrees: list[int] | None
    moves: list[str] | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class PatternMatches:
    """Every occurrence of one pattern in one sequence (plural, evidence-carrying).

    ``voices_skipped`` names any voice line the matcher could not linearize
    (simultaneous onsets) — skipped loudly, never silently. ``key`` echoes the
    key a degree-level match was conditional on (``None`` otherwise).
    """

    pattern_name: str
    pattern_version: str
    pitch_level: str
    time_level: str
    key: tuple[int, str] | None
    count: int
    occurrences: list[PatternOccurrence]
    voices_skipped: list

    def to_dict(self) -> dict:
        return {
            "pattern_name": self.pattern_name,
            "pattern_version": self.pattern_version,
            "pitch_level": self.pitch_level,
            "time_level": self.time_level,
            "key": list(self.key) if self.key is not None else None,
            "count": self.count,
            "occurrences": [o.to_dict() for o in self.occurrences],
            "voices_skipped": list(self.voices_skipped),
        }


__all__ = ["PatternOccurrence", "PatternMatches"]
