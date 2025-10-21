"""Chord definitions and utilities."""

from __future__ import annotations

from dataclasses import dataclass

from .bitmask import mask_from_pcs, validate_pc, is_subset
from .enharmonics import primary_name
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

    def spelled(self, prefer: str = "auto") -> list[str]:
        # TODO: integrate advanced spelling logic based on key signature
        return [primary_name(pc) for pc in self.pcs]


def chord_in_scale(chord: Chord, scale_mask: int) -> bool:
    return is_subset(chord.mask, scale_mask)


def chord_degree_labels(chord: Chord, scale_root_pc: int, scale_degrees: list[int]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for pc in chord.pcs:
        relative = (pc - scale_root_pc) % 12
        if relative in scale_degrees:
            label = str(scale_degrees.index(relative) + 1)
        else:
            label = "(out)"
        labels[primary_name(pc)] = label
    return labels
