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
    ParsedPitch,
    register_scale,
    register_chord,
    chord_brief,
    parse_pitch_token,
)
from mts.analysis.builders import (
    degrees_from_mask,
    mask_from_text,
    match_scale,
    match_chord,
    SESSION_SCALES,
    SESSION_CHORDS,
    load_session_catalog,
    save_session_catalog,
)
def _parse_pitch_list(text: str | None) -> tuple[list[int], list[ParsedPitch]]:
    if text is None:
        return [], []
    parsed: list[ParsedPitch] = []
    for token in text.split(","):
        stripped = token.strip()
        if not stripped:
            continue
        parsed.append(parse_pitch_token(stripped))
    pcs = [item.pc for item in parsed]
    return pcs, parsed


def _detect_context(parsed: list[ParsedPitch]) -> str:
    if any(item.pitch is not None for item in parsed):
        return "absolute"
    if any(item.is_note_token for item in parsed):
        return "note"
    return "abstract"


def _print_context_summary(context: dict[str, object] | None) -> None:
    if not context:
        return
    scope = context.get("scope", "abstract")
    tokens = context.get("tokens") or []
    if scope == "abstract" and not tokens:
        return
    descriptor = scope.capitalize()
    if tokens:
        joined = ", ".join(tokens)
        print(f"  Context: {descriptor} ({joined})")
    else:
        print(f"  Context: {descriptor}")


def resolve_degrees(
    degrees_arg: str | None,
    mask_arg: str | None,
) -> tuple[list[int], tuple[str, ...], tuple[int, ...], str]:
    if mask_arg:
        mask_value = mask_from_text(mask_arg)
        degrees = degrees_from_mask(mask_value)
        if not degrees:
            raise ValueError("Mask does not contain any pitch classes.")
        return degrees, tuple(), tuple(), "abstract"
    pcs, parsed = _parse_pitch_list(degrees_arg)
    if not pcs:
        raise ValueError("Provide either --mask or a comma-separated degree list.")
    degrees = sorted(set(pc % 12 for pc in pcs))
    tokens = tuple(item.token for item in parsed)
    absolute = tuple(item.pitch for item in parsed if item.pitch is not None)
    context = _detect_context(parsed)
    return degrees, tokens, absolute, context


def resolve_intervals(
    intervals_arg: str | None,
    mask_arg: str | None,
) -> tuple[list[int], tuple[str, ...], tuple[int, ...], str]:
    if mask_arg:
        mask_value = mask_from_text(mask_arg)
        intervals = sorted(set(degrees_from_mask(mask_value)))
        if not intervals:
            raise ValueError("Mask does not contain any intervals.")
        return intervals, tuple(), tuple(), "abstract"
    pcs, parsed = _parse_pitch_list(intervals_arg)
    if not pcs:
        raise ValueError("Provide either --mask or a comma-separated interval list.")
    intervals = sorted(set(pc % 12 for pc in pcs))
    tokens = tuple(item.token for item in parsed)
    absolute = tuple(item.pitch for item in parsed if item.pitch is not None)
    context = _detect_context(parsed)
    return intervals, tokens, absolute, context


def scale_command(args: argparse.Namespace) -> None:
    load_session_catalog()
    catalog = load_scales()
    if args.list_session:
        if not SESSION_SCALES:
            print("No session-defined scales.")
        else:
            print("Session-defined scales:")
            for name, scale in sorted(SESSION_SCALES.items()):
                print(f" - {name}: {list(scale.degrees)}")
        return
    if args.clear_session:
        SESSION_SCALES.clear()
        save_session_catalog()
        print("Cleared session-defined scales.")
        return
    degrees, tokens, absolute, context_level = resolve_degrees(args.degrees, args.mask)
    matches = match_scale(degrees, catalog)
    if matches:
        print("Matching catalog scales:")
        for scale in matches:
            print(f" - {scale.name}: {list(scale.degrees)}")
    if args.match_only:
        if not matches:
            print("No catalog matches found.")
        return

    builder = ManualScaleBuilder(
        name=args.name,
        degrees=degrees,
        context=context_level,
        tokens=tokens,
        absolute=absolute,
    )
    result = register_scale(builder, catalog=catalog, persist=True)
    scale = result["scale"]
    if result["match"]:
        print(f"Reusing catalog scale: {scale.name} -> {list(scale.degrees)}")
    else:
        print(f"Registered scale: {scale.name} -> {list(scale.degrees)}")
    _print_context_summary(result.get("context"))


