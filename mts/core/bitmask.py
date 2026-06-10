"""Bitmask utilities for pitch-class sets."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from functools import lru_cache


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


def invert_mask(mask: int, index: int = 0) -> int:
    """The inversion I_n: each pc maps to (index - pc) mod 12."""
    inverted = 0
    for pc in range(12):
        if mask & (1 << pc):
            inverted |= 1 << ((index - pc) % 12)
    return inverted


def complement_mask(mask: int) -> int:
    """The pitch classes absent from the set."""
    return ~mask & 0xFFF


def multiply_mask(mask: int, multiplier: int) -> int:
    """The multiplication M_m: each pc maps to (pc * multiplier) mod 12.

    Only multipliers coprime with 12 (1, 5, 7, 11) are bijections; M5/M7 are
    the classic cycle-of-fourths/fifths mappings (e.g. M5 sends the diatonic
    scale to a chromatic cluster). Non-coprime multipliers are allowed but
    collapse pitch classes.
    """
    multiplied = 0
    for pc in range(12):
        if mask & (1 << pc):
            multiplied |= 1 << ((pc * multiplier) % 12)
    return multiplied


@lru_cache(maxsize=4096)
def interval_vector_from_mask(mask: int) -> tuple[int, int, int, int, int, int]:
    """Interval-class vector of a PC-set mask.

    There are only 4096 possible masks, so each vector is computed at most
    once per process; the cache makes repeated identity analysis O(1).
    """
    pcs = pcs_from_mask(mask)
    vector = [0, 0, 0, 0, 0, 0]
    for i, a in enumerate(pcs):
        for b in pcs[i + 1 :]:
            diff = (b - a) % 12
            ic = diff if diff <= 6 else 12 - diff
            vector[ic - 1] += 1
    return (vector[0], vector[1], vector[2], vector[3], vector[4], vector[5])
