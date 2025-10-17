from __future__ import annotations

import argparse
import sys
from typing import Optional

from ..io.loaders import load_scales, load_chord_qualities
from ..core.chord import Chord
from ..core.enharmonics import pc_from_name, name_for_pc
from ..layouts.push_grid import PushGrid

def _positive_int_or_none(v: Optional[str]) -> Optional[int]:
    if v is None:
        return None
    return int(v)

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m mts.cli.push",
        description="Render a mock Ableton Push grid with symbolic tokens."
    )
    # Layout / view
    p.add_argument("--preset", choices=["fourths", "thirds", "sequential"], default="fourths",
                   help="Row offset preset: fourths=5, thirds=4, sequential=1 (row-continuing).")
    p.add_argument("--mode", choices=["chromatic", "in_scale"], default="chromatic",
                   help="Chromatic shows all pads; in_scale elides out-of-key pads.")
    p.add_argument("--anchor", choices=["fixed_C", "fixed_root"], default="fixed_C",
                   help="Bottom-left anchored to C or to the root note.")
    p.add_argument("--origin", choices=["upper", "lower"], default="lower",
                   help="Visual origin: upper (top row first) or lower (bottom row first).")
    p.add_argument("--hide-ook", action="store_true",
                   help="When in_scale mode, elide out-of-key pads and fill each row with 8 in-scale pads.")
    p.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                   help="Enable ANSI colors: auto (default), always, or never.")
    p.add_argument("--tonic-mode", choices=["distinct", "blend"], default="distinct",
               help="Color priority for tonic: 'distinct' keeps a unique tonic color; 'blend' lets in-scale color override tonic.")
    # Labels
    p.add_argument("--degrees", action="store_true", help="Use degree labels instead of note names.")
    p.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto",
                   help="Preference for note spelling; 'auto' can be biased via key signature.")
    p.add_argument("--key-sig", type=int, default=0,
                   help="Circle-of-fifths index (-7..+7). Positive favors sharps, negative favors flats, 0 neutral.")
    # Musical context
    p.add_argument("--key", default="C", help="Key/tonic note name (e.g., C, F#, Eb).")
    p.add_argument("--scale", default="Ionian", help="Scale name from data/scales.json (e.g., Ionian, Dorian).")
    # Chord selection (either --chord 'Root:Quality' or --chord-root + --chord-quality)
    p.add_argument("--chord", default=None,
                   help="Chord as 'Root:Quality' (e.g., 'C:maj7', 'G:7', 'D:min7').")
    p.add_argument("--chord-root", default=None, help="Chord root note (e.g., C, F#, Eb).")
    p.add_argument("--chord-quality", default=None, help="Chord quality name from data/chord_qualities.json (e.g., maj7, min7, 7).")
    # Utilities
    p.add_argument("--list-scales", action="store_true", help="List available scales then exit.")
    p.add_argument("--list-qualities", action="store_true", help="List available chord qualities then exit.")
    return p

