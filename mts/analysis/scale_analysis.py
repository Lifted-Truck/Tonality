"""Scale analysis: request in, typed ``ScaleAnalysisResult`` out.

Modes, symmetry (rotational + reflective), interval summary, and set-class
data for a scale — numeric/PC only (spelling renders at the display edge).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..core.bitmask import mask_from_pcs
from ..core.scale import Scale
from ..core.symmetry import rotational_steps
from .pcset_math import interval_vector as _interval_vector
from .pcset_math import reflection_axes as _reflection_axes
from .pcset_math import set_class_data
from .results import (
    ModeRotation,
    ScaleAnalysisResult,
    ScaleIntervalSummary,
    SymmetryData,
)


@dataclass
class ScaleAnalysisRequest:
    """Container for ad hoc scale analysis instructions."""

    scale: Scale
    tonic_pc: int | None = None
    include_modes: bool = True
    include_symmetry: bool = True
    include_interval_report: bool = True
    include_set_class: bool = True


def _normalize_degrees(degrees: Iterable[int]) -> list[int]:
    return sorted({int(pc) % 12 for pc in degrees})


def _ascending_steps(degrees: Iterable[int]) -> list[int]:
    """Successive semitone gaps around the scale, starting from the LOWEST pc
    (root-anchored). Used for modal rotations, which pre-rotate each mode so its
    root becomes pc 0 — there the lowest pc *is* the mode's root, so this yields
    that mode's own ascending pattern (Ionian W-W-H-W-W-W-H, Dorian W-H-W-W-W-H-W,
    …, each distinct)."""
    ordered = _normalize_degrees(degrees)
    if not ordered:
        return []
    return [
        (ordered[(i + 1) % len(ordered)] - ordered[i]) % 12 or 12
        for i in range(len(ordered))
    ]


def _step_pattern(degrees: Iterable[int]) -> list[int]:
    """Transposition-INVARIANT step signature (issue #205, resolution (a)): the
    lexicographically-minimal rotation of the cyclic ascending-step sequence, so
    the value is a pure shape descriptor — identical across all 12 transpositions,
    a sibling of ``interval_vector``. It is deliberately **not** tonic-relative:
    the supplied ``tonic_pc`` does not rotate it (the tonic-relative reading is
    ``degrees``; each mode's root-anchored pattern lives in the ``modes`` list).
    The old form anchored at the numerically-smallest pc — an artifact of 12-TET
    numbering that made it neither invariant nor tonic-anchored."""
    steps = _ascending_steps(degrees)
    if not steps:
        return []
    return min(steps[i:] + steps[:i] for i in range(len(steps)))


def _modal_rotations(scale: Scale) -> list[ModeRotation]:
    if not scale.degrees:
        return []
    rotations: list[ModeRotation] = []
    degrees = list(scale.degrees)
    for mode_index, root in enumerate(degrees):
        rotated = sorted(((pc - root) % 12 for pc in degrees))
        pattern = _ascending_steps(rotated)
        vector = _interval_vector(rotated)
        rotations.append(
            ModeRotation(
                mode_index=mode_index,
                root_pc=root,
                degrees=rotated,
                mask=mask_from_pcs(rotated),
                step_pattern=pattern,
                interval_vector=vector,
            )
        )
    return rotations


def _symmetry_data(scale: Scale) -> SymmetryData:
    # No empty-set special case: core's convention applies (the empty set is
    # trivially invariant — period 1, every step; the old hardcoded period 0
    # disagreed with core and the exported set-class table).
    mask = scale.mask
    reflection_axes = _reflection_axes(set(scale.degrees))
    return SymmetryData(
        rotational_period=scale.rotational_period,
        rotational_steps=list(rotational_steps(mask)),
        # achiral iff a reflection axis exists — the single definition shared
        # with chord_analysis (RE-6d), not a second step-pattern palindrome
        # computation (verified identical across all 4096 masks).
        achiral=bool(reflection_axes),
        reflection_axes=reflection_axes,
    )


def _interval_summary(step_pattern: list[int], interval_vector: list[int]) -> ScaleIntervalSummary:
    if not step_pattern:
        return ScaleIntervalSummary(
            cardinality=0,
            interval_vector=interval_vector,
            largest_step=None,
            smallest_step=None,
            semitone_count=0,
            tone_count=0,
            tritone_pairs=interval_vector[5] if interval_vector else 0,
            ic_map={str(idx + 1): count for idx, count in enumerate(interval_vector)},
        )
    ic_map = {str(idx + 1): count for idx, count in enumerate(interval_vector)}
    return ScaleIntervalSummary(
        cardinality=len(step_pattern),
        interval_vector=interval_vector,
        largest_step=max(step_pattern),
        smallest_step=min(step_pattern),
        semitone_count=step_pattern.count(1),
        tone_count=step_pattern.count(2),
        tritone_pairs=interval_vector[5] if len(interval_vector) > 5 else 0,
        ic_map=ic_map,
    )


def analyze_scale(request: ScaleAnalysisRequest) -> ScaleAnalysisResult:
    """Return a typed analysis result for the given scale."""

    normalized_degrees = _normalize_degrees(request.scale.degrees)
    step_pattern = _step_pattern(normalized_degrees)
    interval_vector = _interval_vector(normalized_degrees)

    modes: list[ModeRotation] | None = None
    if request.include_modes:
        modes = _modal_rotations(request.scale)

    symmetry: SymmetryData | None = None
    if request.include_symmetry:
        symmetry = _symmetry_data(request.scale)

    intervals: ScaleIntervalSummary | None = None
    if request.include_interval_report:
        intervals = _interval_summary(step_pattern, interval_vector)

    return ScaleAnalysisResult(
        scale_name=request.scale.name,
        tonic_pc=request.tonic_pc,
        degrees=list(request.scale.degrees),
        cardinality=len(request.scale.degrees),
        step_pattern=step_pattern,
        interval_vector=interval_vector,
        mask=request.scale.mask,
        mask_binary="".join(
            "1" if request.scale.mask & (1 << pc) else "0" for pc in range(12)
        ),
        modes=modes,
        symmetry=symmetry,
        intervals=intervals,
        set_class=set_class_data(request.scale.mask) if request.include_set_class else None,
    )
