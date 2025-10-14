"""Chord quality definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .bitmask import mask_from_pcs, validate_pc


@dataclass(frozen=True)
class ChordQuality:
    name: str
    intervals: Tuple[int, ...]
    tensions: Tuple[int, ...]
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

    def pcs_from_root(self, root_pc: int) -> List[int]:
        validate_pc(root_pc)
        return [((root_pc + iv) % 12) for iv in self.intervals]
