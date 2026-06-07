"""Tests for the analytical frame (AnalyticalContext + contextualize_chord)."""

import pytest

from mts.analysis import AnalyticalContext, contextualize_chord
from mts.core.chord import Chord
from mts.io.loaders import load_chord_qualities, load_scales

Q = load_chord_qualities()
S = load_scales()


def _chord(root, qual):
    return Chord.from_quality(root, Q[qual])


def _c_major():
    return AnalyticalContext(tonic_pc=0, key=S["Ionian"])


# --- AnalyticalContext frame ------------------------------------------------

def test_frame_predicates():
    assert AnalyticalContext().has_tonic is False
    assert AnalyticalContext(tonic_pc=0).has_tonic is True
    assert AnalyticalContext(tonic_pc=0).has_key is False
    assert _c_major().has_key is True


def test_interval_membership_and_degree():
    ctx = _c_major()
    assert ctx.interval_from_tonic(7) == 7
    assert ctx.in_key(7) is True       # G is in C major
    assert ctx.in_key(6) is False      # F# is not
    assert ctx.degree_of(0) == 0       # C -> degree 0
    assert ctx.degree_of(11) == 6      # B -> degree 6
    assert ctx.degree_of(6) is None    # chromatic


def test_helpers_none_without_key_or_tonic():
    bare = AnalyticalContext()
    assert bare.interval_from_tonic(7) is None
    assert bare.in_key(7) is None
    assert bare.degree_of(7) is None
    tonic_only = AnalyticalContext(tonic_pc=0)
    assert tonic_only.interval_from_tonic(7) == 7
    assert tonic_only.in_key(7) is None   # no key
    assert tonic_only.degree_of(7) is None


def test_invalid_tonic_rejected():
    with pytest.raises(ValueError):
        AnalyticalContext(tonic_pc=12)


# --- contextualize_chord ----------------------------------------------------

def test_diatonic_chord_placement():
    r = contextualize_chord(_chord(7, "7"), _c_major())  # G7 = V7 in C
    assert r.root_degree == 4
    assert r.is_diatonic is True
    assert r.chromatic_pcs == []
    assert r.root_interval_from_tonic == 7


def test_secondary_dominant_flags_chromatic_tone():
    r = contextualize_chord(_chord(2, "7"), _c_major())  # D7 = V/V, F# is chromatic
    assert r.is_diatonic is False
    assert r.chromatic_pcs == [6]
    assert r.root_degree == 1            # D is degree 1 (still diatonic as a root)
    assert r.tone_degrees == [1, None, 5, 0]


def test_borrowed_chord_root_not_in_key():
    r = contextualize_chord(_chord(3, "maj"), _c_major())  # Eb major (bIII)
    assert r.root_degree is None
    assert r.is_diatonic is False
    assert set(r.chromatic_pcs) == {3, 10}


def test_tonic_without_key_gives_intervals_only():
    r = contextualize_chord(_chord(7, "maj"), AnalyticalContext(tonic_pc=0))
    assert r.root_interval_from_tonic == 7
    assert r.root_degree is None
    assert r.is_diatonic is False
    assert r.key_name is None


def test_requires_a_tonal_center():
    with pytest.raises(ValueError):
        contextualize_chord(_chord(0, "maj"), AnalyticalContext())
