"""Summary helpers for compact chord/scale analytics."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Mapping, Any

from .chord_analysis import ChordAnalysisRequest, analyze_chord
from ..core.chord import Chord
from ..core.quality import ChordQuality
from ..core.scale import Scale


@dataclass
class ChordBrief:
    interval_fingerprint: str
    compatible_scales: list[str]
    functional_roles: list[str]

    def as_lines(self) -> list[str]:
        lines = [f"Intervals: {self.interval_fingerprint}"]
        if self.compatible_scales:
            lines.append(f"Fits in: {', '.join(self.compatible_scales)}")
        if self.functional_roles:
            lines.append(f"Functions: {', '.join(self.functional_roles)}")
        return lines


@lru_cache(maxsize=None)
def _function_mappings(mode: str) -> list[Any]:
    from ..io.loaders import load_function_mappings

    return load_function_mappings(mode)


def chord_brief(
    quality: ChordQuality,
    *,
    catalog_scales: Mapping[str, Scale] | None = None,
    max_scales: int = 3,
) -> ChordBrief:
    chord = Chord.from_quality(0, quality)
    analysis = analyze_chord(
        ChordAnalysisRequest(
            chord=chord,
            include_inversions=True,
            include_voicings=False,
            include_enharmonics=False,
        )
    )

    histogram: dict[int, int] = analysis.get("interval_class_histogram_numeric", {})
    fingerprint = _format_interval_fingerprint(histogram, limit=3)

    if catalog_scales is None:
        from ..io.loaders import load_scales

        scales = load_scales()
    else:
        scales = catalog_scales
    compatible = _compatibility_snapshot(quality, scales.values(), max_scales=max_scales)

    roles = _functional_alignment(quality.name)

    return ChordBrief(
        interval_fingerprint=fingerprint,
        compatible_scales=compatible,
        functional_roles=roles,
    )


def _format_interval_fingerprint(histogram: dict[int, int], limit: int) -> str:
    ordered = sorted(histogram.items(), key=lambda item: (-item[1], item[0]))
    parts = [f"ic{ic}:{count}" for ic, count in ordered if count > 0]
    if len(parts) > limit:
        parts = parts[:limit]
    return ", ".join(parts) if parts else "none"


def _compatibility_snapshot(
    quality: ChordQuality,
    scales: Iterable[Scale],
    *,
    max_scales: int,
) -> list[str]:
    snapshot: list[tuple[str, tuple[int, ...]]] = []
    for scale in scales:
        if scale.name.lower() == "chromatic":
            continue
        roots = _compatibility_roots(scale, quality)
        if not roots:
            continue
        snapshot.append((scale.name, roots))
    snapshot.sort(key=lambda item: (-len(item[1]), item[0]))
    # TODO: annotate each scale entry with diatonic/borrowed status relative to a workspace context.
    formatted: list[str] = []
    for name, roots in snapshot[:max_scales]:
        display = ", ".join(str(r) for r in roots)
        formatted.append(f"{name} (roots {display})")
    return formatted


@lru_cache(maxsize=2048)
def _compatibility_roots(scale: Scale, quality: ChordQuality) -> tuple[int, ...]:
    from ..core.bitmask import mask_from_pcs, is_subset

    roots: list[int] = []
    base_intervals = tuple(quality.intervals)
    for root in range(12):
        pcs = [((iv + root) % 12) for iv in base_intervals]
        if is_subset(mask_from_pcs(pcs), scale.mask):
            roots.append(root)
    return tuple(roots)


def _functional_alignment(chord_quality_name: str) -> list[str]:
    roles: list[str] = []
    for mode in ("major", "minor"):
        for mapping in _function_mappings(mode):
            if mapping.chord_quality == chord_quality_name:
                descriptor = f"{mode}: {mapping.modal_label} ({mapping.role})"
                if descriptor not in roles:
                    roles.append(descriptor)
    return roles
