"""Scale analysis placeholder routines.

TODO:
    - Compute interval vectors, step patterns, and modal rotations.
    - Detect symmetry properties (e.g., rotational order, palindromic structure).
    - Classify chirality and imperfect tones.
    - Provide hooks for bracelet/Tonnetz style visualisations.
    - Surface chord families that fit at each scale degree / interval.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass

from ..core.bitmask import mask_from_pcs, rotate_mask
from ..core.enharmonics import SpellingPref, name_for_pc
from ..core.scale import Scale


@dataclass
class ScaleAnalysisRequest:
    """Container for ad hoc scale analysis instructions."""

    scale: Scale
    tonic_pc: int | None = None
    spelling: SpellingPref = "auto"
    key_signature: int | None = None
    include_modes: bool = True
    include_symmetry: bool = True
    include_interval_report: bool = True
    include_note_names: bool = True


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


def _interval_vector(degrees: Iterable[int]) -> list[int]:
    ordered = _normalize_degrees(degrees)
    vector = [0] * 6
    for a, b in itertools.combinations(ordered, 2):
        diff = (b - a) % 12
        step = diff if diff <= 6 else 12 - diff
        if step == 0 or step > 6:
            continue
        vector[step - 1] += 1
    return vector


def _modal_rotations(scale: Scale) -> list[dict[str, object]]:
    if not scale.degrees:
        return []
    rotations: list[dict[str, object]] = []
    degrees = list(scale.degrees)
    for mode_index, root in enumerate(degrees):
        rotated = sorted(((pc - root) % 12 for pc in degrees))
        pattern = _step_pattern(rotated)
        vector = _interval_vector(rotated)
        rotations.append(
            {
                "mode_index": mode_index,
                "root_pc": root,
                "degrees": rotated,
                "mask": mask_from_pcs(rotated),
                "step_pattern": pattern,
                "interval_vector": vector,
            }
        )
    return rotations


def _reflection_axes(pcs: set[int]) -> list[dict[str, object]]:
    axes: list[dict[str, object]] = []
    if not pcs:
        return axes
    for axis in range(12):
        reflected_pitch = {((2 * axis - pc) % 12) for pc in pcs}
        if reflected_pitch == pcs:
            axes.append({"type": "pitch", "center": axis})
        reflected_between = {((2 * axis + 1 - pc) % 12) for pc in pcs}
        if reflected_between == pcs:
            axes.append({"type": "between", "center": (axis + 0.5) % 12})
    unique_axes: list[dict[str, object]] = []
    seen: set[tuple[str, float | int]] = set()
    for axis in axes:
        key = (axis["type"], axis["center"])
        if key in seen:
            continue
        seen.add(key)
        unique_axes.append(axis)
    return unique_axes


def _symmetry_data(scale: Scale, step_pattern: list[int]) -> dict[str, object]:
    if not step_pattern:
        return {
            "rotational_order": 0,
            "rotational_steps": [],
            "achiral": False,
            "reflection_axes": [],
        }
    mask = scale.mask
    rotational_steps = [step for step in range(1, 12) if rotate_mask(mask, step) == mask]
    rotational_order = scale.symmetry_order
    reversed_pattern = list(reversed(step_pattern))
    achiral = any(
        reversed_pattern[shift:] + reversed_pattern[:shift] == step_pattern
        for shift in range(len(step_pattern))
    )
    reflection_axes = _reflection_axes(set(scale.degrees))
    return {
        "rotational_order": rotational_order,
        "rotational_steps": rotational_steps or [12],
        "achiral": achiral,
        "reflection_axes": reflection_axes,
    }


def _interval_summary(step_pattern: list[int], interval_vector: list[int]) -> dict[str, object]:
    if not step_pattern:
        return {
            "cardinality": 0,
            "interval_vector": interval_vector,
            "largest_step": None,
            "smallest_step": None,
            "semitone_count": 0,
            "tone_count": 0,
            "tritone_pairs": interval_vector[5] if interval_vector else 0,
            "ic_map": {str(idx + 1): count for idx, count in enumerate(interval_vector)},
        }
    ic_map = {str(idx + 1): count for idx, count in enumerate(interval_vector)}
    return {
        "cardinality": len(step_pattern),
        "interval_vector": interval_vector,
        "largest_step": max(step_pattern),
        "smallest_step": min(step_pattern),
        "semitone_count": step_pattern.count(1),
        "tone_count": step_pattern.count(2),
        "tritone_pairs": interval_vector[5] if len(interval_vector) > 5 else 0,
        "ic_map": ic_map,
    }


def analyze_scale(request: ScaleAnalysisRequest) -> dict[str, object]:
    """Return a basic analysis dictionary for the given scale."""

    normalized_degrees = _normalize_degrees(request.scale.degrees)
    step_pattern = _step_pattern(normalized_degrees)
    interval_vector = _interval_vector(normalized_degrees)

    report: dict[str, object] = {
        "scale_name": request.scale.name,
        "degrees": list(request.scale.degrees),
        "cardinality": len(request.scale.degrees),
        "step_pattern": step_pattern,
        "interval_vector": interval_vector,
        "mask": request.scale.mask,
        "mask_binary": "".join("1" if request.scale.mask & (1 << pc) else "0" for pc in range(12)),
    }
    if request.include_note_names and request.tonic_pc is not None:
        report["note_names"] = [
            name_for_pc((request.tonic_pc + degree) % 12, prefer=request.spelling, key_signature=request.key_signature)
            for degree in request.scale.degrees
        ]
    if request.include_modes:
        report["modes"] = _modal_rotations(request.scale)
    if request.include_symmetry:
        report["symmetry"] = _symmetry_data(request.scale, step_pattern)
    if request.include_interval_report:
        report["intervals"] = _interval_summary(step_pattern, interval_vector)
    return report
