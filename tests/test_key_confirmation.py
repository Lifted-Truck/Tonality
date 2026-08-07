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


# --- the areas x spans join, written once (#256) --------------------------------

def test_area_indices_boundary_convention():
    """The shared join helper must keep the half-open, eps-tolerant convention
    both gap-25 modules had independently open-coded (audit #256)."""
    from mts.temporal.structural_key import area_indices

    class A:
        def __init__(self, s, e): self.start_beats, self.end_beats = s, e

    areas = [A(0.0, 8.0), A(8.0, 16.0)]
    #                                   ↓ within eps BELOW the 8.0 seam
    beats = [-1.0, 0.0, 7.5, 7.999999999, 8.0, 15.5, 16.0, 99.0]
    # The eps tolerance pulls a beat sitting a float-hair below a boundary into
    # the LATER area — absorbing accumulated beat arithmetic so a chord meant to
    # start the new area isn't stranded at the end of the old one. That is the
    # convention both call sites already had; it is pinned here, not chosen here.
    assert area_indices(areas, beats) == [None, 0, 0, 1, 1, 1, None, None]
    assert area_indices([], [0.0, 1.0]) == [None, None]
    assert area_indices(areas, []) == []


def test_area_indices_is_not_a_linear_rescan():
    """Structural gate, per AUDIT §6b: the join must not walk every area per beat.

    Timing is fixture-sensitive; the shape is not. A bisect touches O(log a)
    areas, so 10k beats over 500 areas must not cost ~5M comparisons.
    """
    from mts.temporal.structural_key import area_indices

    class A:
        def __init__(self, s, e):
            self.start_beats, self.end_beats = s, e
            A.touched = 0
        def __getattribute__(self, name):
            if name in ("start_beats", "end_beats"):
                A.touched += 1
            return object.__getattribute__(self, name)

    areas = [A(i * 4.0, (i + 1) * 4.0) for i in range(500)]
    A.touched = 0
    area_indices(areas, [i * 0.2 for i in range(10_000)])
    # a linear rescan averages ~250 areas/beat ⇒ millions of field reads
    assert A.touched < 100_000, f"{A.touched} field reads — the join went linear again"
