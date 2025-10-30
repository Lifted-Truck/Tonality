"""Chord comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from ..core.bitmask import mask_from_pcs, is_subset
from ..core.quality import ChordQuality
from ..core.scale import Scale
from .summaries import chord_brief

ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def _compatibility_roots(scale: Scale, quality: ChordQuality) -> tuple[int, ...]:
    """Return root positions (0..11) where the chord quality fits inside the scale."""

    roots: list[int] = []
    intervals = tuple(quality.intervals)
    for root in range(12):
        pcs = [((root + iv) % 12) for iv in intervals]
        if is_subset(mask_from_pcs(pcs), scale.mask):
            roots.append(root)
    return tuple(roots)


def _degree_labels(scale: Scale, chord_pcs: Sequence[int]) -> list[str]:
    labels: list[str] = []
    degrees = list(scale.degrees)
    for pc in chord_pcs:
        if pc in degrees:
            idx = degrees.index(pc)
            if idx < len(ROMANS):
                labels.append(ROMANS[idx])
            else:
                labels.append(str(idx + 1))
        else:
            labels.append("(out)")
    return labels


@dataclass(frozen=True)
class ScaleChordPlacement:
    scale: str
    roots_a: tuple[int, ...]
    roots_b: tuple[int, ...]
    shared_roots: tuple[int, ...]
    degree_map_a: Mapping[int, list[str]]
    degree_map_b: Mapping[int, list[str]]


@dataclass(frozen=True)
class ChordComparison:
    quality_a: str
    quality_b: str
    interval_fingerprint_a: str
    interval_fingerprint_b: str
    intervals_only_a: tuple[int, ...]
    intervals_only_b: tuple[int, ...]
    shared_scales: list[ScaleChordPlacement]
    unique_to_a: tuple[str, ...]
    unique_to_b: tuple[str, ...]


def compare_chord_qualities(
    quality_a: ChordQuality,
    quality_b: ChordQuality,
    *,
    catalog_scales: Mapping[str, Scale] | None = None,
    include_scales: Iterable[str] | None = None,
) -> ChordComparison:
    """Compare two chord qualities across the scale catalog."""

    if catalog_scales is None:
        from ..io.loaders import load_scales

        catalog_scales = load_scales()

    scales = dict(catalog_scales)
    if include_scales:
        include = {name for name in include_scales if name in scales}
        scales = {name: scale for name, scale in scales.items() if name in include}

    brief_a = chord_brief(quality_a, catalog_scales=scales)
    brief_b = chord_brief(quality_b, catalog_scales=scales)

    intervals_a = tuple(sorted(set(quality_a.intervals)))
    intervals_b = tuple(sorted(set(quality_b.intervals)))
    only_a = tuple(sorted(set(intervals_a) - set(intervals_b)))
    only_b = tuple(sorted(set(intervals_b) - set(intervals_a)))

    shared_scales: list[ScaleChordPlacement] = []
    unique_a: list[str] = []
    unique_b: list[str] = []

    for name, scale in sorted(scales.items()):
        if scale.name.lower() == "chromatic":
            continue
        roots_a = _compatibility_roots(scale, quality_a)
        roots_b = _compatibility_roots(scale, quality_b)

        if roots_a and roots_b:
            chord_map_a = {
                root: _degree_labels(scale, [((root + iv) % 12) for iv in quality_a.intervals])
                for root in roots_a
            }
            chord_map_b = {
                root: _degree_labels(scale, [((root + iv) % 12) for iv in quality_b.intervals])
                for root in roots_b
            }
            shared_scales.append(
                ScaleChordPlacement(
                    scale=name,
                    roots_a=roots_a,
                    roots_b=roots_b,
                    shared_roots=tuple(sorted(set(roots_a) & set(roots_b))),
                    degree_map_a=chord_map_a,
                    degree_map_b=chord_map_b,
                )
            )
        elif roots_a:
            unique_a.append(name)
        elif roots_b:
            unique_b.append(name)

    return ChordComparison(
        quality_a=quality_a.name,
        quality_b=quality_b.name,
        interval_fingerprint_a=brief_a.interval_fingerprint,
        interval_fingerprint_b=brief_b.interval_fingerprint,
        intervals_only_a=only_a,
        intervals_only_b=only_b,
        shared_scales=shared_scales,
        unique_to_a=tuple(sorted(unique_a)),
        unique_to_b=tuple(sorted(unique_b)),
    )


__all__ = [
    "ChordComparison",
    "ScaleChordPlacement",
    "compare_chord_qualities",
]
