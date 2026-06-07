"""CLI helper for chord analysis.

Analysis is pure-identity (numeric); spelling and interval-label style are applied
at the display edge from a ``DisplayContext`` via ``mts.context.result_format``.
"""

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
from mts.context import DisplayContext
from mts.context.formatters import format_pitch_class
from mts.context.result_format import format_chord_analysis, interval_label


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_overview(report: ChordAnalysisResult, ctx: DisplayContext) -> None:
    display = format_chord_analysis(report, ctx)
    print(f"Chord: {display.root_name}:{report.quality} (root pc {report.root_pc})")
    print(f"Pitch classes: {report.pcs}  mask={report.mask}  cardinality={report.cardinality}")
    print(f"Note names: {display.note_names}")


def _print_interval_details(report: ChordAnalysisResult, ctx: DisplayContext) -> None:
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
        for ic, count in report.interval_class_histogram.items():
            print(f"    {interval_label(ic, ctx)}: {count}")
    print("  interval matrix (labels):")
    for row in report.interval_matrix:
        print("    " + ", ".join(interval_label(iv, ctx) for iv in row))


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


def _print_tonic_context(report: ChordAnalysisResult, ctx: DisplayContext) -> None:
    tonic = report.tonic_context
    if not tonic:
        return
    _print_section("Tonic Context")
    print(f"  tonic pc: {tonic.tonic_pc}")
    print(
        f"  root interval from tonic: "
        f"{tonic.root_interval_from_tonic} ({interval_label(tonic.root_interval_from_tonic, ctx)})"
    )
    if tonic.relative_pcs:
        print("  chord tones relative to tonic:")
        for rel in tonic.relative_pcs:
            print(f"    pc+{rel} ({interval_label(rel, ctx)})")


def _print_inversions(report: ChordAnalysisResult, ctx: DisplayContext) -> None:
    if not report.inversions:
        return
    _print_section("Inversions")
    for inversion in report.inversions:
        labels = [interval_label(iv, ctx) for iv in inversion.intervals]
        note_names = [
            format_pitch_class((inversion.root_pc + iv) % 12, ctx) for iv in inversion.intervals
        ]
        figure = f" [{inversion.figured_bass}]" if inversion.figured_bass else ""
        print(
            f"  {inversion.position_name}{figure} — root pc {inversion.root_pc}: "
            f"intervals {inversion.intervals} labels {labels}"
        )
        print(f"    note names: {note_names}")


def _print_suggested_voicings(chord: Chord, ctx: DisplayContext) -> None:
    # Generative, not analysis: register is invented from the identity. The chord
    # here is register-less (note name + quality), so analyze_voicing would
    # correctly error; suggestions are the honest thing to show instead.
    voicings = suggest_voicings(chord)
    _print_section("Suggested Voicings (generative)")
    for data in voicings.entries:
        note_names = [format_pitch_class((chord.root_pc + o) % 12, ctx) for o in data.semitones_from_root]
        print(f"  {data.label}: semitones {data.semitones_from_root} (spread {data.spread})")
        print(f"    intervals mod 12: {data.intervals_mod_12}")
        print(f"    note names: {note_names}")


def _print_enharmonics(report: ChordAnalysisResult, ctx: DisplayContext) -> None:
    _print_section("Enharmonic Spellings")
    for entry in format_chord_analysis(report, ctx).enharmonics:
        if entry.alternates:
            print(f"  pc {entry.pc}: {entry.preferred} (alternates: {', '.join(entry.alternates)})")
        else:
            print(f"  pc {entry.pc}: {entry.preferred}")


def _print_report(report: ChordAnalysisResult, ctx: DisplayContext, *, enharmonics: bool) -> None:
    _print_overview(report, ctx)
    _print_interval_details(report, ctx)
    _print_symmetry(report)
    _print_tonnetz(report)
    _print_tonic_context(report, ctx)
    _print_inversions(report, ctx)
    if enharmonics:
        _print_enharmonics(report, ctx)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a chord using the analysis toolkit.")
    parser.add_argument("root", nargs="?", help="Chord root note (e.g., C, F#, Eb)")
    parser.add_argument("quality", nargs="?", help="Chord quality name from data/chord_qualities.json (e.g., maj7)")
    parser.add_argument("--list-scales", action="store_true", help="List available scales and exit.")
    parser.add_argument("--list-qualities", action="store_true", help="List available chord qualities and exit.")
    parser.add_argument("--tonic", dest="tonic", help="Optional tonic for context analysis")
    parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                        help="Enharmonic spelling preference for chord notes (display).")
    parser.add_argument("--key-sig", type=int, default=None,
                        help="Optional circle-of-fifths index (-7..+7) for spelling bias (display).")
    parser.add_argument("--interval-labels", choices=["numeric", "classical"], default="numeric",
                        help="Format for interval names (display).")
    parser.add_argument("--no-inversions", action="store_true",
                        help="Skip inversion enumeration in the output.")
    parser.add_argument("--no-voicings", action="store_true",
                        help="Skip generative voicing suggestions in the output.")
    parser.add_argument("--no-enharmonics", action="store_true",
                        help="Skip enharmonic spelling listings.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the analysis payload (numeric) plus a spelled display view as JSON.")
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
    tonic_pc = pc_from_name(args.tonic) if args.tonic else None

    # Build the display context (spelling / labels / tonal center) for the edge.
    ctx = DisplayContext()
    ctx.set("spelling", args.spelling, layer="cli")
    ctx.set("interval_label_style", args.interval_labels, layer="cli")
    if args.key_sig is not None:
        ctx.set("key_signature", args.key_sig, layer="cli")
    if tonic_pc is not None:
        ctx.set("tonic_pc", tonic_pc, layer="cli")

    session_context = SESSION_CHORD_CONTEXT.get(chord.quality.name)
    if session_context:
        scope = session_context.get("scope", "abstract").capitalize()
        tokens = ", ".join(session_context.get("tokens", []))
        line = f"Context: {scope}"
        if tokens:
            line += f" ({tokens})"
        print(line)

    request = ChordAnalysisRequest(
        chord=chord,
        tonic_pc=tonic_pc,
        include_inversions=not args.no_inversions,
    )
    report = analyze_chord(request)
    if args.json:
        payload = report.to_dict()
        payload["display"] = format_chord_analysis(report, ctx).to_dict()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    _print_report(report, ctx, enharmonics=not args.no_enharmonics)
    if not args.no_voicings:
        _print_suggested_voicings(chord, ctx)


if __name__ == "__main__":
    main()
