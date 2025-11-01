"""
Shared presenter dataclasses for the Qt GUI layer.

The goal is to transform analyzer dictionaries into structured objects that can
drive both Qt widgets and (eventually) other front-ends like a web client.  All
logic here should remain GUI-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ...core.enharmonics import name_for_pc
from ...workspace import Workspace


@dataclass(frozen=True)
class WorkspaceContext:
    """Lightweight snapshot of the current workspace context metadata."""

    scope: str
    tokens: tuple[str, ...]
    absolute_midi: tuple[int, ...]


@dataclass(frozen=True)
class ScaleSummary:
    """Structured view of the current scale and its analysis."""

    name: str
    tonic_pc: int | None
    degrees: Sequence[int]
    cardinality: int
    step_pattern: Sequence[int]
    interval_vector: Sequence[int]
    modes: Sequence[Mapping[str, Any]] | None
    symmetry: Mapping[str, Any] | None
    note_names: Sequence[str] | None
    context: WorkspaceContext


@dataclass(frozen=True)
class ChordSummary:
    """Structured view of the current chord and its analysis."""

    name: str
    root_pc: int | None
    pcs: Sequence[int]
    intervals: Sequence[int]
    voicings: Mapping[str, Any]
    inversions: Sequence[Mapping[str, Any]]
    brief: Any | None
    context: WorkspaceContext


def _context_from_workspace(workspace: Workspace) -> WorkspaceContext:
    return WorkspaceContext(
        scope=workspace.context_scope,
        tokens=tuple(workspace.context_tokens),
        absolute_midi=tuple(workspace.context_absolute_midi),
    )


def build_scale_summary(workspace: Workspace, analysis: Mapping[str, Any]) -> ScaleSummary:
    """Convert an analyzer dictionary into a `ScaleSummary`."""

    return ScaleSummary(
        name=str(analysis.get("scale_name", workspace.scale.name if workspace.scale else "")),
        tonic_pc=analysis.get("tonic_pc"),
        degrees=list(analysis.get("degrees", [])),
        cardinality=int(analysis.get("cardinality", 0)),
        step_pattern=list(analysis.get("step_pattern", [])),
        interval_vector=list(analysis.get("interval_vector", [])),
        modes=analysis.get("modes"),
        symmetry=analysis.get("symmetry"),
        note_names=analysis.get("note_names"),
        context=_context_from_workspace(workspace),
    )


def build_chord_summary(workspace: Workspace, analysis: Mapping[str, Any]) -> ChordSummary:
    """Convert an analyzer dictionary into a `ChordSummary`."""

    chord = workspace.chord
    name = _chord_display_name(chord, analysis)
    intervals = list(
        analysis.get("intervals_relative_to_root")
        or analysis.get("intervals")
        or []
    )
    return ChordSummary(
        name=name,
        root_pc=chord.root_pc if chord else None,
        pcs=list(analysis.get("pcs", [])),
        intervals=intervals,
        voicings=analysis.get("voicings", {}),
        inversions=list(analysis.get("inversions", [])),
        brief=analysis.get("brief"),
        context=_context_from_workspace(workspace),
    )


def _chord_display_name(chord, analysis: Mapping[str, Any]) -> str:
    label = str(analysis.get("chord_name") or "").strip()
    if label:
        return label
    if chord:
        root = name_for_pc(chord.root_pc)
        return f"{root}:{chord.quality.name}"
    return ""


__all__ = [
    "WorkspaceContext",
    "ScaleSummary",
    "ChordSummary",
    "build_scale_summary",
    "build_chord_summary",
]
