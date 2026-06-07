"""Timeline analysis scaffolding — DEPRECATED stub.

Superseded by the real temporal layer in :mod:`mts.temporal` (Phase 2 Slice 1),
which provides ``Event`` / ``Sequence`` with tempo + meter and the
event → realization → identity-key reduction. This stub remains only for the
legacy ``workspace.analyze_timeline`` path pending its migration onto
``mts.temporal`` (a tracked Phase 2 follow-up). Do not build new code on these
placeholder types — import from ``mts.temporal`` instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Any


@dataclass
class TimedEvent:
    """Placeholder for a single time-based event (note, chord, control change)."""

    onset: float  # seconds or beats; interpretation TBD
    duration: float
    payload: Mapping[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()


@dataclass
class TimelineAnalysisRequest:
    """Container describing which timeline analytics to run."""

    events: Iterable[TimedEvent]
    sample_rate: float | None = None
    tempo_bpm: float | None = None
    meter: tuple[int, int] | None = None
    include_harmony_windows: bool = True
    include_rhythm_profile: bool = True
    include_generation_suggestions: bool = False


def analyze_timeline(request: TimelineAnalysisRequest) -> dict[str, object]:
    """Return a stub analysis dictionary highlighting future work."""

    # TODO: convert events into quantized beats tied to tempo/meter.
    # TODO: derive harmonic context by reusing analyze_scale/analyze_chord.
    # TODO: compute rhythmic density, syncopation metrics, and motif stats.
    # TODO: when include_generation_suggestions is True, propose future events.

    return {
        "event_count": sum(1 for _ in request.events),
        "tempo_bpm": request.tempo_bpm,
        "meter": request.meter,
        "harmony_windows": "TODO: summarize chord/scale windows.",
        "rhythm_profile": "TODO: compute rhythmic density and accents.",
        "generation_suggestions": (
            "TODO: emit candidate continuations."
            if request.include_generation_suggestions
            else None
        ),
        "notes": [
            "Timeline analysis is currently a placeholder.",
            "Implement MIDI/MusicXML ingestion and context tracking.",
        ],
    }


def generate_sequence(seed_events: Iterable[TimedEvent], *, length: float) -> list[TimedEvent]:
    """Stub for future generative workflows."""

    # TODO: incorporate interval statistics, harmonic constraints, and rhythm templates.
    # TODO: allow probabilistic branching or rule-based cadences.

    del seed_events, length  # appease linters until implementation exists
    return []