def chord_command(args: argparse.Namespace) -> None:
    load_session_catalog()
    catalog = load_chord_qualities()
    scale_catalog = load_scales()
    if getattr(args, "list_session", False):
        if not SESSION_CHORDS:
            print("No session-defined chord qualities.")
        else:
            print("Session-defined chord qualities:")
            for name, quality in sorted(SESSION_CHORDS.items()):
                print(f" - {name}: {list(quality.intervals)}")
        return
    if getattr(args, "clear_session", False):
        SESSION_CHORDS.clear()
        save_session_catalog()
        print("Cleared session-defined chord qualities.")
        return
    intervals, tokens, absolute, context_level = resolve_intervals(args.intervals, args.mask)
    matches = match_chord(intervals, catalog)
    if matches:
        print("Matching catalog chord qualities:")
        for quality in matches:
            print(f" - {quality.name}: {list(quality.intervals)}")
    if args.match_only:
        if not matches:
            print("No catalog matches found.")
        return

    builder = ManualChordBuilder(
        name=args.name,
        intervals=intervals,
        context=context_level,
        tokens=tokens,
        absolute=absolute,
    )
    result = register_chord(builder, catalog=catalog, persist=True)
    quality = result["quality"]
    if result["match"]:
        print(f"Reusing catalog quality: {quality.name} -> {list(quality.intervals)}")
    else:
        print(f"Registered chord: {quality.name} -> {list(quality.intervals)}")
    _print_context_summary(result.get("context"))
    if getattr(args, "summary", "brief") != "none":
        brief = chord_brief(quality, catalog_scales=scale_catalog)
        for line in brief.as_lines():
            print(f"  {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ad hoc scales or chords for the current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scale_parser = subparsers.add_parser("scale", help="Register or match a manual scale")
    scale_parser.add_argument("--name", help="Optional name; will fall back to placeholder if omitted.")
    scale_parser.add_argument("--degrees", help="Comma-separated pitch classes (0-11).")
    scale_parser.add_argument("--mask", help="12-bit mask in binary or decimal (e.g., 0b101010101010 or 2730).")
    scale_parser.add_argument("--match-only", action="store_true",
                              help="Only display catalog matches without registering.")
    scale_parser.add_argument("--list-session", action="store_true",
                              help="List session-defined scales and exit.")
    scale_parser.add_argument("--clear-session", action="store_true",
                              help="Clear session-defined scales and exit.")

    chord_parser = subparsers.add_parser("chord", help="Register or match a manual chord quality")
    chord_parser.add_argument("--name", help="Optional name; will fall back to placeholder if omitted.")
    chord_parser.add_argument("--intervals", help="Comma-separated intervals (0-11) relative to the root.")
    chord_parser.add_argument("--mask", help="12-bit interval mask in binary or decimal.")
    chord_parser.add_argument("--match-only", action="store_true",
                              help="Only display catalog matches without registering.")
    chord_parser.add_argument("--list-session", action="store_true",
                              help="List session-defined chord qualities and exit.")
    chord_parser.add_argument("--clear-session", action="store_true",
                              help="Clear session-defined chord qualities and exit.")
    chord_parser.add_argument("--summary", choices=["brief", "full", "none"], default="brief",
                              help="Control the post-registration chord summary (default: brief).")

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
