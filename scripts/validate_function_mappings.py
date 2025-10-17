"""Utility to sanity-check function mappings against scale pitch classes."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, List

from pathlib import Path

# Ensure the repository root is on sys.path when running as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.core.bitmask import is_subset, mask_from_pcs
from mts.core.scale import Scale
from mts.io.loaders import load_function_mappings, load_scales


@dataclass
class FunctionCheckResult:
    mode: str
    modal_label: str
    degree_pc: int
    chord_quality: str
    chord_pcs: List[int]
    missing_pcs: List[int]
    scale_name: str


def chord_pcs_from_mapping(degree_pc: int, intervals: Iterable[int]) -> List[int]:
    return [((degree_pc + interval) % 12) for interval in intervals]


def ensure_scale(scales: dict[str, Scale], name: str, fallback_degrees: Iterable[int]) -> Scale:
    if name in scales:
        return scales[name]
    scale = Scale.from_degrees(name, fallback_degrees)
    scales[name] = scale
    return scale


def evaluate_mode(mode: str, scale: Scale, scale_name: str) -> List[FunctionCheckResult]:
    results: List[FunctionCheckResult] = []
    scale_mask = scale.mask
    for mapping in load_function_mappings(mode):
        chord_pcs = chord_pcs_from_mapping(mapping.degree_pc, mapping.intervals)
        chord_mask = mask_from_pcs(chord_pcs)
        if not is_subset(chord_mask, scale_mask):
            missing = [pc for pc in chord_pcs if not scale.contains(pc)]
            results.append(
                FunctionCheckResult(
                    mode=mode,
                    modal_label=mapping.modal_label,
                    degree_pc=mapping.degree_pc,
                    chord_quality=mapping.chord_quality,
                    chord_pcs=chord_pcs,
                    missing_pcs=missing,
                    scale_name=scale_name,
                )
            )
    return results


def main() -> int:
    scales = load_scales()
    ionian = ensure_scale(scales, "Ionian", [0, 2, 4, 5, 7, 9, 11])
    aeolian = ensure_scale(scales, "Aeolian", [0, 2, 3, 5, 7, 8, 10])

    major_failures = evaluate_mode("major", ionian, ionian.name)
    minor_failures = evaluate_mode("minor", aeolian, aeolian.name)

    if not major_failures and not minor_failures:
        print("All function mappings fit within their respective scales.")
        return 0

    def render(failure: FunctionCheckResult) -> str:
        chord = ",".join(str(pc) for pc in sorted(failure.chord_pcs))
        missing = ",".join(str(pc) for pc in sorted(failure.missing_pcs))
        return (
            f"[{failure.mode}] {failure.modal_label} "
            f"(degree_pc={failure.degree_pc}, quality={failure.chord_quality}) "
            f"-> chord_pcs=[{chord}] missing_from_scale=[{missing}] "
            f"(scale={failure.scale_name})"
        )

    if major_failures:
        print("Major mode mismatches:")
        for failure in major_failures:
            print("  " + render(failure))
    if minor_failures:
        print("Minor mode mismatches:")
        for failure in minor_failures:
            print("  " + render(failure))

    return 1


if __name__ == "__main__":
    sys.exit(main())
