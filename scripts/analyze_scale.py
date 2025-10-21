"""CLI stub for scale analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales
from mts.analysis import ScaleAnalysisRequest, analyze_scale


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a scale using placeholder analytics.")
    parser.add_argument(
        "scale",
        help=(
            "Scale name from the database (e.g., Ionian). "
            "Use scripts/check_chord_scale_compat.py --list-scales to inspect options."
        ),
    )
    args = parser.parse_args()

    scales = load_scales()
    if args.scale not in scales:
        parser.error(f"Unknown scale {args.scale!r}")

    request = ScaleAnalysisRequest(scale=scales[args.scale])
    report = analyze_scale(request)
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
