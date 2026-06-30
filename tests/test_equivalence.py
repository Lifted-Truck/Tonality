"""Tests for structural / enharmonic equivalence (interpret_chord)."""

import pytest

from mts.analysis import interpret_chord


def _pairs(pcs):
    return {(i.root_pc, i.quality) for i in interpret_chord(pcs).interpretations}


def test_symmetric_dim7_names_at_four_roots():
    result = interpret_chord([0, 3, 6, 9])
    assert result.rotational_period == 3
    assert {(i.root_pc, i.quality) for i in result.interpretations} == {
        (0, "dim7"), (3, "dim7"), (6, "dim7"), (9, "dim7"),
    }


def test_symmetric_augmented_names_at_three_roots():
    result = interpret_chord([0, 4, 8])
    assert result.rotational_period == 4
    assert {(i.root_pc, i.quality) for i in result.interpretations} == {
        (0, "aug"), (4, "aug"), (8, "aug"),
    }


def test_ambiguous_set_c6_equals_am7():
    pairs = _pairs([0, 4, 7, 9])
    assert (0, "maj6") in pairs   # C6
    assert (9, "min7") in pairs   # Am7


def test_german_sixth_surfaces_as_dominant():
    # {0,3,6,8} is the A-flat dominant-7th pitch-class set (= German 6th in C).
    pairs = _pairs([0, 3, 6, 8])
    assert (8, "7") in pairs  # root G#/Ab as a dominant 7th


def test_plain_triad_has_single_interpretation():
    result = interpret_chord([0, 4, 7])
    assert result.rotational_period == 12
    assert [(i.root_pc, i.quality) for i in result.interpretations] == [(0, "maj")]


def test_interpretation_is_numeric_with_aliases():
    # interpret_chord is identity-level: numeric root_pc + canonical quality +
    # aliases. Spelling the root is a display-edge concern (name_interpretation).
    interp = interpret_chord([0, 4, 7]).interpretations[0]
    assert interp.root_pc == 0
    assert interp.quality == "maj"
    assert "major" in interp.aliases


def test_octave_and_duplicate_pcs_are_normalized():
    # raw MIDI-ish input with doublings reduces to the identity set
    assert _pairs([0, 12, 4, 7, 7]) == _pairs([0, 4, 7])


def test_empty_input_raises():
    with pytest.raises(ValueError):
        interpret_chord([])
