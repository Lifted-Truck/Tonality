"""Manual scale/chord builder scaffolding.

These helper classes give the CLI and future GUI/API layers a single
place to manage ad hoc user-defined objects.  They currently hold
session-local registries and basic validation hooks.

TODO:
    - Integrate with persistence once the scale/chord databases expand.
    - Provide binary/decimal bitmask parsing helpers.
    - Surface matching algorithms for nearest known scales/chords.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from pathlib import Path
import json
import os
import sys
from typing import Iterable, Mapping, Sequence

from ..core.bitmask import mask_from_pcs, pcs_from_mask
from ..core.enharmonics import pc_from_name
from ..core.pitch import Pitch
from ..core.scale import Scale
from ..core.quality import ChordQuality


@dataclass
class ManualScaleBuilder:
    name: str | None
    degrees: Sequence[int | str]
    tags: tuple[str, ...] = ()
    context: str = "abstract"
    tokens: tuple[str, ...] = ()
    absolute: tuple[Pitch, ...] = ()

    def to_scale(self) -> Scale:
        # TODO: expose bitmask constructors for non-12TET systems.
        normalized = _normalize_degrees(self.degrees)
        name = self.name or _placeholder_name("ManualScale", SESSION_SCALES, ())
        return Scale.from_degrees(name, normalized)


@dataclass
class ManualChordBuilder:
    name: str | None
    intervals: Sequence[int | str]
    tensions: Sequence[int | str] = ()
    context: str = "abstract"
    tokens: tuple[str, ...] = ()
    absolute: tuple[Pitch, ...] = ()

    def to_quality(self) -> ChordQuality:
        # TODO: support arbitrary tuning systems.
        normalized_intervals = _normalize_intervals(self.intervals)
        normalized_tensions = tuple(_normalize_degrees(self.tensions)) if self.tensions else ()
        name = self.name or _placeholder_name("ManualChord", SESSION_CHORDS, ())
        return ChordQuality.from_intervals(name, normalized_intervals, normalized_tensions)


SESSION_SCALES: dict[str, Scale] = {}
SESSION_CHORDS: dict[str, ChordQuality] = {}
SESSION_SCALE_CONTEXT: dict[str, dict[str, object]] = {}
SESSION_CHORD_CONTEXT: dict[str, dict[str, object]] = {}

DEFAULT_SESSION_PATH = Path(__file__).resolve().parents[2] / ".tonality_session.json"
SESSION_FILE = Path(os.environ.get("TONALITY_SESSION_FILE", DEFAULT_SESSION_PATH))
_SAVE_SESSION_ERROR_REPORTED = False


def _placeholder_name(stem: str, registry: Mapping[str, object], existing: Iterable[str]) -> str:
    taken = set(registry.keys()) | set(existing)
    for idx in count(1):
        candidate = f"{stem}-{idx}"
        if candidate not in taken:
            return candidate
    return stem


def _builder_context_payload(builder) -> dict[str, object]:
    scope = getattr(builder, "context", "abstract") or "abstract"
    tokens = list(getattr(builder, "tokens", ()))
    absolute = [pitch.midi for pitch in getattr(builder, "absolute", ()) if pitch is not None]
    payload: dict[str, object] = {"scope": scope}
    if tokens:
        payload["tokens"] = tokens
    if absolute:
        payload["absolute_midi"] = absolute
    return payload


def _normalize_degrees(degrees: Iterable[int | str]) -> list[int]:
    normalized: set[int] = set()
    for value in degrees:
        if isinstance(value, str):
            normalized.add(pc_from_name(value))
        else:
            normalized.add(int(value) % 12)
    return sorted(normalized)


def _normalize_intervals(intervals: Iterable[int | str]) -> list[int]:
    normalized: set[int] = set()
    for value in intervals:
        if isinstance(value, str):
            normalized.add(pc_from_name(value))
        else:
            normalized.add(int(value) % 12)
    return sorted(normalized)


def match_scale(degrees: Iterable[int], catalog: Mapping[str, Scale]) -> list[Scale]:
    target = _normalize_degrees(degrees)
    target_mask = mask_from_pcs(target)
    matches: list[Scale] = []
    seen: set[str] = set()
    for scale in catalog.values():
        if mask_from_pcs(scale.degrees) == target_mask:
            if scale.name not in seen:
                seen.add(scale.name)
                matches.append(scale)
    return matches


def match_chord(intervals: Iterable[int], catalog: Mapping[str, ChordQuality]) -> list[ChordQuality]:
    target = _normalize_intervals(intervals)
    matches: list[ChordQuality] = []
    seen: set[str] = set()
    for quality in catalog.values():
        if _normalize_intervals(quality.intervals) == target:
            if quality.name not in seen:
                seen.add(quality.name)
                matches.append(quality)
    return matches


def register_scale(
    builder: ManualScaleBuilder,
    *,
    catalog: Mapping[str, Scale] | None = None,
    auto_placeholder: bool = True,
    persist: bool = False,
    session_path: Path | None = None,
) -> dict[str, object]:
    catalog = catalog or {}
    context_payload = _builder_context_payload(builder)
    matches = match_scale(builder.degrees, catalog)
    if matches:
        scale = matches[0]
        SESSION_SCALES[scale.name] = scale
        return {"scale": scale, "match": matches, "context": context_payload}

    scale = builder.to_scale()
    if auto_placeholder and (scale.name in catalog or scale.name in SESSION_SCALES):
        placeholder = _placeholder_name("ManualScale", SESSION_SCALES, catalog.keys())
        scale = Scale.from_degrees(placeholder, builder.degrees)
    SESSION_SCALES[scale.name] = scale
    SESSION_SCALE_CONTEXT[scale.name] = context_payload
    if persist:
        save_session_catalog(session_path)
    return {"scale": scale, "match": [], "context": context_payload}


def register_chord(
    builder: ManualChordBuilder,
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
    auto_placeholder: bool = True,
    persist: bool = False,
    session_path: Path | None = None,
) -> dict[str, object]:
    catalog = catalog or {}
    context_payload = _builder_context_payload(builder)
    matches = match_chord(builder.intervals, catalog)
    if matches:
        quality = matches[0]
        SESSION_CHORDS[quality.name] = quality
        return {"quality": quality, "match": matches, "context": context_payload}

    quality = builder.to_quality()
    if auto_placeholder and (quality.name in catalog or quality.name in SESSION_CHORDS):
        placeholder = _placeholder_name("ManualChord", SESSION_CHORDS, catalog.keys())
        quality = ChordQuality.from_intervals(placeholder, builder.intervals, builder.tensions)
    SESSION_CHORDS[quality.name] = quality
    SESSION_CHORD_CONTEXT[quality.name] = context_payload
    if persist:
        save_session_catalog(session_path)
    return {"quality": quality, "match": [], "context": context_payload}


def degrees_from_mask(mask: int) -> list[int]:
    """Convert a pitch-class mask into normalized degrees."""

    return pcs_from_mask(mask)


def mask_from_text(text: str) -> int:
    """Parse a decimal or binary mask string."""

    stripped = text.strip().lower()
    base = 2 if stripped.startswith("0b") or set(stripped) <= {"0", "1"} else 10
    if stripped.startswith("0b"):
        stripped = stripped[2:]
    value = int(stripped, base)
    return value & ((1 << 12) - 1)


def is_session_scale(name: str) -> bool:
    """Return True if the scale name was registered in this session."""

    return name in SESSION_SCALES


def is_session_chord(name: str) -> bool:
    """Return True if the chord name was registered in this session."""

    return name in SESSION_CHORDS


def load_session_catalog(path: Path | None = None) -> None:
    """Load session-defined scales/chords from disk."""

    target = path or SESSION_FILE
    if not target.exists():
        return
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return
    for entry in data.get("scales", []):
        name = entry.get("name")
        degrees = entry.get("degrees", [])
        if name:
            try:
                scale_builder = ManualScaleBuilder(name=name, degrees=list(degrees))
                scale = scale_builder.to_scale()
            except Exception:
                continue
            SESSION_SCALES[scale.name] = scale
            context_payload = {
                "scope": entry.get("context", "abstract"),
                "tokens": entry.get("tokens", []),
            }
            absolute_midi = entry.get("absolute_midi", [])
            if absolute_midi:
                context_payload["absolute_midi"] = list(absolute_midi)
            SESSION_SCALE_CONTEXT[scale.name] = context_payload
    for entry in data.get("chords", []):
        name = entry.get("name")
        intervals = entry.get("intervals", [])
        tensions = entry.get("tensions", [])
        if name:
            try:
                chord_builder = ManualChordBuilder(name=name, intervals=list(intervals), tensions=tuple(tensions))
                quality = chord_builder.to_quality()
            except Exception:
                continue
            SESSION_CHORDS[quality.name] = quality
            context_payload = {
                "scope": entry.get("context", "abstract"),
                "tokens": entry.get("tokens", []),
            }
            absolute_midi = entry.get("absolute_midi", [])
            if absolute_midi:
                context_payload["absolute_midi"] = list(absolute_midi)
            SESSION_CHORD_CONTEXT[quality.name] = context_payload


def save_session_catalog(path: Path | None = None) -> None:
    """Persist session-defined scales/chords to disk."""

    target = path or SESSION_FILE
    payload = {
        "scales": [
            {
                "name": scale.name,
                "degrees": list(scale.degrees),
                "context": SESSION_SCALE_CONTEXT.get(scale.name, {}).get("scope", "abstract"),
                "tokens": SESSION_SCALE_CONTEXT.get(scale.name, {}).get("tokens", []),
                "absolute_midi": SESSION_SCALE_CONTEXT.get(scale.name, {}).get("absolute_midi", []),
            }
            for scale in SESSION_SCALES.values()
        ],
        "chords": [
            {
                "name": quality.name,
                "intervals": list(quality.intervals),
                "tensions": list(getattr(quality, "tensions", ()) or ()),
                "context": SESSION_CHORD_CONTEXT.get(quality.name, {}).get("scope", "abstract"),
                "tokens": SESSION_CHORD_CONTEXT.get(quality.name, {}).get("tokens", []),
                "absolute_midi": SESSION_CHORD_CONTEXT.get(quality.name, {}).get("absolute_midi", []),
            }
            for quality in SESSION_CHORDS.values()
        ],
    }
    global _SAVE_SESSION_ERROR_REPORTED
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        if not _SAVE_SESSION_ERROR_REPORTED:
            print("Warning: Unable to persist session catalog.", file=sys.stderr)
            _SAVE_SESSION_ERROR_REPORTED = True


try:
    load_session_catalog()
except Exception:
    pass
