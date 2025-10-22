"""Workspace scaffolding for coordinating scale, chord, and timeline state.

This module provides a central object that can be shared across CLIs/GUI layers.
It keeps track of the currently selected scale, chord, and timeline events while
exposing helper methods that reuse the existing analyzers.  The implementation is
intentional scaffolding—each method documents TODOs so future features can land
without reshaping the rest of the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .analysis import (
    ScaleAnalysisRequest,
    ChordAnalysisRequest,
    TimelineAnalysisRequest,
    analyze_scale,
    analyze_chord,
    analyze_timeline,
    TimedEvent,
)
from .analysis.builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    register_scale,
    register_chord,
    match_scale,
    match_chord,
    SESSION_SCALES,
    SESSION_CHORDS,
)
from .core.scale import Scale
from .core.quality import ChordQuality
from .core.chord import Chord
from .io.loaders import load_scales, load_chord_qualities


@dataclass
class Workspace:
    """Aggregate object describing the current musical context."""

    scale: Scale | None = None
    chord: Chord | None = None
    timeline_events: list[TimedEvent] = field(default_factory=list)

    def refresh_catalogs(self) -> tuple[Mapping[str, Scale], Mapping[str, ChordQuality]]:
        """Return the latest scale/chord catalogs (including session entries)."""

        scales = load_scales()
        chords = load_chord_qualities()
        return scales, chords

    # --- Scale utilities -------------------------------------------------

    def set_scale_by_name(self, name: str) -> Scale:
        scales, _ = self.refresh_catalogs()
        if name not in scales:
            raise ValueError(f"Unknown scale {name!r}.")
        self.scale = scales[name]
        return self.scale

    def register_scale(self, builder: ManualScaleBuilder) -> Scale:
        scales, _ = self.refresh_catalogs()
        result = register_scale(builder, catalog=scales)
        self.scale = result["scale"]
        return self.scale

    def analyze_scale(self, **kwargs) -> dict[str, object]:
        if not self.scale:
            raise ValueError("No scale is currently selected.")
        request = ScaleAnalysisRequest(scale=self.scale, **kwargs)
        return analyze_scale(request)

    def match_scale(self, degrees: Iterable[int]) -> list[Scale]:
        scales, _ = self.refresh_catalogs()
        return match_scale(degrees, scales)

    # --- Chord utilities -------------------------------------------------

    def set_chord(self, root_pc: int, quality_name: str) -> Chord:
        _, chords = self.refresh_catalogs()
        if quality_name not in chords:
            raise ValueError(f"Unknown chord quality {quality_name!r}.")
        self.chord = Chord.from_quality(root_pc, chords[quality_name])
        return self.chord

    def register_chord(self, builder: ManualChordBuilder, *, root_pc: int = 0) -> Chord:
        _, chords = self.refresh_catalogs()
        result = register_chord(builder, catalog=chords)
        quality = result["quality"]
        self.chord = Chord.from_quality(root_pc, quality)
        return self.chord

    def analyze_chord(self, **kwargs) -> dict[str, object]:
        if not self.chord:
            raise ValueError("No chord is currently selected.")
        request = ChordAnalysisRequest(chord=self.chord, **kwargs)
        return analyze_chord(request)

    def match_chord(self, intervals: Iterable[int]) -> list[ChordQuality]:
        _, chords = self.refresh_catalogs()
        return match_chord(intervals, chords)

    # --- Timeline utilities ----------------------------------------------

    def set_timeline(self, events: Iterable[TimedEvent]) -> None:
        self.timeline_events = list(events)

    def analyze_timeline(self, **kwargs) -> dict[str, object]:
        if not self.timeline_events:
            raise ValueError("No timeline events registered.")
        request = TimelineAnalysisRequest(events=self.timeline_events, **kwargs)
        return analyze_timeline(request)

    def clear(self) -> None:
        """Clear the workspace selections (scale/chord/timeline)."""

        self.scale = None
        self.chord = None
        self.timeline_events.clear()

    # --- Session metadata -----------------------------------------------

    @staticmethod
    def session_scales() -> Mapping[str, Scale]:
        return SESSION_SCALES

    @staticmethod
    def session_chords() -> Mapping[str, ChordQuality]:
        return SESSION_CHORDS

    # TODO: integrate persistence/export for session-defined objects.
    # TODO: surface change notifications for GUI/interactive layers.
    # TODO: bridge MIDI ingestion once events_from_midi_file is implemented.


__all__ = ["Workspace"]
