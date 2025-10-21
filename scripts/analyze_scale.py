"""CLI stub for scale analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales
from mts.analysis import ScaleAnalysisRequest, analyze_scale
from mts.core.enharmonics import pc_from_name


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_symmetry(symmetry: dict[str, object]) -> None:
    _print_section("Symmetry")
    print(f"  rotational order: {symmetry.get('rotational_order')}")
    steps = symmetry.get("rotational_steps", [])
    if steps:
        print(f"  rotational steps: {', '.join(str(step) for step in steps)}")
    print(f"  achiral: {symmetry.get('achiral')}")
    axes = symmetry.get("reflection_axes", [])
    if axes:
        print("  reflection axes:")
        for axis in axes:
            center = axis.get("center")
            axis_type = axis.get("type")
            print(f"    - {axis_type} axis @ {center}")
    else:
        print("  reflection axes: none")


def _print_intervals(intervals: dict[str, object]) -> None:
    _print_section("Interval Summary")
    print(f"  cardinality: {intervals.get('cardinality')}")
    print(f"  interval vector: {intervals.get('interval_vector')}")
    if intervals.get("largest_step") is not None:
        print(f"  largest step: {intervals['largest_step']}")
    if intervals.get("smallest_step") is not None:
        print(f"  smallest step: {intervals['smallest_step']}")
    print(f"  semitone steps: {intervals.get('semitone_count')}")
    print(f"  whole-tone steps: {intervals.get('tone_count')}")
    print(f"  tritone pairs: {intervals.get('tritone_pairs')}")
    ic_map = intervals.get("ic_map")
    if isinstance(ic_map, dict):
        print("  interval class counts:")
        for ic, count in sorted(ic_map.items(), key=lambda item: int(item[0])):
            print(f"    ic{ic}: {count}")


def _print_modes(modes: list[dict[str, object]]) -> None:
    _print_section("Modes")
    for mode in modes:
        name = f"Mode {mode.get('mode_index', '?')}"
        root = mode.get("root_pc")
        degrees = mode.get("degrees")
        pattern = mode.get("step_pattern")
        vector = mode.get("interval_vector")
        print(f"  {name} (root pc {root})")
        print(f"    degrees: {degrees}")
        print(f"    step pattern: {pattern}")
        print(f"    interval vector: {vector}")


def _print_report(report: dict[str, object]) -> None:
    print(f"Scale: {report['scale_name']}")
    print(f"Degrees: {report['degrees']} (cardinality {report.get('cardinality')})")
    print(f"Mask: {report.get('mask')} (binary {report.get('mask_binary')})")
    if "note_names" in report:
        print(f"Note names: {report['note_names']}")
    print(f"Step pattern: {report.get('step_pattern')}")
    print(f"Interval vector: {report.get('interval_vector')}")
    if "intervals" in report:
        _print_intervals(report["intervals"])
    if "symmetry" in report:
        _print_symmetry(report["symmetry"])
    if "modes" in report:
        _print_modes(report["modes"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a scale using placeholder analytics.")
    parser.add_argument(
        "scale",
        help=(
            "Scale name from the database (e.g., Ionian). "
            "Use scripts/check_chord_scale_compat.py --list-scales to inspect options."
        ),
    )
    parser.add_argument("--tonic", help="Optional tonic note to spell the scale (e.g., C, F#, Eb)")
    parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                        help="Enharmonic spelling preference when tonic provided.")
    parser.add_argument("--key-sig", type=int, default=None,
                        help="Optional circle-of-fifths index (-7..+7) for spelling bias.")
    parser.add_argument("--no-note-names", action="store_true",
                        help="Suppress note-name output even if tonic is specified.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the raw analysis payload as pretty-printed JSON.")
    args = parser.parse_args()

    scales = load_scales()
    if args.scale not in scales:
        parser.error(f"Unknown scale {args.scale!r}")

    tonic_pc = pc_from_name(args.tonic) if args.tonic else None
    request = ScaleAnalysisRequest(
        scale=scales[args.scale],
        tonic_pc=tonic_pc,
        spelling=args.spelling,
        key_signature=args.key_sig,
        include_note_names=not args.no_note_names,
    )
    report = analyze_scale(request)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    _print_report(report)


if __name__ == "__main__":
    main()
