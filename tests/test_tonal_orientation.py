"""Pitch-space tonal orientation (Audiology brief-17): a voicing-continuous
fifths-space angle. Verifies A6's three requirements — reduces to arg(f5) for a
neutral voicing, rotates predictably under transposition, varies with voicing.
"""

from __future__ import annotations

import math

import pytest

from mts.core.bitmask import mask_from_pcs
from mts.core.setclass import dft_phases
from mts.representation import tonal_orientation


def test_uniform_closed_voicing_reduces_to_arg_f5():
    # one note per pc, uniform weights → the pc-level fifths centroid arg(f5).
    o = tonal_orientation([60, 64, 67])  # C major, closed
    arg_f5 = dft_phases(mask_from_pcs({0, 4, 7}))[4]
    assert o.angle_radians == pytest.approx(arg_f5)
    assert o.spec_level == "registered" and o.note_count == 3


def test_rotates_predictably_under_transposition():
    a0 = tonal_orientation([60, 64, 67]).angle_radians
    a2 = tonal_orientation([62, 66, 69]).angle_radians  # T+2
    expected = (a0 + 2 * math.pi * 7 * 2 / 12) % (2 * math.pi)
    assert a2 % (2 * math.pi) == pytest.approx(expected)


def test_bass_weighting_makes_inversions_distinct():
    # uniform: same pcs+multiplicities → same angle (inversion-invariant).
    root_u = tonal_orientation([60, 64, 67], octave_decay=1.0).angle_radians
    inv_u = tonal_orientation([64, 67, 72], octave_decay=1.0).angle_radians
    assert root_u == pytest.approx(inv_u)
    # bass-weighted: the inversion moves the angle (voicing-continuous).
    root_w = tonal_orientation([60, 64, 67], octave_decay=0.5).angle_radians
    inv_w = tonal_orientation([64, 67, 72], octave_decay=0.5).angle_radians
    assert abs(root_w - inv_w) > 1e-6


def test_spread_shifts_a_bass_weighted_voicing():
    close = tonal_orientation([48, 52, 55], octave_decay=0.5).angle_radians
    spread = tonal_orientation([48, 64, 79], octave_decay=0.5).angle_radians  # same pcs, wide
    assert abs(close - spread) > 1e-6


def test_validation_and_serialisation():
    import json
    o = tonal_orientation([60, 64, 67], octave_decay=0.7)
    json.dumps(o.to_dict())
    assert tonal_orientation([60, 64, 67], octave_decay=0.7).to_dict() == o.to_dict()
    assert 0.0 <= o.focus <= 1.0
    with pytest.raises(ValueError, match="at least one sounding pitch"):
        tonal_orientation([])
    with pytest.raises(ValueError, match="octave_decay must be positive"):
        tonal_orientation([60], octave_decay=0.0)
