"""Shared pitch-class-set math for the analysis layer.

Single home for helpers that were previously duplicated across
``chord_analysis``/``scale_analysis`` (interval vector, reflection axes) and
``comparisons``/``summaries`` (compatibility roots). Everything here reduces
to the 12-bit mask space (4096 values), so results are cached once per
identity rather than recomputed per call.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from functools import lru_cache

from ..core.bitmask import (
    interval_vector_from_mask,
    is_subset,
    mask_from_pcs,
    pcs_from_mask,
    rotate_mask,
)
from ..core.bitmask import complement_mask
from ..core.quality import ChordQuality
from ..core.scale import Scale
from ..core.setclass import (
    dft_magnitudes,
    normal_order,
    prime_form,
    prime_form_mask,
    z_partner_mask,
)
from .results import ReflectionAxis, SetClassData


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


@lru_cache(maxsize=4096)
def _containing_roots_for_masks(container_mask: int, query_mask: int) -> tuple[int, ...]:
    return tuple(
        root
        for root in range(12)
        if is_subset(query_mask, rotate_mask(container_mask, root))
    )


def containing_roots(container_mask: int, query_mask: int) -> tuple[int, ...]:
    """Roots (0..11) where the catalog identity, transposed there, contains the query.

    The reverse question of :func:`compatibility_roots`: the container moves,
    the query stays absolute.
    """

    return _containing_roots_for_masks(container_mask, query_mask)


# The neo-Riemannian Tonnetz lattice: each pc placed by P5/M3/m3 axes from C.
# Shared by chord analysis (per-chord coordinates) and the Tonnetz descriptor
# (the full lattice + edge derivation) — one source of truth for the layout.
_TONNETZ_AXES = (
    (7, (1, 0, 0)),  # perfect fifth
    (4, (0, 1, 0)),  # major third
    (3, (0, 0, 1)),  # minor third
)


@lru_cache(maxsize=1)
def tonnetz_coordinates() -> dict[int, tuple[int, int, int]]:
    """Integer Tonnetz lattice coordinate of each pitch class (C at origin).

    Axes: x = perfect fifth (+7), y = major third (+4), z = minor third (+3).
    A spanning-tree assignment by BFS from C — fixed and deterministic.
    """

    coords: dict[int, tuple[int, int, int]] = {0: (0, 0, 0)}
    queue = deque([0])
    while queue and len(coords) < 12:
        pc = queue.popleft()
        base = coords[pc]
        for interval, delta in _TONNETZ_AXES:
            target = (pc + interval) % 12
            if target not in coords:
                coords[target] = tuple(base[i] + delta[i] for i in range(3))
                queue.append(target)
    return coords


def set_class_data(mask: int) -> SetClassData:
    """Set-class identity for a mask (Phase 3.5a).

    Built fresh per call (list fields stay unshared); the underlying core
    functions are mask-cached, so construction is cheap.
    """

    partner = z_partner_mask(mask)
    return SetClassData(
        normal_order=list(normal_order(mask)),
        prime_form=list(prime_form(mask)),
        prime_form_mask=prime_form_mask(mask),
        dft_magnitudes=list(dft_magnitudes(mask)),
        z_partner_prime_form=list(pcs_from_mask(partner)) if partner is not None else None,
        complement_prime_form=list(prime_form(complement_mask(mask))),
    )
