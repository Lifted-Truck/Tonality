"""Analysis toolkit stubs for scales, chords, and builders.

These modules are intentionally lightweight scaffolding.  They provide
entry points for forthcoming analytical routines (symmetry detection,
enharmonic traversal, etc.) and can be imported from CLI tools or
future GUI/API integrations.
"""

from __future__ import annotations

from .scale_analysis import ScaleAnalysisRequest, analyze_scale
from .chord_analysis import ChordAnalysisRequest, analyze_chord
from .timeline import (
    TimedEvent,
    TimelineAnalysisRequest,
    analyze_timeline,
    generate_sequence,
)
from .builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    register_scale,
    register_chord,
)

__all__ = [
    "ScaleAnalysisRequest",
    "ChordAnalysisRequest",
    "TimelineAnalysisRequest",
    "TimedEvent",
    "ManualScaleBuilder",
    "ManualChordBuilder",
    "analyze_scale",
    "analyze_chord",
    "analyze_timeline",
    "generate_sequence",
    "register_scale",
    "register_chord",
]
