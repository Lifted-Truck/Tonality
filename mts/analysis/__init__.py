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
from .summaries import ChordBrief, chord_brief
from ..core.pitch import Pitch, parse_pitch_token, ParsedPitch
from .builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    register_scale,
    register_chord,
)
from .comparisons import (
    ChordComparison,
    ScaleChordPlacement,
    compare_chord_qualities,
)
from .specs import ChordSpec, ChordParseResult, ScopeLiteral, QualityVariant, parse_chord_spec

__all__ = [
    "ScaleAnalysisRequest",
    "ChordAnalysisRequest",
    "TimelineAnalysisRequest",
    "TimedEvent",
    "Pitch",
    "ParsedPitch",
    "ChordBrief",
    "ChordComparison",
    "ScaleChordPlacement",
    "ChordSpec",
    "ChordParseResult",
    "ScopeLiteral",
    "QualityVariant",
    "ManualScaleBuilder",
    "ManualChordBuilder",
    "analyze_scale",
    "analyze_chord",
    "analyze_timeline",
    "generate_sequence",
    "parse_pitch_token",
    "chord_brief",
    "parse_chord_spec",
    "compare_chord_qualities",
    "register_scale",
    "register_chord",
]
