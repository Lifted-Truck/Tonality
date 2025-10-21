"""CLI stub for chord analysis."""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a chord using placeholder analytics.")
    parser.add_argument("root", help="Chord root note (e.g., C, F#, Eb)")
    parser.add_argument("quality", help="Chord quality name from data/chord_qualities.json (e.g., maj7)")
    parser.add_argument("--tonic", dest="tonic", help="Optional tonic for context analysis")
    args = parser.parse_args()

    qualities = load_chord_qualities()
    if args.quality not in qualities:
        parser.error(f"Unknown quality {args.quality!r}")

    root_pc = pc_from_name(args.root)
    chord = Chord.from_quality(root_pc, qualities[args.quality])
    tonic_pc = pc_from_name(args.tonic) if args.tonic else None

    request = ChordAnalysisRequest(chord=chord, tonic_pc=tonic_pc)
    report = analyze_chord(request)
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
