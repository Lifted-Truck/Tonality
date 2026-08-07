"""gap 25 slice — cadence-confirmed key areas.

Joins structural key areas to cadence detection: each area is judged against ITS
OWN key, asking the literature's #1 modulation discriminator ("a tonicization
does not incorporate a cadence in the tonicized key; a modulation does"). These
tests pin the join, the evidence-not-verdict contract, the honest refusals, and
the measured grid trap.
"""

from __future__ import annotations

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.temporal import confirm_key_areas


def _tri(root_pc, beat, dur=2):
    return [[beat, dur, 60 + root_pc + i] for i in (0, 4, 7)]


def _modulating():
    """C major (C-F-G-C x2) then G major (G-C-A-D x2) — both cadentially closed."""
    ev, t = [], 0
    for r in (0, 5, 7, 0) * 2:
        ev += _tri(r, t); t += 2
    for r in (7, 0, 2, 7) * 2:
        ev += _tri(r, t); t += 2
    return _canonical_sequence(ev)


def test_each_area_is_judged_in_its_own_key():
    r = confirm_key_areas(_modulating(), subdivisions=2)
    assert len(r.areas) >= 2
    tonics = [a.tonic_pc for a in r.areas]
    assert 0 in tonics and 7 in tonics          # a C area and a G area
    for area in r.areas:
        # the cadences reported for an area were detected against THAT tonic
        assert area.claim_possible
        assert area.confirmed is area.has_authentic


def test_a_cadence_confirmed_modulation_is_detected():
    r = confirm_key_areas(_modulating(), subdivisions=2)
    confirmed = [a for a in r.areas if a.confirmed]
    assert confirmed, "both areas close authentically in their own key"
    assert any("authentic" in a.cadence_types for a in confirmed)
    assert r.confirmed_areas == len(confirmed)


def test_the_grid_trap_is_real_and_directional():
    """MEASURED: a grid coarser than the harmonic rhythm hides the cadence.

    Same music, opposite answer — which is exactly why the module documents
    `subdivisions` as a usage trap rather than a tuning knob.
    """
    coarse = confirm_key_areas(_modulating(), subdivisions=1)
    fine = confirm_key_areas(_modulating(), subdivisions=2)
    assert fine.confirmed_areas > coarse.confirmed_areas
    assert all("authentic" not in a.cadence_types for a in coarse.areas)
    assert any("authentic" in a.cadence_types for a in fine.areas)
    # and the tell is visible in the output: fewer chords resolved per area
    assert sum(a.chords_considered for a in coarse.areas) < sum(
        a.chords_considered for a in fine.areas)


def test_unconfirmed_is_reported_as_absence_not_as_a_verdict():
    """An unconfirmed area must NOT read as 'this is a tonicization'."""
    r = confirm_key_areas(_modulating(), subdivisions=1)
    unconfirmed = [a for a in r.areas if a.claim_possible and not a.confirmed]
    assert unconfirmed
    for a in unconfirmed:
        assert a.reason and "ABSENCE" in a.reason.upper()
        # no field anywhere claims a modulation/tonicization verdict
        keys = set(a.to_dict())
        for forbidden in ("is_modulation", "is_tonicization", "verdict", "label"):
            assert forbidden not in keys


def test_too_few_chords_makes_no_claim():
    ev = _tri(0, 0) + _tri(0, 2)     # one repeated chord — no approach/arrival pair
    r = confirm_key_areas(_canonical_sequence(ev))
    assert r.no_claim_areas >= 1
    noclaim = [a for a in r.areas if not a.claim_possible]
    assert noclaim and "fewer than two" in noclaim[0].reason
    # a no-claim area is counted separately, never as "unconfirmed"
    assert r.confirmed_areas + r.unconfirmed_areas + r.no_claim_areas == len(r.areas)


def test_no_claim_areas_are_excluded_from_both_tallies():
    r = confirm_key_areas(_modulating(), subdivisions=2)
    claimable = [a for a in r.areas if a.claim_possible]
    assert r.confirmed_areas + r.unconfirmed_areas == len(claimable)


def test_reusing_a_structural_result_gives_the_same_answer():
    from mts.temporal import reduce_to_structural_keys

    seq = _modulating()
    structural = reduce_to_structural_keys(seq)
    a = confirm_key_areas(seq, subdivisions=2)
    b = confirm_key_areas(seq, structural=structural, subdivisions=2)
    assert a.to_dict() == b.to_dict()


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="non-empty"):
        confirm_key_areas(_canonical_sequence([]))


def test_deterministic():
    seq = _modulating()
    assert confirm_key_areas(seq, subdivisions=2).to_dict() == \
           confirm_key_areas(seq, subdivisions=2).to_dict()


def test_mcp_parity():
    from mts.mcp import tools

    ev, t = [], 0
    for r in (0, 5, 7, 0) * 2:
        ev += _tri(r, t); t += 2
    out = tools.confirm_key_areas(events=[list(e) for e in ev], subdivisions=2)
    assert "areas" in out and out["areas"]
    assert set(out["areas"][0]) >= {"tonic_pc", "mode", "confirmed", "claim_possible"}
