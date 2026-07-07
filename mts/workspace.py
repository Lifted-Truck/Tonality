"""Stateful session facade over the analysis engine.

A ``Workspace`` holds the currently selected scale/chord plus a
``DisplayContext``, and exposes helpers that reuse the typed analyzers. It is
*a* entry point (for the CLI and interactive use), not *the* API — the pure
analysis functions are. Each ``Workspace`` owns its own ``SessionCatalog`` so
multiple workspaces coexist with independent user-registered scales/chords.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .analysis import (
    ScaleAnalysisRequest,
    ChordAnalysisRequest,
    analyze_scale,
    analyze_chord,
)
from .analysis.results import ScaleAnalysisResult, ChordAnalysisResult
from .analysis.builders import (
    ManualScaleBuilder,
    ManualChordBuilder,
    SessionCatalog,
    register_scale,
    register_chord,
    match_scale,
    match_chord,
    SESSION_FILE,
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
    context_scope: str = "abstract"
    context_tokens: tuple[str, ...] = field(default_factory=tuple)
    context_absolute_midi: tuple[int, ...] = field(default_factory=tuple)
    _session: SessionCatalog = field(
        default_factory=SessionCatalog.empty, init=False, repr=False, compare=False
    )
    display_context: DisplayContext = field(default_factory=DisplayContext, init=False, repr=False, compare=False)

    def refresh_catalogs(self) -> tuple[Mapping[str, Scale], Mapping[str, ChordQuality]]:
        """Return the latest scale/chord catalogs (including this workspace's session entries)."""
        scales = load_scales(session=self._session)
        chords = load_chord_qualities(session=self._session)
        return scales, chords

    # --- Scale utilities -------------------------------------------------

    def set_scale_by_name(self, name: str) -> Scale:
        scales, _ = self.refresh_catalogs()
        if name not in scales:
            raise ValueError(f"Unknown scale {name!r}.")
        self.scale = scales[name]
        self._apply_context(self._session.scale_context.get(self.scale.name))
        update_context_with_scale(
            self.display_context,
            tonic_pc=None,
            degrees=self.scale.degrees,
        )
        return self.scale

    def register_scale(self, builder: ManualScaleBuilder) -> Scale:
        scales, _ = self.refresh_catalogs()
        result = register_scale(builder, catalog=scales, session=self._session)
        self.scale = result["scale"]
        self._apply_context(result.get("context"))
        update_context_with_scale(
            self.display_context,
            tonic_pc=None,
            degrees=self.scale.degrees,
        )
        return self.scale

    def analyze_scale(self, **kwargs) -> ScaleAnalysisResult:
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
        self._apply_context(self._session.chord_context.get(self.chord.quality.name))
        update_context_with_chord_root(self.display_context, root_pc)
        return self.chord

    def register_chord(self, builder: ManualChordBuilder, *, root_pc: int = 0) -> Chord:
        _, chords = self.refresh_catalogs()
        result = register_chord(builder, catalog=chords, session=self._session)
        quality = result["quality"]
        self.chord = Chord.from_quality(root_pc, quality)
        self._apply_context(result.get("context"))
        update_context_with_chord_root(self.display_context, root_pc)
        return self.chord

    def analyze_chord(self, **kwargs) -> ChordAnalysisResult:
        if not self.chord:
            raise ValueError("No chord is currently selected.")
        request = ChordAnalysisRequest(chord=self.chord, **kwargs)
        return analyze_chord(request)

    def match_chord(self, intervals: Iterable[int]) -> list[ChordQuality]:
        _, chords = self.refresh_catalogs()
        return match_chord(intervals, chords)

    def clear(self) -> None:
        """Clear the workspace selections (scale/chord)."""
        self.scale = None
        self.chord = None
        self.context_scope = "abstract"
        self.context_tokens = tuple()
        self.context_absolute_midi = tuple()
        update_context_with_scale(self.display_context, None, [])
        update_context_with_chord_root(self.display_context, None)

    # --- Session management ----------------------------------------------

    def session_scales(self) -> Mapping[str, Scale]:
        """Return the scales registered in this workspace's session."""
        return self._session.scales

    def session_chords(self) -> Mapping[str, ChordQuality]:
        """Return the chord qualities registered in this workspace's session."""
        return self._session.chords

    def load_session(self, path: Path | None = None) -> None:
        """Load session-defined scales/chords from disk into this workspace."""
        self._session.load(path or SESSION_FILE)

    def save_session(self, path: Path | None = None) -> None:
        """Persist this workspace's session to disk."""
        self._session.save(path or SESSION_FILE)

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

    # --- Display context helpers ------------------------------------------

    def display_setting(self, key: str, default: Any = None) -> Any:
        return self.display_context.get(key, default)

    def set_display_setting(self, key: str, value: Any, *, layer: str = "session") -> None:
        self.display_context.set(key, value, layer=layer)


__all__ = ["Workspace"]
