"""Workspace scaffolding for coordinating scale, chord, and timeline state.

This module provides a central object that can be shared across CLIs/GUI layers.
It keeps track of the currently selected scale, chord, and timeline events while
exposing helper methods that reuse the existing analyzers.  The implementation is
intentional scaffolding—each method documents TODOs so future features can land
without reshaping the rest of the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

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
    SESSION_SCALE_CONTEXT,
    SESSION_CHORD_CONTEXT,
)
from .core.scale import Scale
from .core.quality import ChordQuality
from .core.chord import Chord
from .io.loaders import load_scales, load_chord_qualities
from .context import DisplayContext
from .context.formatters import (
    update_context_with_scale,
    update_context_with_chord_root,
)


@dataclass
class Workspace:
    """Aggregate object describing the current musical context."""

    scale: Scale | None = None
    chord: Chord | None = None
    timeline_events: list[TimedEvent] = field(default_factory=list)
    context_scope: str = "abstract"
    context_tokens: tuple[str, ...] = field(default_factory=tuple)
    context_absolute_midi: tuple[int, ...] = field(default_factory=tuple)
    _listeners: list[Callable[[str, object | None], None]] = field(
        default_factory=list, init=False, repr=False, compare=False
    )
    display_context: DisplayContext = field(default_factory=DisplayContext, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.display_context.add_listener(self._on_display_context_change)

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
        self._apply_context(SESSION_SCALE_CONTEXT.get(self.scale.name))
        update_context_with_scale(
            self.display_context,
            tonic_pc=None,
            degrees=self.scale.degrees,
        )
        self._notify("scale", self.scale)
        return self.scale

    def register_scale(self, builder: ManualScaleBuilder) -> Scale:
        scales, _ = self.refresh_catalogs()
        result = register_scale(builder, catalog=scales)
        self.scale = result["scale"]
        self._apply_context(result.get("context"))
        update_context_with_scale(
            self.display_context,
            tonic_pc=None,
            degrees=self.scale.degrees,
        )
        self._notify("scale", self.scale)
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
        self._apply_context(SESSION_CHORD_CONTEXT.get(self.chord.quality.name))
        update_context_with_chord_root(self.display_context, root_pc)
        self._notify("chord", self.chord)
        return self.chord

    def register_chord(self, builder: ManualChordBuilder, *, root_pc: int = 0) -> Chord:
        _, chords = self.refresh_catalogs()
        result = register_chord(builder, catalog=chords)
        quality = result["quality"]
        self.chord = Chord.from_quality(root_pc, quality)
        self._apply_context(result.get("context"))
        update_context_with_chord_root(self.display_context, root_pc)
        self._notify("chord", self.chord)
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
        self._notify("timeline", list(self.timeline_events))

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
        self.context_scope = "abstract"
        self.context_tokens = tuple()
        self.context_absolute_midi = tuple()
        update_context_with_scale(self.display_context, None, [])
        update_context_with_chord_root(self.display_context, None)
        self._notify("scale", None)
        self._notify("chord", None)
        self._notify("timeline", [])
        self._notify("context", self._context_payload())

    # --- Session metadata -----------------------------------------------

    @staticmethod
    def session_scales() -> Mapping[str, Scale]:
        return SESSION_SCALES

    @staticmethod
    def session_chords() -> Mapping[str, ChordQuality]:
        return SESSION_CHORDS

    def _apply_context(self, context: dict[str, object] | None) -> None:
        if not context:
            self.context_scope = "abstract"
            self.context_tokens = tuple()
            self.context_absolute_midi = tuple()
        else:
            self.context_scope = context.get("scope", "abstract")
            self.context_tokens = tuple(context.get("tokens", []))
            absolute = tuple(int(v) for v in context.get("absolute_midi", []) or [])
            self.context_absolute_midi = absolute
        self._notify("context", self._context_payload())

    def add_listener(self, callback: Callable[[str, object | None], None]) -> None:
        """Register a listener for workspace change events."""

        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, object | None], None]) -> None:
        """Remove a previously registered listener."""

        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _notify(self, event: str, payload: object | None) -> None:
        if not self._listeners:
            return
        for listener in tuple(self._listeners):
            listener(event, payload)

    def _context_payload(self) -> dict[str, Any]:
        return {
            "scope": self.context_scope,
            "tokens": tuple(self.context_tokens),
            "absolute_midi": tuple(self.context_absolute_midi),
        }

    # --- Display context helpers --------------------------------------

    def display_setting(self, key: str, default: Any = None) -> Any:
        return self.display_context.get(key, default)

    def set_display_setting(self, key: str, value: Any, *, layer: str = "session") -> None:
        self.display_context.set(key, value, layer=layer)

    def _on_display_context_change(self, event: str, payload: object) -> None:
        self._notify("display_context", {"event": event, "payload": payload})

    # TODO: integrate persistence/export for session-defined objects.
    # TODO: surface change notifications for GUI/interactive layers.
    # TODO: bridge MIDI ingestion once events_from_midi_file is implemented.


__all__ = ["Workspace"]
