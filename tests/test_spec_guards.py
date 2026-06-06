"""Tests for spec-level guards: error, don't guess (the cardinal rule)."""

import pytest

from mts.analysis import (
    ChordAnalysisRequest,
    Realization,
    SpecificationError,
    analyze_chord,
    analyze_voicing,
    require_realization,
    suggest_voicings,
)
from mts.analysis.specs import parse_chord_spec
from mts.core.chord import Chord
from mts.io.loaders import load_chord_qualities


def _maj7_chord() -> Chord:
    quality = load_chord_qualities()["maj7"]
    return Chord.from_quality(0, quality)


def test_analyze_chord_is_pure_identity():
    # No register in, no register (no voicings) out.
    result = analyze_chord(ChordAnalysisRequest(chord=_maj7_chord()))
    assert not hasattr(result, "voicings")
    assert "voicings" not in result.to_dict()


def test_analyze_voicing_errors_without_register():
    # A register-less identity asking for register-dependent analysis.
    with pytest.raises(SpecificationError):
        analyze_voicing(None)


def test_require_realization_guard():
    with pytest.raises(SpecificationError):
        require_realization(None, analysis="anything")
    real = Realization.from_midi([48, 52, 55])
    assert require_realization(real, analysis="anything") is real


def test_analyze_voicing_reads_real_register():
    real = parse_chord_spec("[C3,E3,G3,C4]").to_realization()
    assert real is not None
    analysis = analyze_voicing(real)
    assert analysis.rooted is True
    assert analysis.bass_midi == 48
    assert analysis.intervals_from_bass == [0, 4, 7, 12]  # register-aware, not mod-12
    assert analysis.spread_semitones == 12
    assert analysis.doublings == [0]
    assert analysis.note_names == ["C3", "E3", "G3", "C4"]


def test_analyze_voicing_accepts_rootless_template():
    template = Realization.from_midi([48, 52, 55])  # no root_pc
    analysis = analyze_voicing(template)
    assert analysis.rooted is False
    assert analysis.spec_level == "voicing template"


def test_suggest_voicings_is_generative_and_available():
    # The generative escape hatch still exists, clearly separated from analysis.
    voicings = suggest_voicings(_maj7_chord())
    assert voicings.get("closed").label == "closed"
