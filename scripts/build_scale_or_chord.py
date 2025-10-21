"""CLI stub for manual scale/chord entry and session registration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales, load_chord_qualities
from mts.analysis import (
    ManualScaleBuilder,
    ManualChordBuilder,
    register_scale,
    register_chord,
)
from mts.analysis.builders import (
    degrees_from_mask,
    mask_from_text,
    match_scale,
    match_chord,
)


def parse_int_list(text: str | None) -> list[int]:
    if text is None:
        return []
    return [int(token) % 12 for token in text.split(",") if token.strip()]


def resolve_degrees(degrees_arg: str | None, mask_arg: str | None) -> list[int]:
    if mask_arg:
        mask_value = mask_from_text(mask_arg)
        degrees = degrees_from_mask(mask_value)
        if not degrees:
            raise ValueError("Mask does not contain any pitch classes.")
        return degrees
    degrees = parse_int_list(degrees_arg)
    if not degrees:
        raise ValueError("Provide either --mask or a comma-separated degree list.")
    return sorted(set(degrees))


def resolve_intervals(intervals_arg: str | None, mask_arg: str | None) -> list[int]:
    if mask_arg:
        mask_value = mask_from_text(mask_arg)
        intervals = sorted(set(degrees_from_mask(mask_value)))
        if not intervals:
            raise ValueError("Mask does not contain any intervals.")
        return intervals
    intervals = parse_int_list(intervals_arg)
    if not intervals:
        raise ValueError("Provide either --mask or a comma-separated interval list.")
    return sorted(set(intervals))


def scale_command(args: argparse.Namespace) -> None:
    catalog = load_scales()
    degrees = resolve_degrees(args.degrees, args.mask)
    matches = match_scale(degrees, catalog)
    if matches:
        print("Matching catalog scales:")
        for scale in matches:
            print(f" - {scale.name}: {list(scale.degrees)}")
    if args.match_only:
        if not matches:
            print("No catalog matches found.")
        return

    builder = ManualScaleBuilder(name=args.name, degrees=degrees)
    result = register_scale(builder, catalog=catalog)
    scale = result["scale"]
    if result["match"]:
        print(f"Reusing catalog scale: {scale.name} -> {list(scale.degrees)}")
    else:
        print(f"Registered scale: {scale.name} -> {list(scale.degrees)}")


def chord_command(args: argparse.Namespace) -> None:
    catalog = load_chord_qualities()
    intervals = resolve_intervals(args.intervals, args.mask)
    matches = match_chord(intervals, catalog)
    if matches:
        print("Matching catalog chord qualities:")
        for quality in matches:
            print(f" - {quality.name}: {list(quality.intervals)}")
    if args.match_only:
        if not matches:
            print("No catalog matches found.")
        return

    builder = ManualChordBuilder(name=args.name, intervals=intervals)
    result = register_chord(builder, catalog=catalog)
    quality = result["quality"]
    if result["match"]:
        print(f"Reusing catalog quality: {quality.name} -> {list(quality.intervals)}")
    else:
        print(f"Registered chord: {quality.name} -> {list(quality.intervals)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ad hoc scales or chords for the current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scale_parser = subparsers.add_parser("scale", help="Register or match a manual scale")
    scale_parser.add_argument("--name", help="Optional name; will fall back to placeholder if omitted.")
    scale_parser.add_argument("--degrees", help="Comma-separated pitch classes (0-11).")
    scale_parser.add_argument("--mask", help="12-bit mask in binary or decimal (e.g., 0b101010101010 or 2730).")
    scale_parser.add_argument("--match-only", action="store_true",
                              help="Only display catalog matches without registering.")

    chord_parser = subparsers.add_parser("chord", help="Register or match a manual chord quality")
    chord_parser.add_argument("--name", help="Optional name; will fall back to placeholder if omitted.")
    chord_parser.add_argument("--intervals", help="Comma-separated intervals (0-11) relative to the root.")
    chord_parser.add_argument("--mask", help="12-bit interval mask in binary or decimal.")
    chord_parser.add_argument("--match-only", action="store_true",
                              help="Only display catalog matches without registering.")

    args = parser.parse_args()

    try:
        if args.command == "scale":
            scale_command(args)
        elif args.command == "chord":
            chord_command(args)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
