"""Demonstrate dynamic functional mapping generation."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_chord_qualities, load_scales
from mts.theory.functions import (
    DEFAULT_FEATURES_MAJOR,
    DEFAULT_FEATURES_MINOR,
    FEATURE_ALTERED_DOMINANT,
    FEATURE_LEADING_TONE,
    FEATURE_LYDIAN_EXTENSIONS,
    FEATURE_POWER_DYADS,
    FEATURE_RAISED_SIXTH,
    generate_functions_for_scale,
)
from mts.theory import functions as fn


def _print_functions(title: str, generated):
    print(f"\n{title}")
    for func in generated:
        tags = f" [{', '.join(func.tags)}]" if func.tags else ""
        intervals = ",".join(str(iv) for iv in func.intervals)
        print(
            f"  degree={func.degree_pc:2d} "
            f"quality={func.chord_quality:>8} "
            f"label={func.modal_label:>8} "
            f"role={func.role:<11} "
            f"intervals=[{intervals}]"
            f"{tags}"
        )


def main() -> None:
    scales = load_scales()
    qualities = load_chord_qualities()

    ionian = scales["Ionian"]
    aeolian = scales["Natural Minor"]

    major_basic = generate_functions_for_scale(
        ionian,
        qualities,
        templates=fn.TEMPLATES_MAJOR,
        enabled_features=DEFAULT_FEATURES_MAJOR,
        include_nondiatic=False,
    )

    major_extended_features = set(DEFAULT_FEATURES_MAJOR) | {
        FEATURE_LYDIAN_EXTENSIONS,
        FEATURE_ALTERED_DOMINANT,
        FEATURE_POWER_DYADS,
    }
    major_extended = generate_functions_for_scale(
        ionian,
        qualities,
        templates=fn.TEMPLATES_MAJOR,
        enabled_features=major_extended_features,
        include_nondiatic=True,
    )

    minor_aeolian = generate_functions_for_scale(
        aeolian,
        qualities,
        templates=fn.TEMPLATES_MINOR,
        enabled_features=set(DEFAULT_FEATURES_MINOR) - {FEATURE_LEADING_TONE},
        include_nondiatic=False,
    )

    minor_harmonic = generate_functions_for_scale(
        aeolian,
        qualities,
        templates=fn.TEMPLATES_MINOR,
        enabled_features=set(DEFAULT_FEATURES_MINOR)
        | {FEATURE_ALTERED_DOMINANT, FEATURE_RAISED_SIXTH},
        include_nondiatic=True,
    )

    _print_functions("Ionian (diatonic feature set)", major_basic)
    _print_functions("Ionian (extended + altered)", major_extended)
    _print_functions("Natural Minor (strict Aeolian)", minor_aeolian)
    _print_functions("Natural Minor (harmonic/melodic options)", minor_harmonic)


if __name__ == "__main__":
    main()
