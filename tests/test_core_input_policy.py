"""RE-3e/f: one input policy across core — validate, don't silently normalize.

The identity layer had four places that silently reinterpreted bad input where
their siblings raise (`mask_from_pcs` raises on pc 12; `Scale.from_degrees`
wrapped it), plus a symmetry sentinel that leaked into results as a false
claim. These tests pin the errors-not-guesses rulings.
"""

from __future__ import annotations

import pytest

from mts.session import mask_from_text
from mts.core.chord import Chord
from mts.core.pitch import Pitch, parse_pitch_token
from mts.core.quality import ChordQuality
from mts.core.scale import Scale
from mts.core.symmetry import rotational_period, rotational_steps


# --- Pitch: the one previously-unvalidated primitive -------------------------

def test_pitch_rejects_contradictory_fields():
    with pytest.raises(ValueError, match="Inconsistent Pitch"):
        Pitch(midi=60, pc=5, octave=4)  # C4's pc is 0, not 5
    with pytest.raises(ValueError, match="Inconsistent Pitch"):
        Pitch(midi=60, pc=0, octave=3)  # C4's octave is 4


def test_pitch_constructors_stay_consistent():
    assert Pitch.from_midi(60) == Pitch(midi=60, pc=0, octave=4)
    assert Pitch.from_components(pc=9, octave=3) == Pitch.from_midi(57)


def test_parse_pitch_token_rejects_negative_ints():
    # "-3" used to silently wrap to pc 9.
    with pytest.raises(ValueError, match="[Nn]egative"):
        parse_pitch_token("-3")
    assert parse_pitch_token("9").pc == 9
    assert parse_pitch_token("60").pitch == Pitch.from_midi(60)


# --- validate BEFORE mod-12 (matching mask_from_pcs) --------------------------

def test_scale_from_degrees_rejects_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        Scale.from_degrees("bad", [0, 4, 12])  # 12 used to wrap to 0
    with pytest.raises(ValueError, match="out of range"):
        Scale.from_degrees("bad", [-1, 4, 7])  # -1 used to wrap to 11


def test_quality_from_intervals_rejects_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        ChordQuality.from_intervals("bad", [0, 4, 14])  # a "9th" is pc 2, say so
    with pytest.raises(ValueError, match="out of range"):
        ChordQuality.from_intervals("bad", [0, 4, 7], tensions=[14])


# --- mask_from_text: no binary-vs-decimal guessing ----------------------------

def test_mask_from_text_explicit_forms():
    assert mask_from_text("0b10") == 2
    assert mask_from_text("101010110101") == 2741  # full 12 bits: unambiguous
    assert mask_from_text("2741") == 2741
    assert mask_from_text("145") == 145  # non-0/1 digits: plainly decimal


def test_mask_from_text_ambiguous_and_out_of_range_raise():
    with pytest.raises(ValueError, match="Ambiguous"):
        mask_from_text("10")  # binary 2 or decimal 10? — say which
    with pytest.raises(ValueError, match="out of range"):
        mask_from_text("5000")  # used to be silently truncated to 12 bits


# --- rotational_steps: sentinel removed ---------------------------------------

def test_rotational_steps_empty_for_asymmetric_sets():
    maj = 0b000010010001  # {0,4,7}: no nontrivial rotational symmetry
    assert rotational_steps(maj) == ()  # was (12,) — a false symmetry claim
    assert rotational_steps(0b000100010001) == (4, 8)  # augmented
    assert rotational_period(maj) == 12  # the period still says "asymmetric"


def test_empty_set_convention_matches_core_everywhere():
    # Core: the empty set is trivially invariant (period 1, every step) —
    # and the exported set-class table row 0 already pins period 1. Analysis
    # used to hardcode period 0 for empty inputs, disagreeing with both.
    assert rotational_period(0) == 1
    assert rotational_steps(0) == tuple(range(1, 12))
