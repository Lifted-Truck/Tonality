"""Helpers for symmetry detection."""

from __future__ import annotations

from .bitmask import rotate_mask


def mask_symmetry_order(mask: int) -> int:
    for step in range(1, 13):
        if rotate_mask(mask, step) == mask:
            return step
    return 12
