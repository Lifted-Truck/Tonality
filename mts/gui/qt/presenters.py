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
from ...analysis.results import (
    ChordAnalysisResult,
    ScaleAnalysisResult,
    VoicingSet,
)
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


def build_scale_summary(workspace: Workspace, analysis: ScaleAnalysisResult) -> ScaleSummary:
    """Convert a typed `ScaleAnalysisResult` into a `ScaleSummary`."""

    name = analysis.scale_name or (workspace.scale.name if workspace.scale else "")
    return ScaleSummary(
        name=str(name),
        tonic_pc=analysis.tonic_pc,
        degrees=list(analysis.degrees),
        cardinality=int(analysis.cardinality),
        step_pattern=list(analysis.step_pattern),
        interval_vector=list(analysis.interval_vector),
        modes=analysis.modes,
        symmetry=analysis.symmetry,
        note_names=analysis.note_names,
        context=_context_from_workspace(workspace),
    )


def build_chord_summary(
    workspace: Workspace,
    analysis: ChordAnalysisResult,
    *,
    brief: Any | None = None,
    voicings: VoicingSet | None = None,
) -> ChordSummary:
    """Convert a typed `ChordAnalysisResult` into a `ChordSummary`.

    ``analyze_chord`` is pure-identity, so ``brief`` and ``voicings`` are not part
    of its output; callers thread them in explicitly. Voicings are generative —
    pass the result of ``suggest_voicings`` — and ``brief`` comes from
    ``chord_brief``.
    """

    chord = workspace.chord
    name = _chord_display_name(chord)
    voicing_map: Mapping[str, Any] = (
        {entry.label: entry for entry in voicings.entries} if voicings else {}
    )
    return ChordSummary(
        name=name,
        root_pc=chord.root_pc if chord else None,
        pcs=list(analysis.pcs),
        intervals=list(analysis.intervals_relative_to_root),
        voicings=voicing_map,
        inversions=list(analysis.inversions or []),
        brief=brief,
        context=_context_from_workspace(workspace),
    )


def _chord_display_name(chord) -> str:
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
