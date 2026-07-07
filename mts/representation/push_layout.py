"""Push-3 pad layout — a render-agnostic pc grid descriptor (Phase 5).

Numeric only: ``grid()`` returns the pitch class at each 8x8 pad. Painting the
pads (ANSI, hardware LEDs, pixels) is an edge concern — the terminal renderer
lives at the CLI edge (``mts/cli/push_grid.py``). Moved here from the removed
``mts/layouts/`` package (RE-6a).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.bitmask import validate_pc


@dataclass(frozen=True)
class Push3Layout:
    row_offset: int = 5
    root_pc: int = 0

    def __post_init__(self) -> None:
        validate_pc(self.root_pc)

    def grid(self) -> list[list[int]]:
        rows: list[list[int]] = []
        for row in range(8):
            rows.append([((self.root_pc + column + row * self.row_offset) % 12) for column in range(8)])
        return rows
