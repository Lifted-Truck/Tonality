"""Colour-content descriptor (Phase 5 — Audiology brief-15 Ask 3).

The two resultant-vector constructions behind the somatic-colour wheels, as
render-agnostic data. The headline test is A6's independent enumeration: all 4083
pc-sets land on exactly 185 distinct interval-colour positions — a cross-
implementation check that our pentagon/normalization convention matches theirs.
"""

from __future__ import annotations

import math

import pytest

from mts.core.bitmask import mask_from_pcs, pcs_from_mask
from mts.core.setclass import dft_components
from mts.representation import colour_content_descriptor


def _pos(pcs):
    ic = colour_content_descriptor(pcs).interval_content
    return (ic.x, ic.y)


def test_matches_audiology_185_position_enumeration():
    # brief-15: all pc-sets with |S|>=2 → exactly 185 distinct interval-colour
    # wheel positions (199 distinct interval vectors collapsing onto 185 points).
    positions = set()
    for mask in range(4096):
        if bin(mask).count("1") >= 2:
            positions.add(_pos(pcs_from_mask(mask)))
    assert len(positions) == 185


def test_pure_single_interval_sets_reach_full_saturation():
    # The five non-tritone dyads + the augmented triad are pure-single-IC → focus 1;
    # the tritone dyad is pure ic6 (central) → focus 0 (grey).
    for ic_semitone in (1, 2, 3, 4, 5):
        d = colour_content_descriptor([0, ic_semitone])
        assert d.interval_content.focus == pytest.approx(1.0)
    assert colour_content_descriptor([0, 4, 8]).interval_content.focus == pytest.approx(1.0)
    assert colour_content_descriptor([0, 6]).interval_content.focus == pytest.approx(0.0)


def test_interval_content_is_transposition_invariant_and_collapses_inversions():
    # root-blind: depends only on the interval vector.
    assert _pos([0, 4, 7]) == _pos([2, 6, 9])           # transposition
    assert _pos([0, 4, 7]) == _pos([0, 3, 7])           # major / minor collapse
    assert _pos([0, 4, 7, 10]) == _pos([0, 3, 6, 10])   # dom7 / m7b5 collapse


def test_fifths_centroid_is_f5_over_n_and_transposition_variant():
    pcs = [0, 4, 7]
    d = colour_content_descriptor(pcs)
    f5 = dft_components(mask_from_pcs(set(pcs)))[5]
    n = len(pcs)
    assert d.fifths_centroid.x == pytest.approx(f5.real / n)
    assert d.fifths_centroid.y == pytest.approx(f5.imag / n)
    assert d.fifths_centroid.angle_radians == pytest.approx(math.atan2(f5.imag, f5.real))
    # root-aware: rotates under transposition (carries absolute position)
    assert colour_content_descriptor([2, 6, 9]).fifths_centroid != d.fifths_centroid


def test_spec_level_and_validation_and_serialisation():
    import json
    d = colour_content_descriptor([0, 4, 7])
    assert d.spec_level == "identity_only"
    assert d.interval_vector == [0, 0, 1, 1, 1, 0]
    json.dumps(d.to_dict())
    assert colour_content_descriptor([0, 4, 7]).to_dict() == d.to_dict()  # deterministic
    with pytest.raises(ValueError, match="at least one pitch class"):
        colour_content_descriptor([])
