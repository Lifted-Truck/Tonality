"""Helpers for symmetry detection.

Both helpers are cached over the full 12-bit mask space (4096 values), so
symmetry lookups in analysis hot paths cost a dict probe after first use.
"""

from __future__ import annotations

from functools import lru_cache

from .bitmask import rotate_mask


@lru_cache(maxsize=4096)
def rotational_period(mask: int) -> int:
    """The set's **rotational period**: the smallest transposition (1..12) that maps
    it to itself. This equals ``12 ÷ (rotational symmetry-group order)``, so
    **12 means no nontrivial rotational symmetry** (a single pc, a major triad) and
    a smaller value means more symmetry (augmented → 4, dim7 → 3, whole-tone → 2).

    (Renamed from ``mask_symmetry_order`` 2026-06-30: it was named like a
    symmetry-group order but always returned the period; the value is unchanged.)
    """
    for step in range(1, 13):
        if rotate_mask(mask, step) == mask:
            return step
    return 12


@lru_cache(maxsize=4096)
def rotational_steps(mask: int) -> tuple[int, ...]:
    """Transpositions in 1..11 that map the mask onto itself, or (12,) if none."""
    steps = tuple(step for step in range(1, 12) if rotate_mask(mask, step) == mask)
    return steps or (12,)
