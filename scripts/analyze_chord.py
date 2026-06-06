"""CLI helper for chord analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_chord_qualities, load_scales
from mts.core.chord import Chord
from mts.core.enharmonics import pc_from_name
from mts.analysis import ChordAnalysisRequest, analyze_chord
from mts.analysis.builders import SESSION_CHORD_CONTEXT
from mts.analysis.results import ChordAnalysisResult
from mts.analysis.voicings import suggest_voicings
from mts.core.enharmonics import SpellingPref


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_overview(report: ChordAnalysisResult) -> None:
    print(f"Chord: {report.quality} (root pc {report.root_pc})")
    print(f"Pitch classes: {report.pcs}  mask={report.mask}  cardinality={report.cardinality}")
    if report.note_names:
        print(f"Note names: {report.note_names}")


def _print_interval_details(report: ChordAnalysisResult) -> None:
    _print_section("Intervals")
    print(f"  interval vector: {report.interval_vector}")
    summary = report.interval_summary
    print(f"  distinct pitch classes: {summary.distinct_pcs}")
    print(f"  smallest interval: {summary.smallest_interval}")
    print(f"  largest interval: {summary.largest_interval}")
    print(f"  span (linear): {summary.span_semitones} semitones")
    print(f"  span (compact): {summary.span_compact} semitones")
    if summary.interval_pairs:
        print(f"  pairwise intervals: {summary.interval_pairs}")
    if report.interval_class_histogram:
        print("  interval class histogram:")
        for label, count in report.interval_class_histogram.items():
            print(f"    {label}: {count}")
    if report.interval_matrix_labels:
        print("  interval matrix (labels):")
        for row in report.interval_matrix_labels:
            print("    " + ", ".join(row))
    if report.inverted_interval_matrix_labels:
        print("  inverted interval matrix (labels):")
        for row in report.inverted_interval_matrix_labels:
            print("    " + ", ".join(row))


def _print_symmetry(report: ChordAnalysisResult) -> None:
    symmetry = report.symmetry
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


def _print_tonnetz(report: ChordAnalysisResult) -> None:
    tonnetz = report.tonnetz
    _print_section("Tonnetz")
    if tonnetz.centroid is not None:
        print(f"  centroid: {tonnetz.centroid}")
    if tonnetz.coordinates:
        print("  coordinates:")
        for pc, triple in sorted(tonnetz.coordinates.items()):
            print(f"    pc {pc}: {triple}")


def _print_tonic_context(report: ChordAnalysisResult) -> None:
    tonic = report.tonic_context
    if not tonic:
        return
    _print_section("Tonic Context")
    print(f"  tonic pc: {tonic.tonic_pc}")
    print(
        f"  root interval from tonic: "
        f"{tonic.root_interval_from_tonic} ({tonic.root_interval_label})"
    )
    if tonic.note_names_relative_to_tonic:
        print("  chord tones relative to tonic:")
        for entry in tonic.note_names_relative_to_tonic:
            print(f"    {entry.note}: pc+{entry.relative_pc} ({entry.relative_label})")


def _print_inversions(report: ChordAnalysisResult) -> None:
    if not report.inversions:
        return
    _print_section("Inversions")
    for inversion in report.inversions:
        print(
            f"  Root pc {inversion.root_pc}: "
            f"intervals {inversion.intervals} "
            f"labels {inversion.interval_labels}"
        )
        print(f"    note names: {inversion.note_names}")


def _print_suggested_voicings(
    chord: Chord,
    spelling: SpellingPref,
    key_sig: int | None,
) -> None:
    # Generative, not analysis: register is invented from the identity. The
    # chord here is register-less (note name + quality), so analyze_voicing
    # would correctly error; suggestions are the honest thing to show instead.
    voicings = suggest_voicings(chord, spelling=spelling, key_signature=key_sig)
    _print_section("Suggested Voicings (generative)")
    for data in voicings.entries:
        print(
            f"  {data.label}: semitones {data.semitones_from_root} "
            f"(spread {data.spread})"
        )
        print(f"    intervals mod 12: {data.intervals_mod_12}")
        print(f"    note names: {data.note_names}")


def _print_enharmonics(report: ChordAnalysisResult) -> None:
    if not report.enharmonics:
        return
    _print_section("Enharmonic Spellings")
    for entry in report.enharmonics:
        if entry.alternates:
            print(
                f"  pc {entry.pc}: {entry.preferred} "
                f"(alternates: {', '.join(entry.alternates)})"
            )
        else:
            print(f"  pc {entry.pc}: {entry.preferred}")


def _print_report(report: ChordAnalysisResult) -> None:
    _print_overview(report)
    _print_interval_details(report)
    _print_symmetry(report)
    _print_tonnetz(report)
    _print_tonic_context(report)
    _print_inversions(report)
    _print_enharmonics(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a chord using the analysis toolkit.")
    # TODO: Support inline chord creation like "[0,4,7]=MyChord" or "C3[0,4,7]=MyVoicing" during analysis.
    parser.add_argument("root", nargs="?", help="Chord root note (e.g., C, F#, Eb)")
    parser.add_argument("quality", nargs="?", help="Chord quality name from data/chord_qualities.json (e.g., maj7)")
    parser.add_argument("--list-scales", action="store_true", help="List available scales and exit.")
    parser.add_argument("--list-qualities", action="store_true", help="List available chord qualities and exit.")
    parser.add_argument("--tonic", dest="tonic", help="Optional tonic for context analysis")
    parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                        help="Enharmonic spelling preference for chord notes.")
    parser.add_argument("--key-sig", type=int, default=None,
                        help="Optional circle-of-fifths index (-7..+7) for spelling bias.")
    parser.add_argument("--interval-labels", choices=["numeric", "classical"], default="numeric",
                        help="Format for interval names (numeric or classical P/M/m labels).")
    parser.add_argument("--no-inversions", action="store_true",
                        help="Skip inversion enumeration in the output.")
    parser.add_argument("--no-voicings", action="store_true",
                        help="Skip generative voicing suggestions in the output.")
    parser.add_argument("--no-enharmonics", action="store_true",
                        help="Skip enharmonic spelling listings.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the raw analysis payload as pretty-printed JSON.")
    args = parser.parse_args()

    qualities = load_chord_qualities()
    scales = load_scales()
    if args.list_scales:
        print("Available scales:")
        for name in sorted(scales.keys()):
            print(" -", name)
        return
    if args.list_qualities:
        print("Available chord qualities:")
        for name in sorted(qualities.keys()):
            print(" -", name)
        return
    if args.root is None or args.quality is None:
        parser.error("Root and quality are required unless using --list-scales/--list-qualities.")
    if args.quality not in qualities:
        parser.error(f"Unknown quality {args.quality!r}. Use --list-qualities to inspect options.")

    root_pc = pc_from_name(args.root)
    chord = Chord.from_quality(root_pc, qualities[args.quality])
    chord_quality = chord.quality
    tonic_pc = pc_from_name(args.tonic) if args.tonic else None

    context = SESSION_CHORD_CONTEXT.get(chord_quality.name)
    if context:
        scope = context.get("scope", "abstract").capitalize()
        tokens = ", ".join(context.get("tokens", []))
        line = f"Context: {scope}"
        if tokens:
            line += f" ({tokens})"
        print(line)

    request = ChordAnalysisRequest(
        chord=chord,
        tonic_pc=tonic_pc,
        spelling=args.spelling,
        key_signature=args.key_sig,
        interval_label_style=args.interval_labels,
        include_inversions=not args.no_inversions,
        include_enharmonics=not args.no_enharmonics,
    )
    report = analyze_chord(request)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    _print_report(report)
    if not args.no_voicings:
        _print_suggested_voicings(chord, args.spelling, args.key_sig)


if __name__ == "__main__":
    main()
