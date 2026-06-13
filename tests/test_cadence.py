"""Cadence detection (gap 7): cadential formulas as evidenced events."""

from __future__ import annotations

import json

import pytest

from mts.analysis import detect_cadences


def _types(result):
    return [(c.type, c.arrival_index) for c in result.cadences]


# --- the four formulas (key of C major: tonic 0) ------------------------------------------


def test_authentic_cadence_v_to_i():
    # ii - V - I in C major: D min, G maj, C maj
    result = detect_cadences([(2, "min"), (7, "maj"), (0, "maj")], tonic_pc=0, mode="major")
    assert result.mode_supported is True
    authentic = [c for c in result.cadences if c.type == "authentic"]
    assert len(authentic) == 1
    cad = authentic[0]
    assert (cad.approach.roman, cad.arrival.roman) == ("V", "I")
    assert cad.arrival_index == 2 and cad.is_final is True
    assert cad.root_motion == 5  # G->C ascending fourth
    assert any("dominant" in e and "tonic" in e for e in cad.evidence)


def test_authentic_with_dominant_seventh():
    result = detect_cadences([(7, "7"), (0, "maj")], tonic_pc=0, mode="major")
    assert _types(result) == [("authentic", 1)]
    assert result.cadences[0].approach.roman == "V7"


def test_plagal_cadence_iv_to_i():
    result = detect_cadences([(0, "maj"), (5, "maj"), (0, "maj")], tonic_pc=0, mode="major")
    plagal = [c for c in result.cadences if c.type == "plagal"]
    assert len(plagal) == 1
    assert (plagal[0].approach.roman, plagal[0].arrival.roman) == ("IV", "I")


def test_deceptive_cadence_v_to_vi():
    result = detect_cadences([(7, "maj"), (9, "min")], tonic_pc=0, mode="major")
    assert _types(result) == [("deceptive", 1)]
    cad = result.cadences[0]
    assert (cad.approach.roman, cad.arrival.roman) == ("V", "vi")


def test_half_cadence_only_at_final_dominant():
    # ii - V ending on the dominant -> a half cadence
    half = detect_cadences([(2, "min"), (7, "maj")], tonic_pc=0, mode="major")
    assert _types(half) == [("half", 1)]
    # but a mid-progression V (V - I) is NOT a half cadence — it's authentic
    mid = detect_cadences([(7, "maj"), (0, "maj")], tonic_pc=0, mode="major")
    assert [c.type for c in mid.cadences] == ["authentic"]


# --- functional annotation + honesty ------------------------------------------------------


def test_every_chord_is_annotated_with_role_and_degree():
    result = detect_cadences([(0, "maj"), (7, "7")], tonic_pc=0, mode="major")
    assert [c.relative_root for c in result.chords] == [0, 7]
    assert [c.role for c in result.chords] == ["tonic", "dominant"]


def test_transposition_invariance():
    # the same ii-V-I in E major (tonic 4) finds the same cadence
    result = detect_cadences([(6, "min"), (11, "maj"), (4, "maj")], tonic_pc=4, mode="major")
    assert _types(result) == [("authentic", 2)]
    assert result.cadences[0].arrival.relative_root == 0


def test_minor_key_dominant_seventh():
    # V7 - i in A minor (tonic 9): E7 (rel root 7) -> A minor
    result = detect_cadences([(4, "7"), (9, "min")], tonic_pc=9, mode="minor")
    assert _types(result) == [("authentic", 1)]
    assert result.cadences[0].approach.roman == "V7"


def test_minor_bare_major_v_triad_inherits_vocabulary_gap():
    # The minor function templates list V7 but not the bare major V triad, so
    # cadence detection (a faithful consumer of that vocabulary) does not
    # recognize a bare E-major -> A-minor as authentic. Pinned as the honest
    # inherited behavior — not a cadence bug.
    result = detect_cadences([(4, "maj"), (9, "min")], tonic_pc=9, mode="minor")
    assert result.cadences == []
    assert result.chords[0].role is None  # the bare major V triad has no role here


def test_non_functional_chords_yield_no_cadence():
    # a chromatic shuffle with no functional resolution
    result = detect_cadences([(1, "maj"), (6, "maj")], tonic_pc=0, mode="major")
    assert result.cadences == []


def test_modal_key_is_not_supported_no_guessing():
    result = detect_cadences([(7, "maj"), (0, "maj")], tonic_pc=0, mode="dorian")
    assert result.mode_supported is False
    assert result.cadences == []
    assert all(c.role is None for c in result.chords)


def test_validation():
    with pytest.raises(ValueError, match="at least one chord"):
        detect_cadences([], tonic_pc=0, mode="major")
    with pytest.raises(ValueError, match="tonic_pc out of range"):
        detect_cadences([(0, "maj")], tonic_pc=12, mode="major")


def test_to_dict_is_json_ready():
    payload = json.loads(json.dumps(
        detect_cadences([(7, "maj"), (0, "maj")], tonic_pc=0, mode="major").to_dict()
    ))
    assert payload["cadences"][0]["type"] == "authentic"
    assert payload["cadences"][0]["evidence"]
    assert payload["chords"][0]["roman"] == "V"
