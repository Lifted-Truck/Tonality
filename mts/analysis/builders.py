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
from typing import Iterable, Mapping

from ..core.bitmask import mask_from_pcs, pcs_from_mask
from ..core.scale import Scale
from ..core.quality import ChordQuality


@dataclass
class ManualScaleBuilder:
    name: str | None
    degrees: list[int]
    tags: tuple[str, ...] = ()

    def to_scale(self) -> Scale:
        # TODO: expose bitmask constructors for non-12TET systems.
        name = self.name or _placeholder_name("ManualScale", SESSION_SCALES, ())
        return Scale.from_degrees(name, self.degrees)


@dataclass
class ManualChordBuilder:
    name: str | None
    intervals: list[int]
    tensions: tuple[int, ...] = ()

    def to_quality(self) -> ChordQuality:
        # TODO: support arbitrary tuning systems.
        name = self.name or _placeholder_name("ManualChord", SESSION_CHORDS, ())
        return ChordQuality.from_intervals(name, self.intervals, self.tensions)


SESSION_SCALES: dict[str, Scale] = {}
SESSION_CHORDS: dict[str, ChordQuality] = {}


def _placeholder_name(stem: str, registry: Mapping[str, object], existing: Iterable[str]) -> str:
    taken = set(registry.keys()) | set(existing)
    for idx in count(1):
        candidate = f"{stem}-{idx}"
        if candidate not in taken:
            return candidate
    return stem


def _normalize_degrees(degrees: Iterable[int]) -> list[int]:
    return sorted({int(pc) % 12 for pc in degrees})


def _normalize_intervals(intervals: Iterable[int]) -> list[int]:
    return sorted({int(iv) % 12 for iv in intervals})


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
) -> dict[str, object]:
    catalog = catalog or {}
    matches = match_scale(builder.degrees, catalog)
    if matches:
        scale = matches[0]
        SESSION_SCALES[scale.name] = scale
        return {"scale": scale, "match": matches}

    scale = builder.to_scale()
    if auto_placeholder and (scale.name in catalog or scale.name in SESSION_SCALES):
        placeholder = _placeholder_name("ManualScale", SESSION_SCALES, catalog.keys())
        scale = Scale.from_degrees(placeholder, builder.degrees)
    SESSION_SCALES[scale.name] = scale
    return {"scale": scale, "match": []}


def register_chord(
    builder: ManualChordBuilder,
    *,
    catalog: Mapping[str, ChordQuality] | None = None,
    auto_placeholder: bool = True,
) -> dict[str, object]:
    catalog = catalog or {}
    matches = match_chord(builder.intervals, catalog)
    if matches:
        quality = matches[0]
        SESSION_CHORDS[quality.name] = quality
        return {"quality": quality, "match": matches}

    quality = builder.to_quality()
    if auto_placeholder and (quality.name in catalog or quality.name in SESSION_CHORDS):
        placeholder = _placeholder_name("ManualChord", SESSION_CHORDS, catalog.keys())
        quality = ChordQuality.from_intervals(placeholder, builder.intervals, builder.tensions)
    SESSION_CHORDS[quality.name] = quality
    return {"quality": quality, "match": []}


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
