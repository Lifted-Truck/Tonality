"""Analysis toolkit stubs for scales, chords, and builders.

These modules are intentionally lightweight scaffolding.  They provide
entry points for forthcoming analytical routines (symmetry detection,
enharmonic traversal, etc.) and can be imported from CLI tools or
future GUI/API integrations.
"""

from __future__ import annotations

from .scale_analysis import ScaleAnalysisRequest, analyze_scale
from .chord_analysis import ChordAnalysisRequest, analyze_chord
from .builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    register_scale,
    register_chord,
)

__all__ = [
    "ScaleAnalysisRequest",
    "ChordAnalysisRequest",
    "ManualScaleBuilder",
    "ManualChordBuilder",
    "analyze_scale",
    "analyze_chord",
    "register_scale",
    "register_chord",
]
