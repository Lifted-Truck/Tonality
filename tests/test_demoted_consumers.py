"""Smoke coverage for the demoted consumer of chord analysis.

`mts/cli/push.py` (the legacy terminal Push grid) is a demoted layer per ROADMAP.md,
but it must stay correct against the typed `ChordAnalysisResult` API. This guards
against regression to the old dict-style access that broke when `analyze_chord`
started returning a frozen dataclass. (The Qt GUI layer was removed 2026-06-29.)
"""

from __future__ import annotations

from mts.io.loaders import load_chord_qualities


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
