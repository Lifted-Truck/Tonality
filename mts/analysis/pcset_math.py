"""Shared pitch-class-set math for the analysis layer.

Single home for helpers that were previously duplicated across
``chord_analysis``/``scale_analysis`` (interval vector, reflection axes) and
``comparisons``/``summaries`` (compatibility roots). Everything here reduces
to the 12-bit mask space (4096 values), so results are cached once per
identity rather than recomputed per call.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from ..core.bitmask import (
    interval_vector_from_mask,
    is_subset,
    mask_from_pcs,
    pcs_from_mask,
    rotate_mask,
)
from ..core.quality import ChordQuality
from ..core.scale import Scale
from .results import ReflectionAxis


def interval_vector(pcs: Iterable[int]) -> list[int]:
    """Interval-class vector of *pcs* (order and duplicates ignored, mod 12)."""

    return list(interval_vector_from_mask(mask_from_pcs({int(pc) % 12 for pc in pcs})))


@lru_cache(maxsize=4096)
def _reflection_axes_for_mask(mask: int) -> tuple[ReflectionAxis, ...]:
    pcs = set(pcs_from_mask(mask))
    axes: list[ReflectionAxis] = []
    for axis in range(12):
        reflected_pitch = {((2 * axis - pc) % 12) for pc in pcs}
        if reflected_pitch == pcs:
            axes.append(ReflectionAxis(type="pitch", center=axis))
        reflected_between = {((2 * axis + 1 - pc) % 12) for pc in pcs}
        if reflected_between == pcs:
            axes.append(ReflectionAxis(type="between", center=(axis + 0.5) % 12))
    unique_axes: list[ReflectionAxis] = []
    seen: set[tuple[str, float]] = set()
    for ax in axes:
        key = (ax.type, ax.center)
        if key in seen:
            continue
        seen.add(key)
        unique_axes.append(ax)
    return tuple(unique_axes)


def reflection_axes(pcs: set[int]) -> list[ReflectionAxis]:
    """Reflective symmetry axes of a pitch-class set.

    ``ReflectionAxis`` is frozen, so the cached instances are shared safely.
    """

    if not pcs:
        return []
    return list(_reflection_axes_for_mask(mask_from_pcs(pcs)))


@lru_cache(maxsize=4096)
def _compatibility_roots_for_masks(scale_mask: int, quality_mask: int) -> tuple[int, ...]:
    return tuple(
        root
        for root in range(12)
        if is_subset(rotate_mask(quality_mask, root), scale_mask)
    )


def compatibility_roots(scale: Scale, quality: ChordQuality) -> tuple[int, ...]:
    """Return root positions (0..11) where the chord quality fits inside the scale."""

    return _compatibility_roots_for_masks(scale.mask, quality.mask)
