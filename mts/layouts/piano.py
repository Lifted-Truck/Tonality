"""Piano layout placeholder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PianoLayout:
    root_pc: int = 0

    def keys(self) -> List[int]:
        # TODO: implement piano key mapping aligned with GUI keyboard visualization
        return list(range(12))
