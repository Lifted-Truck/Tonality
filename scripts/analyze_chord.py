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

from mts.io.loaders import load_chord_qualities
from mts.core.chord import Chord
from mts.core.enharmonics import pc_from_name
from mts.analysis import ChordAnalysisRequest, analyze_chord


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_overview(report: dict[str, object]) -> None:
    print(f"Chord: {report['quality']} (root pc {report['root_pc']})")
    print(f"Pitch classes: {report['pcs']}  mask={report['mask']}  cardinality={report['cardinality']}")
    note_names = report.get("note_names")
    if note_names:
        print(f"Note names: {note_names}")


def _print_interval_details(report: dict[str, object]) -> None:
    _print_section("Intervals")
    interval_vector = report.get("interval_vector")
    if interval_vector is not None:
        print(f"  interval vector: {interval_vector}")
    summary = report.get("interval_summary", {})
    if summary:
        print(f"  distinct pitch classes: {summary.get('distinct_pcs')}")
        print(f"  smallest interval: {summary.get('smallest_interval')}")
        print(f"  largest interval: {summary.get('largest_interval')}")
        print(f"  span (linear): {summary.get('span_semitones')} semitones")
        print(f"  span (compact): {summary.get('span_compact')} semitones")
        pairs = summary.get("interval_pairs")
        if pairs:
            print(f"  pairwise intervals: {pairs}")
    histogram = report.get("interval_class_histogram")
    if histogram:
        print("  interval class histogram:")
        for label, count in histogram.items():
            print(f"    {label}: {count}")
    matrix_labels = report.get("interval_matrix_labels")
    if matrix_labels:
        print("  interval matrix (labels):")
        for row in matrix_labels:
            print("    " + ", ".join(row))
    inverted_matrix = report.get("inverted_interval_matrix_labels")
    if inverted_matrix:
        print("  inverted interval matrix (labels):")
        for row in inverted_matrix:
            print("    " + ", ".join(row))


def _print_symmetry(report: dict[str, object]) -> None:
    symmetry = report.get("symmetry")
    if not symmetry:
        return
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
            print(f"    - {axis.get('type')} axis @ {axis.get('center')}")
    else:
        print("  reflection axes: none")


def _print_tonnetz(report: dict[str, object]) -> None:
    tonnetz = report.get("tonnetz", {})
    if not tonnetz:
        return
    _print_section("Tonnetz")
    centroid = tonnetz.get("centroid")
    if centroid is not None:
        print(f"  centroid: {centroid}")
    coords = tonnetz.get("coordinates", {})
    if coords:
        print("  coordinates:")
        for pc, triple in sorted(coords.items()):
            print(f"    pc {pc}: {triple}")


def _print_tonic_context(report: dict[str, object]) -> None:
    tonic = report.get("tonic_context")
    if not tonic:
        return
    _print_section("Tonic Context")
    print(f"  tonic pc: {tonic.get('tonic_pc')}")
    print(
        "  root interval from tonic: "
        f"{tonic.get('root_interval_from_tonic')} ({tonic.get('root_interval_label')})"
    )
    rel_notes = tonic.get("note_names_relative_to_tonic", [])
    if rel_notes:
        print("  chord tones relative to tonic:")
        for entry in rel_notes:
            print(
                f"    {entry.get('note')}: pc+{entry.get('relative_pc')} "
                f"({entry.get('relative_label')})"
            )


def _print_inversions(report: dict[str, object]) -> None:
    inversions = report.get("inversions", [])
    if not inversions:
        return
    _print_section("Inversions")
    for inversion in inversions:
        print(
            f"  Root pc {inversion.get('root_pc')}: "
            f"intervals {inversion.get('intervals')} "
            f"labels {inversion.get('interval_labels')}"
        )
        print(f"    note names: {inversion.get('note_names')}")


def _print_voicings(report: dict[str, object]) -> None:
    voicings = report.get("voicings")
    if not voicings:
        return
    _print_section("Voicings")
    for label, data in voicings.items():
        print(
            f"  {label}: semitones {data.get('semitones_from_root')} "
            f"(spread {data.get('spread')})"
        )
        print(f"    intervals mod 12: {data.get('intervals_mod_12')}")
        print(f"    note names: {data.get('note_names')}")


def _print_enharmonics(report: dict[str, object]) -> None:
    enharmonics = report.get("enharmonics", [])
    if not enharmonics:
        return
    _print_section("Enharmonic Spellings")
    for entry in enharmonics:
        alternates = entry.get("alternates") or []
        if alternates:
            print(
                f"  pc {entry.get('pc')}: {entry.get('preferred')} "
                f"(alternates: {', '.join(alternates)})"
            )
        else:
            print(f"  pc {entry.get('pc')}: {entry.get('preferred')}")


def _print_report(report: dict[str, object]) -> None:
    _print_overview(report)
    _print_interval_details(report)
    _print_symmetry(report)
    _print_tonnetz(report)
    _print_tonic_context(report)
    _print_inversions(report)
    _print_voicings(report)
    _print_enharmonics(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a chord using the analysis toolkit.")
    parser.add_argument("root", help="Chord root note (e.g., C, F#, Eb)")
    parser.add_argument("quality", help="Chord quality name from data/chord_qualities.json (e.g., maj7)")
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
                        help="Skip voicing generation in the output.")
    parser.add_argument("--no-enharmonics", action="store_true",
                        help="Skip enharmonic spelling listings.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the raw analysis payload as pretty-printed JSON.")
    args = parser.parse_args()

    qualities = load_chord_qualities()
    if args.quality not in qualities:
        parser.error(f"Unknown quality {args.quality!r}")

    root_pc = pc_from_name(args.root)
    chord = Chord.from_quality(root_pc, qualities[args.quality])
    tonic_pc = pc_from_name(args.tonic) if args.tonic else None

    request = ChordAnalysisRequest(
        chord=chord,
        tonic_pc=tonic_pc,
        spelling=args.spelling,
        key_signature=args.key_sig,
        interval_label_style=args.interval_labels,
        include_inversions=not args.no_inversions,
        include_voicings=not args.no_voicings,
        include_enharmonics=not args.no_enharmonics,
    )
    report = analyze_chord(request)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    _print_report(report)


if __name__ == "__main__":
    main()
