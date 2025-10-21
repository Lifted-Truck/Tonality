"""Chord-scale compatibility explorer with transposition support."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path
import sys

# Prefer installing the package in editable mode when possible. The path tweak
# keeps this script runnable during development workflows.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mts.io.loaders import load_scales, load_chord_qualities
from mts.core.bitmask import mask_from_pcs, is_subset
from mts.core.quality import ChordQuality
from mts.core.scale import Scale
from mts.core.enharmonics import name_for_pc, pc_from_name, SpellingPref

EXTENSIONS_ORDER: list[tuple[str, int]] = [
    ("power", 0),
    ("maj", 0),
    ("min", 0),
    ("dim", 0),
    ("aug", 0),
    ("sus2", 0),
    ("sus4", 0),
    ("maj6", 1),
    ("min6", 1),
    ("majadd9", 2),
    ("minadd9", 2),
    ("maj6add9", 2),
    ("min6add9", 2),
    ("maj7", 3),
    ("min7", 3),
    ("min7b5", 3),
    ("minmaj7", 3),
    ("7", 3),
    ("7sus4", 3),
    ("maj9", 4),
    ("min9", 4),
    ("9", 4),
    ("9b5", 5),
    ("9#5", 5),
    ("maj7#11", 5),
    ("maj9#11", 5),
    ("11", 6),
    ("min11", 6),
    ("13", 7),
    ("min13", 7),
    ("maj13", 7),
    ("7b5", 7),
    ("7#5", 7),
    ("7b9", 7),
    ("7#9", 7),
    ("7#11", 7),
    ("7alt", 8),
    ("dim7", 8),
]

EXTENSION_PRIORITY: dict[str, int] = {name: idx for idx, (name, _) in enumerate(EXTENSIONS_ORDER)}


@lru_cache(maxsize=None)
def _chord_mask(intervals: tuple[int, ...], transpose: int) -> int:
    pcs = [((iv + transpose) % 12) for iv in intervals]
    return mask_from_pcs(pcs)


def compatibility_positions(scale: Scale, quality: ChordQuality) -> list[int]:
    """Return root positions (0..11) where the chord fits in the scale."""
    compatible_roots: list[int] = []
    scale_mask = scale.mask
    base_intervals = quality.intervals
    intervals_tuple = tuple(base_intervals)
    for root in range(12):
        mask = _chord_mask(intervals_tuple, root)
        if is_subset(mask, scale_mask):
            compatible_roots.append(root)
    return compatible_roots


def describe_scale(scale: Scale) -> str:
    degrees = ",".join(str(pc) for pc in scale.degrees)
    return f"{scale.name} ({degrees})"


def _sort_key(name: str, quality: ChordQuality) -> tuple[int, int, int, str]:
    intervals = quality.intervals
    size = len(intervals)
    max_interval = max(intervals) if intervals else 0
    priority = EXTENSION_PRIORITY.get(name, len(EXTENSIONS_ORDER))
    return (priority, size, max_interval, name)


def _spell_chord(root_pc: int, quality: ChordQuality, prefer: SpellingPref, key_signature: int | None) -> list[str]:
    return [
        name_for_pc((root_pc + interval) % 12, prefer=prefer, key_signature=key_signature)
        for interval in quality.intervals
    ]


def run_overview(
    scales: Mapping[str, Scale],
    qualities: Mapping[str, ChordQuality],
    *,
    tonic_pc: int,
    spelling: SpellingPref,
    key_signature: int | None,
    include_note_names: bool,
) -> None:
    for scale_name, scale in sorted(scales.items()):
        compatible: list[tuple[str, list[int], ChordQuality]] = []
        incompatible: list[str] = []
        for quality_name, quality in qualities.items():
            roots = compatibility_positions(scale, quality)
            if roots:
                compatible.append((quality_name, roots, quality))
            else:
                incompatible.append(quality_name)

        print(f"\nScale: {describe_scale(scale)}")
        for name, roots, quality in sorted(compatible, key=lambda item: _sort_key(item[0], item[2])):
            if include_note_names:
                rendered_roots = []
                for root in roots:
                    absolute_root = (tonic_pc + root) % 12
                    root_name = name_for_pc(absolute_root, prefer=spelling, key_signature=key_signature)
                    notes = _spell_chord(absolute_root, quality, spelling, key_signature)
                    rendered_roots.append(f"{root} ({root_name}: {'-'.join(notes)})")
                root_display = ", ".join(rendered_roots)
            else:
                root_display = ", ".join(str(r) for r in roots)
            print(f"  {name:<10} -> roots [{root_display}]")
        print(f"  Non-diatonic ({len(incompatible)}): {', '.join(sorted(incompatible))}")


def run_specific(
    scales: Mapping[str, Scale],
    qualities: Mapping[str, ChordQuality],
    *,
    scale_name: str,
    chord_quality: str,
    tonic_pc: int,
    spelling: SpellingPref,
    key_signature: int | None,
    include_note_names: bool,
) -> None:
    scale = scales[scale_name]
    quality = qualities[chord_quality]
    roots = compatibility_positions(scale, quality)
    if roots:
        if include_note_names:
            rendered = []
            for root in roots:
                absolute_root = (tonic_pc + root) % 12
                root_name = name_for_pc(absolute_root, prefer=spelling, key_signature=key_signature)
                notes = _spell_chord(absolute_root, quality, spelling, key_signature)
                rendered.append(f"{root} ({root_name}: {'-'.join(notes)})")
            display = ", ".join(rendered)
        else:
            display = ", ".join(str(r) for r in roots)
        print(f"{chord_quality} fits in {scale.name} at roots: [{display}]")
    else:
        print(f"{chord_quality} introduces out-of-scale tones in {scale.name} at every root.")
        print("TODO: Identify modal sources for non-diatonic placements.")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Explore chord-scale compatibility via pitch-class masks.")
    parser.add_argument("--scale", help="Scale name to analyze (optional).")
    parser.add_argument("--chord-quality", help="Chord quality name to test (optional).")
    parser.add_argument("--list-scales", action="store_true", help="List available scales and exit.")
    parser.add_argument("--list-qualities", action="store_true", help="List chord qualities and exit.")
    parser.add_argument("--tonic", help="Optional tonic note to spell results (defaults to C if omitted).")
    parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                        help="Enharmonic preference for rendered notes.")
    parser.add_argument("--key-sig", type=int, default=None,
                        help="Optional circle-of-fifths index (-7..+7) for spelling bias.")
    parser.add_argument("--no-note-names", action="store_true",
                        help="Suppress note-name rendering in outputs.")
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

    tonic_pc = pc_from_name(args.tonic) if args.tonic else 0
    include_note_names = not args.no_note_names

    if args.scale and args.chord_quality:
        if args.scale not in scales:
            parser.error(f"Unknown scale {args.scale!r}. Use --list-scales to inspect options.")
        if args.chord_quality not in qualities:
            parser.error(f"Unknown chord quality {args.chord_quality!r}. Use --list-qualities to inspect options.")
        run_specific(
            scales,
            qualities,
            scale_name=args.scale,
            chord_quality=args.chord_quality,
            tonic_pc=tonic_pc,
            spelling=args.spelling,
            key_signature=args.key_sig,
            include_note_names=include_note_names,
        )
    else:
        run_overview(
            scales,
            qualities,
            tonic_pc=tonic_pc,
            spelling=args.spelling,
            key_signature=args.key_sig,
            include_note_names=include_note_names,
        )


if __name__ == "__main__":
    main()
