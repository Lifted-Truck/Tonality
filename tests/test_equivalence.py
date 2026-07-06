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


def test_cached_index_covers_all_masks_identically_to_inline_build():
    # RE-5c: the default path uses a cached mask index; a caller-supplied
    # catalog builds inline. Both must yield identical interpretations for
    # every pc-set — pin it across the whole 4096-mask space.
    from mts.core.bitmask import pcs_from_mask
    from mts.io.loaders import load_chord_qualities

    catalog = load_chord_qualities()  # same content, forces the inline path
    for mask in range(1, 4096):
        pcs = pcs_from_mask(mask)
        cached = interpret_chord(pcs).interpretations
        inline = interpret_chord(pcs, catalog=catalog).interpretations
        assert [(i.root_pc, i.quality, tuple(i.aliases)) for i in cached] == [
            (i.root_pc, i.quality, tuple(i.aliases)) for i in inline
        ]


def test_session_registered_chord_appears_via_cached_index():
    from mts.analysis.builders import ManualChordBuilder, register_chord
    from mts.io.loaders import _DEFAULT_SESSION

    try:
        register_chord(ManualChordBuilder(name="Re5cProbe", intervals=[0, 1, 2]))
        names = {i.quality for i in interpret_chord([0, 1, 2]).interpretations}
        assert "Re5cProbe" in names  # session fingerprint invalidated the cache
    finally:
        _DEFAULT_SESSION.chords.clear()
        _DEFAULT_SESSION.chord_specs.clear()
        _DEFAULT_SESSION.chord_context.clear()
    assert "Re5cProbe" not in {
        i.quality for i in interpret_chord([0, 1, 2]).interpretations
    }
