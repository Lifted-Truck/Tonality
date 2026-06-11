"""Analysis toolkit stubs for scales, chords, and builders.

These modules are intentionally lightweight scaffolding.  They provide
entry points for forthcoming analytical routines (symmetry detection,
enharmonic traversal, etc.) and can be imported from CLI tools or
future GUI/API integrations.
"""

from __future__ import annotations

from .scale_analysis import ScaleAnalysisRequest, analyze_scale
from .chord_analysis import ChordAnalysisRequest, analyze_chord, analyze_voicing
from .voicings import suggest_voicings
from .equivalence import interpret_chord
from .analytical_context import AnalyticalContext, ChordInKey, contextualize_chord
from .key_induction import candidate_context, infer_key
from .naming import name_chord, name_chord_across_keys
from .voice_leading import POLICY_DOUBLING_V1, voice_leading
from .errors import SpecificationError, require_realization
from ..core.realization import Realization
from ..core.spec_level import Registral, SpecLevel, Transpositional
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
from .specs import (
    ChordSpec,
    ChordParseResult,
    ScopeLiteral,
    QualityVariant,
    parse_chord_spec,
    from_scope,
    to_scope,
)
from .results import (
    ChordAnalysisResult,
    ChordInterpretation,
    ChordInterpretations,
    AnalyticalContextSnapshot,
    ChordIntervalSummary,
    ChordNaming,
    Inversion,
    KeyCandidate,
    KeyInductionResult,
    ModeRotation,
    MultiKeyNaming,
    NamingEvidence,
    NamingUnderKey,
    RankedInterpretation,
    ReflectionAxis,
    ScaleAnalysisResult,
    ScaleIntervalSummary,
    SetClassData,
    SymmetryData,
    TonnetzAnalysis,
    TonicContext,
    VoiceLeadingResult,
    VoicingAnalysis,
    VoicingEntry,
    VoicingSet,
)

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
    "from_scope",
    "to_scope",
    "SpecLevel",
    "Transpositional",
    "Registral",
    "Realization",
    "SpecificationError",
    "require_realization",
    "ManualScaleBuilder",
    "ManualChordBuilder",
    "analyze_scale",
    "analyze_chord",
    "analyze_voicing",
    "suggest_voicings",
    "interpret_chord",
    "AnalyticalContext",
    "ChordInKey",
    "contextualize_chord",
    "infer_key",
    "candidate_context",
    "KeyCandidate",
    "KeyInductionResult",
    "voice_leading",
    "POLICY_DOUBLING_V1",
    "VoiceLeadingResult",
    "name_chord",
    "name_chord_across_keys",
    "AnalyticalContextSnapshot",
    "ChordNaming",
    "MultiKeyNaming",
    "NamingEvidence",
    "NamingUnderKey",
    "RankedInterpretation",
    "analyze_timeline",
    "generate_sequence",
    "parse_pitch_token",
    "chord_brief",
    "parse_chord_spec",
    "compare_chord_qualities",
    "register_scale",
    "register_chord",
    "ChordAnalysisResult",
    "ChordInterpretation",
    "ChordInterpretations",
    "ChordIntervalSummary",
    "Inversion",
    "ModeRotation",
    "ReflectionAxis",
    "ScaleAnalysisResult",
    "ScaleIntervalSummary",
    "SetClassData",
    "SymmetryData",
    "TonnetzAnalysis",
    "TonicContext",
    "VoicingAnalysis",
    "VoicingEntry",
    "VoicingSet",
]
