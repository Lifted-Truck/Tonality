"""Scale analysis placeholder routines.

TODO:
    - Compute interval vectors, step patterns, and modal rotations.
    - Detect symmetry properties (e.g., rotational order, palindromic structure).
    - Classify chirality and imperfect tones.
    - Provide hooks for bracelet/Tonnetz style visualisations.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass

from ..core.bitmask import mask_from_pcs
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


def _step_pattern(degrees: Iterable[int]) -> list[int]:
    ordered = sorted({int(pc) % 12 for pc in degrees})
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
    ordered = sorted({int(pc) % 12 for pc in degrees})
    vector = [0] * 6
    for a, b in itertools.combinations(ordered, 2):
        diff = (b - a) % 12
        step = diff if diff <= 6 else 12 - diff
        if step == 0 or step > 6:
            continue
        vector[step - 1] += 1
    return vector


def _modal_rotations(scale: Scale) -> list[dict[str, object]]:
    rotations: list[dict[str, object]] = []
    degrees = list(scale.degrees)
    for root in degrees:
        rotated = sorted(((pc - root) % 12 for pc in degrees))
        rotations.append(
            {
                "root_pc": root,
                "degrees": rotated,
                "mask": mask_from_pcs(rotated),
            }
        )
    return rotations


def _symmetry_data(scale: Scale, step_pattern: list[int]) -> dict[str, object]:
    order = scale.symmetry_order
    # Determine if pattern is palindromic under rotation (achiral)
    reversed_pattern = list(reversed(step_pattern))
    achiral = False
    for shift in range(len(step_pattern)):
        rotated = reversed_pattern[shift:] + reversed_pattern[:shift]
        if rotated == step_pattern:
            achiral = True
            break
    return {
        "rotational_order": order,
        "achiral": achiral,
    }


def analyze_scale(request: ScaleAnalysisRequest) -> dict[str, object]:
    """Return a basic analysis dictionary for the given scale."""

    step_pattern = _step_pattern(request.scale.degrees)
    interval_vector = _interval_vector(request.scale.degrees)

    report: dict[str, object] = {
        "scale_name": request.scale.name,
        "degrees": list(request.scale.degrees),
        "step_pattern": step_pattern,
        "interval_vector": interval_vector,
        "mask_binary": "".join("1" if pc in request.scale.degrees else "0" for pc in range(12)),
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
        report["intervals"] = {
            "unique_degrees": len(set(request.scale.degrees)),
            "interval_vector": interval_vector,
        }
    return report
