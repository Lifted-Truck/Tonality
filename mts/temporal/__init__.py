"""Temporal layer: time-bearing events/sequences over the identity model.

Sits above ``core`` and ``analysis`` (it references them; they do not reference
it). Canonical time unit is the quarter-note beat. The chain is
**event → realization → identity key** (ROADMAP Decision 2): read the pitches
sounding across a window as a ``Realization`` and reduce to a key.
"""

from __future__ import annotations

from .tempo import TempoChange, TempoMap
from .meter import TimeSignature, MetricPosition, MeterChange, MeterMap
from .sequence import Event, Sequence
from .segmentation import Segment, HarmonicRhythm, segment, harmonic_rhythm
from .key_tracking import KeyRegion, KeyTrackingResult, KeyWindow, track_keys
from .voice_motion import VoiceMotionResult, VoicePairMotion, voice_motion
from .melodic import MelodicAnalysis, MelodicNoteAtoms, analyze_melody
from .tolerance import CoalesceResult, DroppedEvent, coalesce
from .rhythmic import (
    RhythmicAnalysis,
    RhythmicNoteAtoms,
    SwingAnalysis,
    SwingDivision,
    analyze_rhythm,
    analyze_swing,
)

__all__ = [
    "TempoChange",
    "TempoMap",
    "TimeSignature",
    "MetricPosition",
    "MeterChange",
    "MeterMap",
    "Event",
    "Sequence",
    "Segment",
    "HarmonicRhythm",
    "segment",
    "harmonic_rhythm",
    "KeyRegion",
    "KeyTrackingResult",
    "KeyWindow",
    "track_keys",
    "VoiceMotionResult",
    "VoicePairMotion",
    "voice_motion",
    "MelodicAnalysis",
    "MelodicNoteAtoms",
    "analyze_melody",
    "RhythmicAnalysis",
    "RhythmicNoteAtoms",
    "analyze_rhythm",
    "SwingAnalysis",
    "SwingDivision",
    "analyze_swing",
    "CoalesceResult",
    "DroppedEvent",
    "coalesce",
]
