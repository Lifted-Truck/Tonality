"""Smoke coverage for the demoted/deferred consumers of chord analysis.

`mts/cli/push.py` and the Qt GUI layer (`mts/gui/qt/*`) are demoted layers per
ROADMAP.md, but they must stay correct against the typed `ChordAnalysisResult`
API. These tests guard against regression to the old dict-style access that broke
when `analyze_chord` started returning a frozen dataclass.
"""

from __future__ import annotations

import pytest

from mts.analysis import (
    ChordAnalysisRequest,
    ScaleAnalysisRequest,
    analyze_chord,
    analyze_scale,
    chord_brief,
)
from mts.analysis.voicings import suggest_voicings
from mts.io.loaders import load_chord_qualities
from mts.workspace import Workspace


def test_push_session_chord_summary_runs():
    """`_session_chord_summary` reads the typed result + generative voicings."""
    from mts.cli.push import _session_chord_summary

    quality = load_chord_qualities()["maj7"]
    summary = _session_chord_summary(quality)

    assert "inversions" in summary
    assert "voicings ->" in summary
    # maj7 is a seventh chord: 4 inversions, and closed is always a valid voicing.
    assert summary.startswith("4 inversions")
    assert "closed" in summary


def test_presenter_build_chord_summary_from_typed_result():
    """`build_chord_summary` consumes a `ChordAnalysisResult` via attributes."""
    from mts.gui.qt.presenters import build_chord_summary

    workspace = Workspace()
    workspace.set_chord(0, "maj7")
    chord = workspace.chord

    result = analyze_chord(
        ChordAnalysisRequest(chord=chord, include_inversions=True)
    )
    summary = build_chord_summary(
        workspace,
        result,
        brief=chord_brief(chord.quality),
        voicings=suggest_voicings(chord),
    )

    assert summary.name == "C:maj7"
    assert list(summary.pcs) == [0, 4, 7, 11]
    assert list(summary.intervals) == [0, 4, 7, 11]
    assert "closed" in summary.voicings
    assert len(summary.inversions) == 4
    assert summary.brief is not None


def test_presenter_build_scale_summary_from_typed_result():
    """`build_scale_summary` consumes a `ScaleAnalysisResult` via attributes."""
    from mts.gui.qt.presenters import build_scale_summary

    workspace = Workspace()
    workspace.set_scale_by_name("Ionian")

    result = analyze_scale(ScaleAnalysisRequest(scale=workspace.scale))
    summary = build_scale_summary(workspace, result)

    assert summary.name == "Ionian"
    assert summary.cardinality == 7
    assert list(summary.degrees) == [0, 2, 4, 5, 7, 9, 11]


def test_workspace_controller_chord_summary_threads_brief_and_voicings():
    """The Qt controller builds a full chord summary without dict mutation."""
    pytest.importorskip("PySide6")
    from mts.gui.qt.workspace_controller import WorkspaceController

    controller = WorkspaceController()
    summary = controller.set_chord(2, "min7")  # D min7

    assert summary is not None
    assert summary.name == "D:min7"
    assert len(summary.inversions) == 4
    assert summary.brief is not None
    assert "closed" in summary.voicings

    reanalyzed = controller.analyze_chord(include_inversions=True)
    assert reanalyzed.name == "D:min7"
    assert reanalyzed.brief is not None
    assert reanalyzed.voicings
