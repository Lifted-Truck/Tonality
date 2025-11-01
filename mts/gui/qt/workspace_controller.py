"""
Qt-friendly controller that wraps the shared Workspace object.

The controller exposes Qt signals whenever the underlying musical context
changes.  Views can connect to these signals to keep their state updated, and
other front-ends can reuse the same logic without depending on Qt by composing
the controller behind an abstract interface.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Mapping, Sequence

from ...workspace import Workspace
from ...analysis import (
    ScaleAnalysisRequest,
    ChordAnalysisRequest,
    TimelineAnalysisRequest,
    analyze_scale,
    analyze_chord,
    analyze_timeline,
    chord_brief,
    TimedEvent,
)
from ...analysis.builders import ManualScaleBuilder, ManualChordBuilder
from .presenters import build_scale_summary, build_chord_summary, ScaleSummary, ChordSummary

try:  # pragma: no cover - import guard
    from PySide6.QtCore import QObject, Signal, Slot  # type: ignore
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "WorkspaceController requires PySide6. Install the 'tonality[qt]' extra "
        "when the dependency group is defined."
    ) from exc


class WorkspaceController(QObject):
    """Adapter between the pure Workspace model and Qt widgets."""

    scale_changed = Signal(object)
    chord_changed = Signal(object)
    timeline_changed = Signal(object)
    context_changed = Signal(object)

    def __init__(self, workspace: Workspace | None = None) -> None:
        super().__init__()
        self._workspace = workspace or Workspace()
        self._workspace.add_listener(self._handle_workspace_event)
        self._suppress_events = False
        self._scale_tonic_pc: int | None = None

    # --- Scale operations -------------------------------------------------

    @Slot(str, int)
    def set_scale_by_name(self, name: str, tonic_pc: int | None = None) -> ScaleSummary | None:
        if tonic_pc is not None and tonic_pc < 0:
            tonic_pc = None
        self._scale_tonic_pc = tonic_pc
        with self._suppress_workspace_events():
            self._workspace.set_scale_by_name(name)
        summary = self._build_scale_summary()
        self.scale_changed.emit(summary)
        self._emit_context()
        return summary

    def register_scale(self, builder: ManualScaleBuilder, *, tonic_pc: int | None = None) -> ScaleSummary | None:
        if tonic_pc is not None and tonic_pc < 0:
            tonic_pc = None
        self._scale_tonic_pc = tonic_pc
        with self._suppress_workspace_events():
            self._workspace.register_scale(builder)
        summary = self._build_scale_summary()
        self.scale_changed.emit(summary)
        self._emit_context()
        return summary

    def analyze_scale(self, **kwargs: Any) -> ScaleSummary:
        if not self._workspace.scale:
            raise ValueError("No scale selected.")
        request = ScaleAnalysisRequest(
            scale=self._workspace.scale,
            tonic_pc=self._scale_tonic_pc,
            **kwargs,
        )
        analysis = analyze_scale(request)
        summary = build_scale_summary(self._workspace, analysis)
        self.scale_changed.emit(summary)
        return summary

    def match_scale(self, degrees: Iterable[int]) -> Sequence[str]:
        matches = self._workspace.match_scale(degrees)
        return [scale.name for scale in matches]

    # --- Chord operations -------------------------------------------------

    @Slot(int, str)
    def set_chord(self, root_pc: int, quality_name: str) -> ChordSummary | None:
        with self._suppress_workspace_events():
            self._workspace.set_chord(root_pc, quality_name)
        summary = self._build_chord_summary()
        self.chord_changed.emit(summary)
        self._emit_context()
        return summary

    def register_chord(self, builder: ManualChordBuilder, *, root_pc: int = 0) -> ChordSummary | None:
        with self._suppress_workspace_events():
            self._workspace.register_chord(builder, root_pc=root_pc)
        summary = self._build_chord_summary()
        self.chord_changed.emit(summary)
        self._emit_context()
        return summary

    def analyze_chord(self, **kwargs: Any) -> ChordSummary:
        if not self._workspace.chord:
            raise ValueError("No chord selected.")
        request = ChordAnalysisRequest(chord=self._workspace.chord, **kwargs)
        analysis = analyze_chord(request)
        summary = build_chord_summary(self._workspace, analysis)
        self.chord_changed.emit(summary)
        return summary

    def match_chord(self, intervals: Iterable[int]) -> Sequence[str]:
        matches = self._workspace.match_chord(intervals)
        return [quality.name for quality in matches]

    # --- Timeline operations ----------------------------------------------

    def set_timeline(self, events: Iterable[TimedEvent]) -> list[TimedEvent]:
        with self._suppress_workspace_events():
            self._workspace.set_timeline(events)
        events_list = list(self._workspace.timeline_events)
        self.timeline_changed.emit(events_list)
        return events_list

    def analyze_timeline(self, **kwargs: Any) -> Mapping[str, Any]:
        if not self._workspace.timeline_events:
            raise ValueError("No timeline events registered.")
        request = TimelineAnalysisRequest(events=self._workspace.timeline_events, **kwargs)
        analysis = analyze_timeline(request)
        self.timeline_changed.emit(self._workspace.timeline_events)
        return analysis

    # --- Workspace metadata -----------------------------------------------

    def clear(self) -> None:
        with self._suppress_workspace_events():
            self._workspace.clear()
        self.scale_changed.emit(None)
        self.chord_changed.emit(None)
        self.timeline_changed.emit([])
        self._emit_context()

    def session_scales(self) -> Mapping[str, Any]:
        return self._workspace.session_scales()

    def session_chords(self) -> Mapping[str, Any]:
        return self._workspace.session_chords()

    def workspace(self) -> Workspace:
        """Expose the underlying Workspace for advanced consumers."""

        return self._workspace

    def available_scales(self) -> list[str]:
        scales, _ = self._workspace.refresh_catalogs()
        return sorted(scales.keys())

    def available_chord_qualities(self) -> list[str]:
        _, chords = self._workspace.refresh_catalogs()
        return sorted(chords.keys())

    def dispose(self) -> None:
        self._workspace.remove_listener(self._handle_workspace_event)

    # --- Internal helpers -------------------------------------------------

    def _emit_context(self) -> None:
        payload = {
            "scope": self._workspace.context_scope,
            "tokens": list(self._workspace.context_tokens),
            "absolute_midi": list(self._workspace.context_absolute_midi),
        }
        self.context_changed.emit(payload)

    def _build_scale_summary(self) -> ScaleSummary | None:
        if not self._workspace.scale:
            return None
        request = ScaleAnalysisRequest(
            scale=self._workspace.scale,
            tonic_pc=self._scale_tonic_pc,
        )
        analysis = analyze_scale(request)
        return build_scale_summary(self._workspace, analysis)

    def _build_chord_summary(self) -> ChordSummary | None:
        if not self._workspace.chord:
            return None
        chord = self._workspace.chord
        request = ChordAnalysisRequest(chord=chord, include_voicings=True, include_inversions=True)
        analysis = analyze_chord(request)
        analysis["brief"] = chord_brief(chord.quality)
        return build_chord_summary(self._workspace, analysis)

    def _handle_workspace_event(self, event: str, payload: object | None) -> None:
        if self._suppress_events:
            return
        if event == "scale":
            self.scale_changed.emit(self._build_scale_summary())
        elif event == "chord":
            self.chord_changed.emit(self._build_chord_summary())
        elif event == "timeline":
            self.timeline_changed.emit(list(self._workspace.timeline_events))
        elif event == "context":
            self.context_changed.emit(payload)

    @contextmanager
    def _suppress_workspace_events(self):
        previous = self._suppress_events
        self._suppress_events = True
        try:
            yield
        finally:
            self._suppress_events = previous


__all__ = ["WorkspaceController"]
