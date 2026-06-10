"""Scale analysis routines.

TODO:
    - Classify chirality and imperfect tones.
    - Provide hooks for bracelet/Tonnetz style visualisations.
    - Surface chord families that fit at each scale degree / interval.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..core.bitmask import mask_from_pcs
from ..core.scale import Scale
from ..core.symmetry import rotational_steps
from .pcset_math import interval_vector as _interval_vector
from .pcset_math import reflection_axes as _reflection_axes
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


def _normalize_degrees(degrees: Iterable[int]) -> list[int]:
    return sorted({int(pc) % 12 for pc in degrees})


def _step_pattern(degrees: Iterable[int]) -> list[int]:
    ordered = _normalize_degrees(degrees)
    if not ordered:
        return []
    pattern: list[int] = []
    for idx, pc in enumerate(ordered):
        nxt = ordered[(idx + 1) % len(ordered)]
        interval = (nxt - pc) % 12
        if idx == len(ordered) - 1:
            interval = (ordered[0] - pc) % 12
        if interval == 0:
            interval = 12
        pattern.append(interval)
    # Ensure the wrap-around interval is computed last
    pattern[-1] = (ordered[0] - ordered[-1]) % 12 or 12
    return pattern


def _modal_rotations(scale: Scale) -> list[ModeRotation]:
    if not scale.degrees:
        return []
    rotations: list[ModeRotation] = []
    degrees = list(scale.degrees)
    for mode_index, root in enumerate(degrees):
        rotated = sorted(((pc - root) % 12 for pc in degrees))
        pattern = _step_pattern(rotated)
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


def _symmetry_data(scale: Scale, step_pattern: list[int]) -> SymmetryData:
    if not step_pattern:
        return SymmetryData(
            rotational_order=0,
            rotational_steps=[],
            achiral=False,
            reflection_axes=[],
        )
    mask = scale.mask
    rotational_order = scale.symmetry_order
    reversed_pattern = list(reversed(step_pattern))
    achiral = any(
        reversed_pattern[shift:] + reversed_pattern[:shift] == step_pattern
        for shift in range(len(step_pattern))
    )
    reflection_axes = _reflection_axes(set(scale.degrees))
    return SymmetryData(
        rotational_order=rotational_order,
        rotational_steps=list(rotational_steps(mask)),
        achiral=achiral,
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
        symmetry = _symmetry_data(request.scale, step_pattern)

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
    )
