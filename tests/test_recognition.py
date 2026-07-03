"""Tests for inversion naming (A3) and voicing recognition (A2)."""

from mts.analysis import ChordAnalysisRequest, analyze_chord, analyze_voicing
from mts.analysis.voicings import voicing_shapes
from mts.core.chord import Chord
from mts.core.realization import Realization
from mts.io.loaders import load_chord_qualities


def _inversions(name):
    chord = Chord.from_quality(0, load_chord_qualities()[name])
    return analyze_chord(ChordAnalysisRequest(chord=chord)).inversions


# --- A3: figured bass / inversion naming -----------------------------------

def test_triad_figured_bass():
    invs = _inversions("maj")
    assert [i.figured_bass for i in invs] == ["5/3", "6", "6/4"]
    assert [i.position_name for i in invs] == [
        "root position", "first inversion", "second inversion",
    ]


def test_seventh_chord_figured_bass():
    invs = _inversions("maj7")
    assert [i.figured_bass for i in invs] == ["7", "6/5", "4/3", "4/2"]
    assert [i.position_index for i in invs] == [0, 1, 2, 3]


def test_non_tertian_cardinality_has_position_but_no_figure():
    invs = _inversions("maj9")  # five notes
    assert all(i.figured_bass is None for i in invs)
    assert invs[0].position_name == "root position"
    assert invs[4].position_name == "fourth inversion"


# --- A2: voicing recognition -----------------------------------------------

def test_recognizes_root_position_closed():
    a = analyze_voicing(Realization.from_midi([48, 52, 55, 59], root_pc=0))  # C maj7
    assert a.voicing_type == "closed"
    assert a.openness == "closed"
    assert a.inversion_index == 0
    assert a.figured_bass == "7"


def test_recognizes_drop2_shape_and_reports_actual_bass():
    # drop-2 of C maj7: G in the bass -> recognized shape 'drop2', open spread,
    # and the literal bass position (G = 5th = second inversion).
    a = analyze_voicing(Realization.from_midi([43, 48, 52, 59], root_pc=0))
    assert a.voicing_type == "drop2"
    assert a.openness == "open"
    assert a.position_name == "second inversion"


def test_inverted_close_triad_names_inversion_but_not_a_vocabulary_type():
    a = analyze_voicing(Realization.from_midi([52, 55, 60], root_pc=0))  # E-G-C
    assert a.position_name == "first inversion"
    assert a.figured_bass == "6"
    assert a.voicing_type is None  # close inversions aren't in the generated vocabulary


def test_rootless_template_reports_openness_only():
    a = analyze_voicing(Realization.from_midi([52, 55, 59]))  # no root_pc
    assert a.rooted is False
    assert a.inversion_index is None
    assert a.voicing_type is None
    assert a.openness in {"closed", "open"}


def test_voicing_shapes_is_the_shared_vocabulary():
    shapes = voicing_shapes([0, 4, 7, 11])  # maj7 intervals
    assert shapes["closed"] == (0, 4, 7, 11)
    assert "drop2" in shapes and "shell" in shapes


# --- RE-2c: figures are gated on tertian-ness, not cardinality alone ---------

def test_non_tertian_four_note_chords_get_no_figure():
    # maj6 (0,4,7,9) and majadd9 (0,2,4,7) are four-note but NOT stacks of
    # thirds — they used to receive seventh-chord figures ("7", "6/5", ...).
    for name in ("maj6", "majadd9"):
        invs = _inversions(name)
        assert all(i.figured_bass is None for i in invs), name
        assert invs[0].position_name == "root position"


def test_sus_triads_get_no_figure():
    # sus4 (0,5,7) is three-note but not tertian — "5/3"/"6"/"6/4" would be wrong.
    invs = _inversions("sus4")
    assert all(i.figured_bass is None for i in invs)


def test_dim7_is_tertian_and_keeps_its_figures():
    invs = _inversions("dim7")  # (0,3,6,9): stacked minor thirds
    assert [i.figured_bass for i in invs] == ["7", "6/5", "4/3", "4/2"]


def test_non_tertian_voicing_recognition_reports_no_figure():
    # analyze_voicing shares the gate: a voiced C6 in root position gets a
    # position name but no figured bass.
    a = analyze_voicing(Realization.from_midi([48, 52, 55, 57], root_pc=0))  # C E G A
    assert a.position_name == "root position"
    assert a.figured_bass is None
