"""CLI stub for manual scale/chord entry and session registration."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.analysis import ManualScaleBuilder, ManualChordBuilder, register_scale, register_chord


def parse_int_list(text: str) -> list[int]:
    return [int(token) for token in text.split(",") if token.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ad hoc scales or chords for the current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scale_parser = subparsers.add_parser("scale", help="Register a manual scale")
    scale_parser.add_argument("name", help="Name for the scale")
    scale_parser.add_argument("degrees", help="Comma-separated pitch classes (0-11)")

    chord_parser = subparsers.add_parser("chord", help="Register a manual chord quality")
    chord_parser.add_argument("name", help="Name for the chord quality")
    chord_parser.add_argument("intervals", help="Comma-separated intervals (0-11)")

    args = parser.parse_args()

    if args.command == "scale":
        builder = ManualScaleBuilder(name=args.name, degrees=parse_int_list(args.degrees))
        scale = register_scale(builder)
        print(f"Registered scale: {scale.name} -> {list(scale.degrees)}")
    elif args.command == "chord":
        builder = ManualChordBuilder(name=args.name, intervals=parse_int_list(args.intervals))
        quality = register_chord(builder)
        print(f"Registered chord: {quality.name} -> {list(quality.intervals)}")


if __name__ == "__main__":
    main()
