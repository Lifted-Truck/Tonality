"""Chord-scale compatibility explorer with transposition support."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales, load_chord_qualities
from mts.core.bitmask import mask_from_pcs, is_subset
from mts.core.quality import ChordQuality
from mts.core.scale import Scale


def chord_mask(intervals: Tuple[int, ...], transpose: int) -> int:
    pcs = [((iv + transpose) % 12) for iv in intervals]
    return mask_from_pcs(pcs)


def compatibility_positions(scale: Scale, quality: ChordQuality) -> List[int]:
    """Return root positions (0..11) where the chord fits in the scale."""
    compatible_roots: List[int] = []
    scale_mask = scale.mask
    base_intervals = quality.intervals
    for root in range(12):
        mask = chord_mask(base_intervals, root)
        if is_subset(mask, scale_mask):
            compatible_roots.append(root)
    return compatible_roots


def describe_scale(scale: Scale) -> str:
    degrees = ",".join(str(pc) for pc in scale.degrees)
    return f"{scale.name} ({degrees})"


def _sort_key(name: str, quality: ChordQuality) -> Tuple[int, int, str]:
    intervals = quality.intervals
    size = len(intervals)
    max_interval = max(intervals) if intervals else 0
    extensions_order = [
        ("maj", 0),
        ("min", 0),
        ("dim", 0),
        ("aug", 0),
        ("sus2", 0),
        ("sus4", 0),
        ("power", 0),
        ("maj6", 1),
        ("min6", 1),
        ("maj6add9", 2),
        ("min6add9", 2),
        ("majadd9", 2),
        ("minadd9", 2),
        ("maj7", 3),
        ("min7", 3),
        ("min7b5", 3),
        ("minmaj7", 3),
        ("7", 3),
        ("maj9", 4),
        ("min9", 4),
        ("9", 4),
        ("maj7#11", 5),
        ("maj9#11", 5),
        ("9b5", 5),
        ("9#5", 5),
        ("11", 6),
        ("min11", 6),
        ("13", 7),
        ("min13", 7),
    ]
    priority_map = {name: idx for idx, (name, _) in enumerate(extensions_order)}
    priority = priority_map.get(name, len(extensions_order))
    return (priority, size, max_interval, name)


def run_overview(scales: Dict[str, Scale], qualities: Dict[str, ChordQuality]) -> None:
    for scale_name, scale in sorted(scales.items()):
        compatible = []
        incompatible = []
        for quality_name, quality in qualities.items():
            roots = compatibility_positions(scale, quality)
            if roots:
                compatible.append((quality_name, roots, quality))
            else:
                incompatible.append(quality_name)

        print(f"\nScale: {describe_scale(scale)}")
        for name, roots, quality in sorted(
            compatible, key=lambda item: _sort_key(item[0], item[2])
        ):
            root_list = ", ".join(str(r) for r in roots)
            print(f"  {name:<10} -> roots [{root_list}]")
        print(f"  Non-diatonic ({len(incompatible)}): {', '.join(sorted(incompatible))}")


def run_specific(scales: Dict[str, Scale], qualities: Dict[str, ChordQuality], *, scale_name: str, chord_quality: str) -> None:
    if scale_name not in scales:
        raise SystemExit(f"Unknown scale {scale_name!r}. Use --list-scales to see options.")
    if chord_quality not in qualities:
        raise SystemExit(f"Unknown chord quality {chord_quality!r}. Use --list-qualities to see options.")

    scale = scales[scale_name]
    quality = qualities[chord_quality]
    roots = compatibility_positions(scale, quality)
    if roots:
        root_list = ", ".join(str(r) for r in roots)
        print(f"{chord_quality} fits in {scale.name} at roots: [{root_list}]")
    else:
        print(f"{chord_quality} introduces out-of-scale tones in {scale.name} at every root.")
        print("TODO: Identify modal sources for non-diatonic placements.")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Explore chord-scale compatibility via pitch-class masks.")
    parser.add_argument("--scale", help="Scale name to analyze (optional).")
    parser.add_argument("--chord-quality", help="Chord quality name to test (optional).")
    parser.add_argument("--list-scales", action="store_true", help="List available scales and exit.")
    parser.add_argument("--list-qualities", action="store_true", help="List chord qualities and exit.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    scales = load_scales()
    qualities = load_chord_qualities()

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

    if args.scale and args.chord_quality:
        run_specific(scales, qualities, scale_name=args.scale, chord_quality=args.chord_quality)
    else:
        run_overview(scales, qualities)


if __name__ == "__main__":
    main()
