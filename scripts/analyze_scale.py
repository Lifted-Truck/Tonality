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

from mts.io.loaders import load_scales, load_chord_qualities
from mts.analysis import ScaleAnalysisRequest, analyze_scale
from mts.analysis.builders import SESSION_SCALE_CONTEXT
from mts.analysis.results import ScaleAnalysisResult, ScaleIntervalSummary, SymmetryData, ModeRotation
from mts.core.enharmonics import pc_from_name
from mts.context import DisplayContext
from mts.context.result_format import format_scale_analysis


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_symmetry(symmetry: SymmetryData) -> None:
    _print_section("Symmetry")
    print(f"  rotational order: {symmetry.rotational_order}")
    if symmetry.rotational_steps:
        print(f"  rotational steps: {', '.join(str(step) for step in symmetry.rotational_steps)}")
    print(f"  achiral: {symmetry.achiral}")
    if symmetry.reflection_axes:
        print("  reflection axes:")
        for axis in symmetry.reflection_axes:
            print(f"    - {axis.type} axis @ {axis.center}")
    else:
        print("  reflection axes: none")


def _print_intervals(intervals: ScaleIntervalSummary) -> None:
    _print_section("Interval Summary")
    print(f"  cardinality: {intervals.cardinality}")
    print(f"  interval vector: {intervals.interval_vector}")
    if intervals.largest_step is not None:
        print(f"  largest step: {intervals.largest_step}")
    if intervals.smallest_step is not None:
        print(f"  smallest step: {intervals.smallest_step}")
    print(f"  semitone steps: {intervals.semitone_count}")
    print(f"  whole-tone steps: {intervals.tone_count}")
    print(f"  tritone pairs: {intervals.tritone_pairs}")
    if intervals.ic_map:
        print("  interval class counts:")
        for ic, count in sorted(intervals.ic_map.items(), key=lambda item: int(item[0])):
            print(f"    ic{ic}: {count}")


def _print_modes(modes: list[ModeRotation]) -> None:
    _print_section("Modes")
    for mode in modes:
        print(f"  Mode {mode.mode_index} (root pc {mode.root_pc})")
        print(f"    degrees: {mode.degrees}")
        print(f"    step pattern: {mode.step_pattern}")
        print(f"    interval vector: {mode.interval_vector}")


def _print_report(report: ScaleAnalysisResult, ctx: DisplayContext, *, note_names: bool = True) -> None:
    print(f"Scale: {report.scale_name}")
    print(f"Degrees: {report.degrees} (cardinality {report.cardinality})")
    print(f"Mask: {report.mask} (binary {report.mask_binary})")
    if note_names:
        print(f"Note names: {format_scale_analysis(report, ctx).note_names}")
    print(f"Step pattern: {report.step_pattern}")
    print(f"Interval vector: {report.interval_vector}")
    if report.intervals is not None:
        _print_intervals(report.intervals)
    if report.symmetry is not None:
        _print_symmetry(report.symmetry)
    if report.modes is not None:
        _print_modes(report.modes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a scale using placeholder analytics.")
    # TODO: Accept inline definitions like "[0,2,3]=MyScale" so analysis can create/named scales on the fly.
    parser.add_argument(
        "scale",
        nargs="?",
        help=(
            "Scale name from the database (e.g., Ionian). "
            "Use scripts/check_chord_scale_compat.py --list-scales to inspect options."
        ),
    )
    parser.add_argument("--list-scales", action="store_true", help="List available scales and exit.")
    parser.add_argument("--list-qualities", action="store_true", help="List available chord qualities and exit.")
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
    if args.list_scales:
        print("Available scales:")
        for name in sorted(scales.keys()):
            print(" -", name)
        return
    if args.list_qualities:
        print("Available chord qualities:")
        for name in sorted(load_chord_qualities().keys()):
            print(" -", name)
        return
    if args.scale is None:
        parser.error("Scale name required unless using --list-scales/--list-qualities.")

    if args.scale not in scales:
        parser.error(f"Unknown scale {args.scale!r}. Use --list-scales to inspect options.")

    scale = scales[args.scale]
    context = SESSION_SCALE_CONTEXT.get(scale.name)
    if context:
        scope = context.get("scope", "abstract").capitalize()
        tokens = ", ".join(context.get("tokens", []))
        line = f"Context: {scope}"
        if tokens:
            line += f" ({tokens})"
        print(line)

    tonic_pc = pc_from_name(args.tonic) if args.tonic else None

    ctx = DisplayContext()
    ctx.set("spelling", args.spelling, layer="cli")
    if args.key_sig is not None:
        ctx.set("key_signature", args.key_sig, layer="cli")
    if tonic_pc is not None:
        ctx.set("tonic_pc", tonic_pc, layer="cli")

    request = ScaleAnalysisRequest(scale=scale, tonic_pc=tonic_pc)
    report = analyze_scale(request)
    if args.json:
        payload = report.to_dict()
        payload["display"] = format_scale_analysis(report, ctx).to_dict()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    _print_report(report, ctx, note_names=not args.no_note_names)


if __name__ == "__main__":
    main()
