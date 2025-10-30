"""Bitmask utilities for pitch-class sets."""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def validate_pc(pc: int) -> int:
    if not 0 <= pc < 12:
        raise ValueError(f"Pitch class out of range: {pc}")
    return pc


def mask_from_pcs(pcs: Iterable[int]) -> int:
    mask = 0
    for pc in pcs:
        validate_pc(pc)
        mask |= 1 << pc
    return mask


def pcs_from_mask(mask: int) -> list[int]:
    return [pc for pc in range(12) if mask & (1 << pc)]


def is_subset(subset_mask: int, superset_mask: int) -> bool:
    return (subset_mask & superset_mask) == subset_mask


def rotate_mask(mask: int, semitones: int) -> int:
    semitones %= 12
    rotated = 0
    for pc in range(12):
        if mask & (1 << pc):
            rotated |= 1 << ((pc + semitones) % 12)
    return rotated


def transpose_pcs(pcs: Sequence[int], semitones: int) -> list[int]:
    return [validate_pc((pc + semitones) % 12) for pc in pcs]
