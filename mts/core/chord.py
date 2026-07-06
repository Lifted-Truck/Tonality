"""Chord definitions and utilities."""

from __future__ import annotations

from dataclasses import dataclass

from .bitmask import mask_from_pcs, validate_pc, is_subset
from .quality import ChordQuality


@dataclass(frozen=True)
class Chord:
    root_pc: int
    quality: ChordQuality
    pcs: tuple[int, ...]
    mask: int

    @classmethod
    def from_quality(cls, root_pc: int, quality: ChordQuality) -> "Chord":
        validate_pc(root_pc)
        pcs = tuple(quality.pcs_from_root(root_pc))
        mask = mask_from_pcs(pcs)
        return cls(root_pc=root_pc, quality=quality, pcs=pcs, mask=mask)


def chord_in_scale(chord: Chord, scale_mask: int) -> bool:
    return is_subset(chord.mask, scale_mask)
