"""Scale models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .bitmask import mask_from_pcs, validate_pc
from .symmetry import mask_symmetry_order


@dataclass(frozen=True)
class Scale:
    name: str
    degrees: Tuple[int, ...]
    mask: int
    aliases: Tuple[str, ...] = ()

    @classmethod
    def from_degrees(
        cls, name: str, degrees: Iterable[int], aliases: Iterable[str] | None = None
    ) -> "Scale":
        normalized = tuple(sorted({validate_pc(int(pc) % 12) for pc in degrees}))
        mask = mask_from_pcs(normalized)
        alias_values = tuple(sorted({str(alias).strip() for alias in (aliases or []) if str(alias).strip()}))
        return cls(name=name, degrees=normalized, mask=mask, aliases=alias_values)

    def contains(self, pc: int) -> bool:
        validate_pc(pc)
        return bool(self.mask & (1 << pc))

    def transpose(self, semitones: int) -> "Scale":
        transposed_degrees = [((pc + semitones) % 12) for pc in self.degrees]
        return Scale.from_degrees(f"{self.name}+{semitones}", transposed_degrees, self.aliases)

    @property
    def symmetry_order(self) -> int:
        return mask_symmetry_order(self.mask)

    def pcs(self) -> List[int]:
        return list(self.degrees)

    def complementary_pcs(self) -> List[int]:
        return [pc for pc in range(12) if pc not in self.degrees]

    def __str__(self) -> str:
        pcs = ",".join(str(pc) for pc in self.degrees)
        if self.aliases:
            aliases = ",".join(self.aliases)
            return f"Scale(name={self.name}, degrees=[{pcs}], aliases=[{aliases}])"
        return f"Scale(name={self.name}, degrees=[{pcs}])"
