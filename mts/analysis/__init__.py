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
from .containment import find_containers
from .cadence import detect_cadences
from .succession import recommend_next_chord, tag_transition
from .key_induction import candidate_context, disambiguate_relative_key, infer_key
from .meter_estimation import infer_meter
from .naming import name_chord, name_chord_across_keys
from .voice_leading import POLICY_DOUBLING_V1, voice_leading, voice_leading_realized
from .errors import InsufficientInformation, SpecificationError, require_realization
from ..core.realization import Realization
from ..core.spec_level import Registral, SpecLevel, Transpositional
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
    CadenceChord,
    CadenceEvent,
    CadenceResult,
    NextChordCandidate,
    NextChordRecommendation,
    SuccessionEvidence,
    CatalogContainer,
    CatalogContainment,
    ChordAnalysisResult,
    ChordInterpretation,
    ChordInterpretations,
    AnalyticalContextSnapshot,
    ChordIntervalSummary,
    ChordNaming,
    Inversion,
    KeyCandidate,
    KeyInductionResult,
    RelativeKeyDisambiguation,
    RelativeKeyEvidence,
    MeterCandidate,
    MeterEstimationResult,
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
    RealizedVoiceLeading,
    VoiceLeadingResult,
    VoicingAnalysis,
    VoicingEntry,
    VoicingSet,
)

__all__ = [
    "ScaleAnalysisRequest",
    "ChordAnalysisRequest",
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
    "find_containers",
    "CatalogContainer",
    "CatalogContainment",
    "detect_cadences",
    "CadenceChord",
    "CadenceEvent",
    "CadenceResult",
    "recommend_next_chord",
    "tag_transition",
    "NextChordCandidate",
    "NextChordRecommendation",
    "SuccessionEvidence",
    "infer_key",
    "candidate_context",
    "disambiguate_relative_key",
    "infer_meter",
    "KeyCandidate",
    "KeyInductionResult",
    "RelativeKeyDisambiguation",
    "RelativeKeyEvidence",
    "MeterCandidate",
    "MeterEstimationResult",
    "voice_leading",
    "voice_leading_realized",
    "POLICY_DOUBLING_V1",
    "VoiceLeadingResult",
    "RealizedVoiceLeading",
    "name_chord",
    "name_chord_across_keys",
    "AnalyticalContextSnapshot",
    "ChordNaming",
    "MultiKeyNaming",
    "NamingEvidence",
    "NamingUnderKey",
    "RankedInterpretation",
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
