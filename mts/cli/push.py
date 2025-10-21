from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from ..io.loaders import load_scales, load_chord_qualities, load_function_mappings, FunctionMapping
from ..core.chord import Chord
from ..core.enharmonics import pc_from_name, name_for_pc
from ..layouts.push_grid import PushGrid
from ..theory import functions as fn_defs

_FUNCTION_FEATURE_CHOICES = sorted(
    {
        fn_defs.FEATURE_ADDED_TONES,
        fn_defs.FEATURE_ALTERED_DOMINANT,
        fn_defs.FEATURE_EXTENDED,
        fn_defs.FEATURE_LEADING_TONE,
        fn_defs.FEATURE_LYDIAN_EXTENSIONS,
        fn_defs.FEATURE_POWER_DYADS,
        fn_defs.FEATURE_RAISED_SIXTH,
        fn_defs.FEATURE_SIXTH_CHORDS,
        fn_defs.FEATURE_SUSPENDED,
        fn_defs.FEATURE_PARALLEL_MAJOR,
        fn_defs.FEATURE_PARALLEL_MINOR,
    }
)


def _infer_function_mode(scale_name: str) -> str | None:
    normalized = scale_name.lower()
    if normalized in {"ionian", "major"}:
        return "major"
    if normalized in {"natural minor", "aeolian"}:
        return "minor"
    return None


def _print_function_catalog(mode: str, mappings: Iterable[FunctionMapping]) -> None:
    print(f"\nFunctional catalog for mode '{mode}':")
    for item in mappings:
        tags = f" [{', '.join(item.tags)}]" if item.tags else ""
        intervals = ",".join(str(iv) for iv in item.intervals)
        print(
            f"  degree_pc={item.degree_pc:2d} "
            f"label={item.modal_label:<10} "
            f"quality={item.chord_quality:<10} "
            f"role={item.role:<12} "
            f"intervals=[{intervals}]"
            f"{tags}"
        )

def _positive_int_or_none(v: str | None) -> int | None:
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
    p.add_argument("--blocks", action="store_true",
                   help="After the text grid, print a compact color-block grid.")
    p.add_argument("--block-char", default="■",
                   help="Glyph for the block grid (e.g., ■ ● □ ▣). Default: ■")

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
    p.add_argument("--list-functions", action="store_true",
                   help="List generated functional mappings for the selected mode then exit.")
    p.add_argument("--strict-in-scale", dest="strict_in_scale", action="store_true", default=True,
               help="(default: on) When mode=in_scale, abort if the chord contains out-of-key tones. Use --no-strict-in-scale to disable.")
    p.add_argument("--no-strict-in-scale", dest="strict_in_scale", action="store_false",
               help="Disable strict in-scale validation (allow chords with out-of-key tones).")
    # Functional catalog controls
    p.add_argument("--functions-mode", choices=["major", "minor", "both"], default=None,
                   help="Template set to use when listing functional mappings. "
                        "Defaults to both major and minor unless specified.")
    p.add_argument("--functions-feature", action="append", default=[],
                   choices=_FUNCTION_FEATURE_CHOICES,
                   help="Enable additional functional features (repeatable).")
    p.add_argument("--functions-include-borrowed", dest="functions_include_borrowed",
                   action="store_true", default=None,
                   help="Force borrowed chords to be included when listing functional mappings.")
    p.add_argument("--functions-no-borrowed", dest="functions_include_borrowed",
                   action="store_false",
                   help="Force borrowed chords to be excluded when listing functional mappings.")
    return p

def main(argv: list[str] | None = None) -> None:
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
    if args.list_functions:
        if args.functions_mode:
            mode_selection = ["major", "minor"] if args.functions_mode == "both" else [args.functions_mode]
        else:
            mode_selection = ["major", "minor"]

        for idx, mode in enumerate(mode_selection):
            if idx:
                print()
            mappings = load_function_mappings(
                mode,
                features=args.functions_feature,
                include_borrowed=args.functions_include_borrowed,
            )
            _print_function_catalog(mode, mappings)
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

    # --- In-scale sanity check: warn or error if chord contains out-of-key tones ---
    if args.mode == "in_scale" and chord_pcs:
        relset = set(scale_degrees)  # degrees relative to tonic (0..11)
        # find out-of-key chord pcs relative to tonic
        ook_abs = [pc for pc in chord_pcs if ((pc - tonic_pc) % 12) not in relset]

        if ook_abs:
            # pretty-print names with current spelling prefs
            ook_names = [name_for_pc(pc, prefer=args.spelling, key_signature=args.key_sig) for pc in ook_abs]
            root_is_ook = ('chord_root_pc' in locals()) and (((chord_root_pc - tonic_pc) % 12) not in relset)

            # tiny ANSI helper (CLI-only)
            def _warn_paint(text, *, fg=None, bold=False, dim=False):
                ANSI = {
                    "reset": "\x1b[0m", "bold": "\x1b[1m", "dim": "\x1b[2m",
                    "fg_yellow": "\x1b[33m", "fg_red": "\x1b[31m",
                    "fg_bright_red": "\x1b[91m", "fg_bright_black": "\x1b[90m",
                }
                parts = []
                if bold: parts.append(ANSI["bold"])
                if dim: parts.append(ANSI["dim"])
                if fg: parts.append(ANSI[fg])
                return ("".join(parts) + text + ANSI["reset"]) if parts else text

            summary = ", ".join(ook_names)
            extra = " " + _warn_paint("(root is out of key)", fg="fg_bright_red", bold=True) if root_is_ook else ""

            if args.strict_in_scale:
                print(_warn_paint("ERROR: ", fg="fg_bright_red", bold=True) +
                      f"Chord contains out-of-key tones in in_scale mode: {summary}{extra}")
                import sys as _sys
                _sys.exit(2)
            else:
                print(_warn_paint("Warning: ", fg="fg_yellow", bold=True) +
                      f"Chord contains out-of-key tones: {summary}{extra}")
                if args.hide_ook:
                    print(_warn_paint("Note: out-of-key pads will be elided in this view.",
                                      fg="fg_bright_black", dim=True))


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

    # Render text grid
    for line in g.render_lines():
        print(line)

    # Optional compact color-block grid
    if args.blocks:
        print()  # spacer
        for line in g.render_block_lines(char=args.block_char):
            print(line)

if __name__ == "__main__":
    main()
