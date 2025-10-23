"""CLI for comparing two chord qualities across the scale catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure repository import path when running as a script
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_chord_qualities, load_scales
from mts.core.enharmonics import pc_from_name, name_for_pc
from mts.core.chord import Chord
from mts.analysis import compare_chord_qualities

ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def _parse_chord_spec(text: str) -> tuple[int, str]:
    """Return (root_pc, quality_name)."""

    if ":" in text:
        root_text, qual_text = text.split(":", 1)
        root_pc = pc_from_name(root_text.strip())
        return root_pc, qual_text.strip()
    return 0, text.strip()


def _root_label(scale_degrees: list[int], root: int) -> str:
    if root in scale_degrees:
        idx = scale_degrees.index(root)
        if idx < len(ROMANS):
            return ROMANS[idx]
        return str(idx + 1)
    return f"pc{root}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two chord qualities and report shared scale contexts.",
    )
    parser.add_argument("chord_a", help="Chord spec 'Root:Quality' (e.g. C:maj7) or quality name.")
    parser.add_argument("chord_b", help="Chord spec 'Root:Quality' (e.g. G:7) or quality name.")
    parser.add_argument(
        "--scales",
        help="Comma-separated list of scale names to restrict the comparison (defaults to all).",
    )
    parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                        help="Enharmonic preference when spelling chord tones.")
    parser.add_argument("--key-sig", type=int, default=0,
                        help="Circle-of-fifths index (-7..+7) used for note spelling.")
    parser.add_argument("--list-qualities", action="store_true",
                        help="List available chord qualities and exit.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    qualities = load_chord_qualities()
    scales = load_scales()

    if args.list_qualities:
        print("Available chord qualities:")
        for name in sorted(qualities):
            print(f" - {name}")
        return

    root_a, qual_name_a = _parse_chord_spec(args.chord_a)
    root_b, qual_name_b = _parse_chord_spec(args.chord_b)

    if qual_name_a not in qualities:
        parser.error(f"Unknown chord quality {qual_name_a!r}. Use --list-qualities to inspect options.")
    if qual_name_b not in qualities:
        parser.error(f"Unknown chord quality {qual_name_b!r}. Use --list-qualities to inspect options.")

    quality_a = qualities[qual_name_a]
    quality_b = qualities[qual_name_b]

    chord_a = Chord.from_quality(root_a, quality_a)
    chord_b = Chord.from_quality(root_b, quality_b)

    include_scales = None
    if args.scales:
        include_scales = [name.strip() for name in args.scales.split(",") if name.strip()]

    comparison = compare_chord_qualities(
        quality_a,
        quality_b,
        catalog_scales=scales,
        include_scales=include_scales,
    )

    def describe_chord(chord: Chord) -> str:
        notes = ", ".join(chord.spelled(prefer=args.spelling, key_signature=args.key_sig))
        intervals = ", ".join(str(iv) for iv in chord.quality.intervals)
        return f"notes [{notes}] intervals [{intervals}]"

    print(f"Chord A: {args.chord_a} -> {describe_chord(chord_a)}")
    print(f"Chord B: {args.chord_b} -> {describe_chord(chord_b)}")
    print()
    print(f"Interval fingerprints:")
    print(f"  {comparison.quality_a}: {comparison.interval_fingerprint_a}")
    print(f"  {comparison.quality_b}: {comparison.interval_fingerprint_b}")
    if comparison.intervals_only_a or comparison.intervals_only_b:
        if comparison.intervals_only_a:
            print(f"  Unique to {comparison.quality_a}: {comparison.intervals_only_a}")
        if comparison.intervals_only_b:
            print(f"  Unique to {comparison.quality_b}: {comparison.intervals_only_b}")
    else:
        print("  Interval sets are identical.")

    if comparison.shared_scales:
        print(f"\nShared scales ({len(comparison.shared_scales)}):")
        for placement in comparison.shared_scales:
            scale = scales[placement.scale]
            degrees = list(scale.degrees)
            print(f" - {placement.scale}")
            print(f"     {comparison.quality_a}:")
            for root in placement.roots_a:
                root_label = _root_label(degrees, root)
                degree_labels = ", ".join(placement.degree_map_a[root])
                print(f"       root {root:>2} ({root_label}) -> degrees [{degree_labels}]")
            print(f"     {comparison.quality_b}:")
            for root in placement.roots_b:
                root_label = _root_label(degrees, root)
                degree_labels = ", ".join(placement.degree_map_b[root])
                print(f"       root {root:>2} ({root_label}) -> degrees [{degree_labels}]")
            if placement.shared_roots:
                shared = ", ".join(str(val) for val in placement.shared_roots)
                print(f"     Common root positions: [{shared}]")
            else:
                print(f"     Common root positions: none")
    else:
        print("\nNo shared scales found for the selected qualities.")

    if comparison.unique_to_a:
        joined = ", ".join(comparison.unique_to_a)
        print(f"\nScales unique to {comparison.quality_a}: {joined}")
    if comparison.unique_to_b:
        joined = ", ".join(comparison.unique_to_b)
        print(f"Scales unique to {comparison.quality_b}: {joined}")


if __name__ == "__main__":
    main()
