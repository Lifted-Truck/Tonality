"""Helpers for symmetry detection.

Both helpers are cached over the full 12-bit mask space (4096 values), so
symmetry lookups in analysis hot paths cost a dict probe after first use.
"""

from __future__ import annotations

from functools import lru_cache

from .bitmask import rotate_mask


@lru_cache(maxsize=4096)
def mask_symmetry_order(mask: int) -> int:
    for step in range(1, 13):
        if rotate_mask(mask, step) == mask:
            return step
    return 12


@lru_cache(maxsize=4096)
def rotational_steps(mask: int) -> tuple[int, ...]:
    """Transpositions in 1..11 that map the mask onto itself, or (12,) if none."""
    steps = tuple(step for step in range(1, 12) if rotate_mask(mask, step) == mask)
    return steps or (12,)
