"""Context-aware formatting helpers."""

from __future__ import annotations

from typing import Iterable, Optional

from ..core.enharmonics import name_for_pc
from .context import DisplayContext

_KEY_SIGNATURE_BY_TONIC = {
    0: 0,
    7: 1,
    2: 2,
    9: 3,
    4: 4,
    11: 5,
    6: 6,
    5: -1,
    10: -2,
    3: -3,
    8: -4,
    1: -5,
}

_DEGREE_LABELS = {
    0: "1",
    1: "b2",
    2: "2",
    3: "b3",
    4: "3",
    5: "4",
    6: "#4",
    7: "5",
    8: "b6",
    9: "6",
    10: "b7",
    11: "7",
}

_INTERVAL_LABELS = {
    0: "P1",
    1: "m2",
    2: "M2",
    3: "m3",
    4: "M3",
    5: "P4",
    6: "TT",
    7: "P5",
    8: "m6",
    9: "M6",
    10: "m7",
    11: "M7",
}


def key_signature_for_tonic(tonic_pc: Optional[int]) -> Optional[int]:
    if tonic_pc is None:
        return None
    return _KEY_SIGNATURE_BY_TONIC.get(tonic_pc % 12)


def format_pitch_class(pc: int, context: DisplayContext) -> str:
    spelling = context.get("spelling", "auto")
    key_sig = context.get("key_signature")
    tonic = context.get("tonic_pc")
    if key_sig is None and spelling == "auto" and tonic is not None:
        key_sig = key_signature_for_tonic(tonic)
    return name_for_pc(pc, prefer=spelling, key_signature=key_sig)


def format_degree(pc: int, context: DisplayContext) -> str:
    tonic = context.get("tonic_pc")
    if tonic is None:
        tonic = 0
    rel = (pc - tonic) % 12
    return _DEGREE_LABELS.get(rel, f"pc{rel}")


def format_interval(pc: int, context: DisplayContext) -> str:
    root = context.get("chord_root_pc")
    if root is None:
        root = context.get("tonic_pc") or 0
    rel = (pc - root) % 12
    return _INTERVAL_LABELS.get(rel, str(rel))


def format_semitone(pc: int, context: DisplayContext) -> str:
    base = context.get("tonic_pc")
    if base is None:
        base = context.get("chord_root_pc")
    if base is None:
        base = 0
    return str((pc - base) % 12)


def resolve_label(pc: int, context: DisplayContext, *, mode: Optional[str] = None) -> str:
    actual_mode = mode or context.get("label_mode", "names")
    if actual_mode == "degrees":
        return format_degree(pc, context)
    if actual_mode == "intervals":
        return format_interval(pc, context)
    if actual_mode == "semitones":
        return format_semitone(pc, context)
    return format_pitch_class(pc, context)


def update_context_with_scale(context: DisplayContext, tonic_pc: Optional[int], degrees: Iterable[int]) -> None:
    context.set("tonic_pc", tonic_pc, layer="session")
    context.set("scale_degrees", list(degrees) if degrees is not None else None, layer="session")
    if context.get("spelling", "auto") == "auto":
        key_sig = key_signature_for_tonic(tonic_pc)
        context.set("key_signature", key_sig, layer="session")


def update_context_with_chord_root(context: DisplayContext, root_pc: Optional[int]) -> None:
    context.set("chord_root_pc", root_pc, layer="session")


__all__ = [
    "format_pitch_class",
    "format_degree",
    "format_interval",
    "format_semitone",
    "resolve_label",
    "update_context_with_scale",
    "update_context_with_chord_root",
]
