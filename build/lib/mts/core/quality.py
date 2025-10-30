"""Chord quality definitions."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .bitmask import mask_from_pcs, validate_pc


@dataclass(frozen=True)
class ChordQuality:
    name: str
    intervals: tuple[int, ...]
    tensions: tuple[int, ...]
    mask: int

    @classmethod
    def from_intervals(
        cls, name: str, intervals: Sequence[int], tensions: Iterable[int] | None = None
    ) -> "ChordQuality":
        normalized_intervals = tuple(sorted({int(iv) % 12 for iv in intervals}))
        normalized_tensions = tuple(sorted({int(tv) % 12 for tv in (tensions or [])}))
        for iv in normalized_intervals:
            validate_pc(iv)
        for tv in normalized_tensions:
            validate_pc(tv)
        mask = mask_from_pcs(normalized_intervals)
        return cls(name=name, intervals=normalized_intervals, tensions=normalized_tensions, mask=mask)

    def pcs_from_root(self, root_pc: int) -> list[int]:
        validate_pc(root_pc)
        return [((root_pc + iv) % 12) for iv in self.intervals]