def main(argv: Optional[list[str]] = None) -> None:
    args = build_arg_parser().parse_args(argv)

    # Load data
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

    # Resolve tonic and scale
    tonic_pc = pc_from_name(args.key)
    if args.scale not in scales:
        raise SystemExit(f"Unknown scale {args.scale!r}. Use --list-scales to see options.")
    scale = scales[args.scale]
    scale_degrees = list(scale.degrees)

    # Resolve chord (root + quality)
    chord_label = "None"
    chord_pcs = []
    chord_spelling = []

    if args.chord:
        # Parse "Root:Quality"
        if ":" not in args.chord:
            raise SystemExit("Use --chord in the form 'Root:Quality', e.g., 'C:maj7' or 'G:7'.")
        root_str, qual_str = args.chord.split(":", 1)
        chord_root_pc = pc_from_name(root_str.strip())
        if qual_str.strip() not in qualities:
            raise SystemExit(f"Unknown chord quality {qual_str!r}. Use --list-qualities to see options.")
        chord = Chord.from_quality(chord_root_pc, qualities[qual_str.strip()])
        chord_label = f"{root_str.strip()}{qual_str.strip()}"
        chord_pcs = list(chord.pcs)
        chord_spelling = chord.spelled()
    elif args.chord_root and args.chord_quality:
        chord_root_pc = pc_from_name(args.chord_root)
        if args.chord_quality not in qualities:
            raise SystemExit(f"Unknown chord quality {args.chord_quality!r}. Use --list-qualities.")
        chord = Chord.from_quality(chord_root_pc, qualities[args.chord_quality])
        chord_label = f"{args.chord_root}{args.chord_quality}"
        chord_pcs = list(chord.pcs)
        chord_spelling = chord.spelled()
    else:
        # No chord: leave empty; grid will show '-' markers
        pass

    # Build grid
    g = PushGrid(
        preset=args.preset,
        anchor=args.anchor,
        origin=args.origin,
        root_pc=tonic_pc,
        tonic_pc=tonic_pc,
        scale_degrees_rel=scale_degrees,
        chord_pcs_abs=chord_pcs,
        layout_mode=args.mode,
        hide_out_of_key=args.hide_ook,
        degree_style=("degrees" if args.degrees else "names"),
        spelling=args.spelling,
        key_signature=args.key_sig,
    )
    g.color_mode = args.color
    g.chord_root_pc = chord_root_pc if 'chord_root_pc' in locals() else None

    # Header
    print(f"\nKey: {args.key}  Scale: {args.scale}  (degrees: {scale_degrees})")
    print(f"Preset: {args.preset}  Mode: {args.mode}  Anchor: {args.anchor}  Origin: {args.origin}")
    print(f"Labels: {'degrees' if args.degrees else 'names'}  Spelling: {args.spelling}  KeySig: {args.key_sig}")

    # Legend (use same ANSI as grid)
    def _paint(s, *, fg=None, bold=False, dim=False):
        ANSI = {
            "reset": "\x1b[0m",
            "bold": "\x1b[1m",
            "dim": "\x1b[2m",
            "fg_black": "\x1b[30m",
            "fg_red": "\x1b[31m",
            "fg_green": "\x1b[32m",
            "fg_yellow": "\x1b[33m",
            "fg_blue": "\x1b[34m",
            "fg_magenta": "\x1b[35m",
            "fg_cyan": "\x1b[36m",
            "fg_white": "\x1b[37m",
            "fg_bright_black": "\x1b[90m",
            "fg_bright_red": "\x1b[91m",
            "fg_bright_green": "\x1b[92m",
            "fg_bright_yellow": "\x1b[93m",
            "fg_bright_blue": "\x1b[94m",
            "fg_bright_magenta": "\x1b[95m",
            "fg_bright_cyan": "\x1b[96m",
            "fg_bright_white": "\x1b[97m",
        }
        parts = []
        if bold:
            parts.append(ANSI["bold"])
        if dim:
            parts.append(ANSI["dim"])
        if fg:
            parts.append(ANSI.get(fg, ""))
        return ("".join(parts) + s + ANSI["reset"]) if parts else s

    use_color = (args.color == "always") or (args.color == "auto" and sys.stdout.isatty())

    if chord_pcs:
        nice_spelling = ", ".join(chord_spelling)
        print(f"Chord: {chord_label}  ->  {nice_spelling}")
    else:
        print("Chord: (none)")

    # Print legend (colored if active)
    if use_color:
        legend = (
            "Legend: "
            + _paint("tonic + chord root", fg="fg_bright_magenta", bold=True) + ", "
            + _paint("tonic in chord", fg="fg_bright_cyan", bold=True) + ", "
            + _paint("tonic", fg="fg_cyan", bold=True) + ", "
            + _paint("chord root (in key)", fg="fg_bright_yellow", bold=True) + ", "
            + _paint("chord root (out of key)", fg="fg_bright_red", bold=True) + ", "
            + _paint("chord tone (in key)", fg="fg_yellow", bold=True) + ", "
            + _paint("chord tone (out of key)", fg="fg_red", bold=True) + ", "
            + _paint("in key", fg="fg_white") + ", "
            + _paint("out of key", fg="fg_bright_black", dim=True)
        )
    else:
        legend = (
            "Legend: tonic + chord root, tonic in chord, tonic, "
            "chord root (in key), chord root (out of key), "
            "chord tone (in key), chord tone (out of key), in key, out of key"
        )
    print(legend)

    # Render
    for line in g.render_lines():
        print(line)


if __name__ == "__main__":
    main()