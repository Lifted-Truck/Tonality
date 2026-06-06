"""Tests for the Realization type and its reduction to an identity key."""

import pytest

from mts.core.bitmask import mask_from_pcs
from mts.core.realization import Realization
from mts.core.spec_level import VOICING, VOICING_TEMPLATE


def test_reduce_to_key_drops_register_and_doublings():
    # C3 E3 G3 C4 -> identity key is just {0, 4, 7}.
    real = Realization.from_midi([48, 52, 55, 60], root_pc=0)
    assert real.reduce_to_key() == mask_from_pcs([0, 4, 7])
    assert real.distinct_pcs == (0, 4, 7)


def test_pcs_preserve_voicing_order_and_doublings():
    real = Realization.from_midi([48, 52, 55, 60], root_pc=0)
    assert real.pcs == (0, 4, 7, 0)
    assert real.doublings == (0,)


def test_bass_is_lowest_sounding_pitch():
    # Out-of-order input; bass is by absolute height, not list position.
    real = Realization.from_midi([60, 48, 55])
    assert real.bass.midi == 48


def test_rooted_voicing_vs_rootless_template():
    voicing = Realization.from_midi([48, 52, 55], root_pc=0)
    assert voicing.is_rooted
    assert voicing.spec_level == VOICING

    template = Realization.from_midi([48, 52, 55])
    assert not template.is_rooted
    assert template.spec_level == VOICING_TEMPLATE


def test_frozen_and_hashable():
    a = Realization.from_midi([48, 52, 55], root_pc=0)
    b = Realization.from_midi([48, 52, 55], root_pc=0)
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


def test_empty_realization_rejected():
    with pytest.raises(ValueError):
        Realization(())


def test_out_of_range_root_rejected():
    with pytest.raises(ValueError):
        Realization.from_midi([48], root_pc=12)
