"""CLI stub for scale analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# TODO: remove when package is installed in editable mode.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales
from mts.analysis import ScaleAnalysisRequest, analyze_scale
from mts.core.enharmonics import pc_from_name


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
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
