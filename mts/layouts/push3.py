"""Push-3 layout mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.bitmask import validate_pc


@dataclass(frozen=True)
class Push3Layout:
    row_offset: int = 5
    root_pc: int = 0

    def __post_init__(self) -> None:
        validate_pc(self.root_pc)

    def grid(self) -> List[List[int]]:
        rows: List[List[int]] = []
        for row in range(8):
            rows.append([((self.root_pc + column + row * self.row_offset) % 12) for column in range(8)])
        return rows
