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

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from ..core.scale import Scale
from ..core.quality import ChordQuality


@dataclass
class ManualScaleBuilder:
    name: str
    degrees: List[int]
    tags: Tuple[str, ...] = ()

    def to_scale(self) -> Scale:
        # TODO: expose bitmask constructors for non-12TET systems.
        return Scale.from_degrees(self.name, self.degrees)


@dataclass
class ManualChordBuilder:
    name: str
    intervals: List[int]
    tensions: Tuple[int, ...] = ()

    def to_quality(self) -> ChordQuality:
        # TODO: support arbitrary tuning systems.
        return ChordQuality.from_intervals(self.name, self.intervals, self.tensions)


SESSION_SCALES: Dict[str, Scale] = {}
SESSION_CHORDS: Dict[str, ChordQuality] = {}


def register_scale(builder: ManualScaleBuilder) -> Scale:
    scale = builder.to_scale()
    SESSION_SCALES[scale.name] = scale
    return scale


def register_chord(builder: ManualChordBuilder) -> ChordQuality:
    quality = builder.to_quality()
    SESSION_CHORDS[quality.name] = quality
    return quality

