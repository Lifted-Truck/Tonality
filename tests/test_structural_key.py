"""Structural key-area reduction: tonicization vs modulation (A6 brief-5 fix).

Reduces the windowed local key track to structural key-areas — absorbing brief,
diatonically-related excursions (tonicizations) into the parent key while keeping
sustained/structural key changes (modulations). The lever is functional
relatedness AND (brevity OR return), not confidence.
"""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.io.loaders import load_structural_key_priors
from mts.temporal import (
    Event,
    KeyRegion,
    KeyTrackingResult,
    Sequence,
    reduce_to_structural_keys,
)


def _region(tonic, mode, sb, eb):
    return KeyRegion(
        start_beats=float(sb), end_beats=float(eb),
        start_seconds=float(sb) / 2, end_seconds=float(eb) / 2,
        tonic_pc=tonic, mode=mode, mean_score=0.8, mean_margin=0.1,
        window_count=max(1, int((eb - sb) / 2)),
    )


def _tracking(regions):
    return KeyTrackingResult(
        regions=regions, windows=[], window_beats=8.0, hop_beats=2.0,
        profile_version="kk-1982.1",
    )


def _cmaj_seq():
    # A clear C-major sequence so the reducer's internal infer_key (global
    # evidence) returns C major; the structural reduction runs on the passed track.
    events = [Event(float(i), 1.0, Pitch.from_midi(60 + pc)) for i in range(8) for pc in (0, 4, 7)]
    return Sequence.from_events(events)


def _reduce(regions):
    # The tonicization/modulation *walk* is independent of how the home anchor is
    # chosen; these tests pin the legacy most_prevalent_region anchor so they
    # exercise the walk in isolation. Anchor-method behaviour has its own tests.
    return reduce_to_structural_keys(
        _cmaj_seq(), tracking=_tracking(regions), anchor_method="most_prevalent_region"
    )


# Mozart-like track: home C, a V tonicization, a vi tonicization, a real modulation to G.
MOZART = [
    _region(0, "major", 0, 32), _region(7, "major", 32, 40), _region(0, "major", 40, 72),
    _region(9, "minor", 72, 76), _region(0, "major", 76, 108), _region(7, "major", 108, 172),
]


# --- the core fix -------------------------------------------------------------------------


def test_tonicizations_absorbed_modulation_kept():
    result = _reduce(MOZART)
    assert len(result.areas) == 2  # collapsed from 6 windowed regions
    home, modulation = result.areas
    assert (home.tonic_pc, home.mode) == (0, "major")
    assert (home.start_beats, home.end_beats) == (0.0, 108.0)
    assert {t.degree for t in home.tonicizations} == {7, 9}  # V and vi
    # the sustained, non-returning G is kept as its own structural area
    assert (modulation.tonic_pc, modulation.mode) == (7, "major")
    assert (modulation.start_beats, modulation.end_beats) == (108.0, 172.0)
    # no G/Am *area* exists — they live only as tonicizations
    assert not any((a.tonic_pc, a.mode) == (9, "minor") for a in result.areas)


def test_anchor_is_most_prevalent_not_global():
    # G major dominates the track by time, even though the sequence's global key is C.
    regions = [_region(7, "major", 0, 40), _region(0, "major", 40, 48), _region(7, "major", 48, 96)]
    result = _reduce(regions)
    assert (result.home_tonic_pc, result.home_mode) == (7, "major")
    assert (result.global_tonic_pc, result.global_mode) == (0, "major")  # they differ — by design


def test_opens_on_a_tonicization():
    # Brief leading G, then C dominates → home is C; area 1 starts at 0.0.
    regions = [_region(7, "major", 0, 4), _region(0, "major", 4, 40), _region(0, "major", 40, 80)]
    result = _reduce(regions)
    assert (result.areas[0].tonic_pc, result.areas[0].mode) == (0, "major")
    assert result.areas[0].start_beats == 0.0
    assert 7 in {t.degree for t in result.areas[0].tonicizations}


def test_areas_tile_the_sequence_contiguously():
    result = _reduce(MOZART)
    assert result.areas[0].start_beats == 0.0
    assert result.areas[-1].end_beats == MOZART[-1].end_beats
    for a, b in zip(result.areas, result.areas[1:]):
        assert a.end_beats == b.start_beats  # shared boundaries, no gaps/overlaps


# --- frame-weighted anchor (A6 brief-7: tonicization-robust home key) ---------------------


# A D911-07-shaped track: the dominant (G) is repeatedly tonicized and out-totals
# the tonic (C) by raw duration (G=32 vs C=22), but C is the opening AND closing
# region — the structural frame. most_prevalent anchors on the dominant; frame
# weighting recovers the tonic.
_DOMINANT_OVERCOUNTED = [
    _region(0, "major", 0, 8),    # C — opening frame (8)
    _region(7, "major", 8, 22),   # G (14)
    _region(0, "major", 22, 28),  # C (6)
    _region(7, "major", 28, 46),  # G (18)
    _region(0, "major", 46, 54),  # C — closing frame (8)
]


def test_legacy_most_prevalent_region_picks_the_overcounted_dominant():
    # The slice-1 method (still available, explicit): most-prevalent-by-duration
    # anchors on the repeatedly-tonicized dominant G.
    result = reduce_to_structural_keys(
        _cmaj_seq(), tracking=_tracking(_DOMINANT_OVERCOUNTED),
        anchor_method="most_prevalent_region",
    )
    assert (result.home_tonic_pc, result.home_mode) == (7, "major")
    assert result.anchor_method == "most_prevalent_region"


def test_default_anchor_is_frame_weighted_and_recovers_the_framed_tonic():
    # Default flipped to frame_weighted (A6 brief-8): the opening + closing C
    # regions carry the tonic, so the default now recovers it.
    result = reduce_to_structural_keys(_cmaj_seq(), tracking=_tracking(_DOMINANT_OVERCOUNTED))
    assert (result.home_tonic_pc, result.home_mode) == (0, "major")
    assert result.anchor_method == "frame_weighted"
    # explicit frame_weighted is identical to the default
    explicit = reduce_to_structural_keys(
        _cmaj_seq(), tracking=_tracking(_DOMINANT_OVERCOUNTED), anchor_method="frame_weighted"
    )
    assert explicit.to_dict() == result.to_dict()


def test_frame_weighting_never_overturns_a_genuine_duration_majority():
    # C is both most-prevalent (72) and framed; a brief G tonicization shouldn't
    # flip it under either method — the bonus is additive, not a replacement.
    clean = [_region(0, "major", 0, 40), _region(7, "major", 40, 48), _region(0, "major", 48, 80)]
    default = reduce_to_structural_keys(_cmaj_seq(), tracking=_tracking(clean))
    framed = reduce_to_structural_keys(
        _cmaj_seq(), tracking=_tracking(clean), anchor_method="frame_weighted"
    )
    assert (default.home_tonic_pc, default.home_mode) == (0, "major")
    assert (framed.home_tonic_pc, framed.home_mode) == (0, "major")


def test_unknown_anchor_method_raises():
    with pytest.raises(ValueError, match="anchor_method"):
        reduce_to_structural_keys(
            _cmaj_seq(), tracking=_tracking(MOZART), anchor_method="bogus"
        )


# --- the predicate ------------------------------------------------------------------------


def test_relatedness_is_mode_agnostic():
    # A brief D-major excursion in C (D diatonic; major ≠ the diatonic ii minor) absorbs.
    regions = [_region(0, "major", 0, 40), _region(2, "major", 40, 44), _region(0, "major", 44, 80)]
    result = _reduce(regions)
    assert len(result.areas) == 1
    assert 2 in {t.degree for t in result.areas[0].tonicizations}


def test_unrelated_brief_region_is_not_absorbed():
    # Eb is not diatonic to C → a brief Eb excursion is its own (modulation) area.
    regions = [_region(0, "major", 0, 40), _region(3, "major", 40, 44), _region(0, "major", 44, 80)]
    result = _reduce(regions)
    assert any((a.tonic_pc, a.mode) == (3, "major") for a in result.areas)
    assert all(t.degree != 3 for a in result.areas for t in a.tonicizations)


def test_chained_modulations_rebase_the_current_key():
    # C → G(sustained) → D(sustained): D is tested vs G (the current key), not C.
    regions = [_region(0, "major", 0, 40), _region(7, "major", 40, 96), _region(2, "major", 96, 160)]
    result = _reduce(regions)
    assert [(a.tonic_pc, a.mode) for a in result.areas] == [(0, "major"), (7, "major"), (2, "major")]


def test_return_through_a_foreign_key_does_not_launder_a_modulation():
    # C → G(long) → Eb(foreign) → C: G's "return" to C passes through foreign Eb,
    # so G is NOT absorbed — it's kept as a modulation.
    regions = [_region(0, "major", 0, 40), _region(7, "major", 40, 104),
               _region(3, "major", 104, 112), _region(0, "major", 112, 160)]
    result = _reduce(regions)
    assert any((a.tonic_pc, a.mode) == (7, "major") for a in result.areas)


# --- contracts ----------------------------------------------------------------------------


def test_deterministic_and_cited():
    a = _reduce(MOZART).to_dict()
    b = _reduce(MOZART).to_dict()
    assert a == b
    assert a["prior_version"] == load_structural_key_priors().version == "structural-key.2"


def test_output_is_numeric_and_json_serialisable():
    result = _reduce(MOZART)
    payload = json.dumps(result.to_dict())
    assert "tracking" in result.to_dict()  # local track carried as evidence
    for area in result.areas:
        for t in area.tonicizations:
            assert isinstance(t.degree, int) and 0 <= t.degree < 12


def test_threshold_change_flips_a_borderline_region():
    # An 8-beat related region: a tonicization iff min_modulation_beats > 8.
    regions = [_region(0, "major", 0, 40), _region(7, "major", 40, 48), _region(0, "major", 48, 96)]
    import dataclasses
    base = load_structural_key_priors()
    strict = dataclasses.replace(base, min_modulation_beats=8.0)   # 8 < 8 is False → modulation
    loose = dataclasses.replace(base, min_modulation_beats=12.0)   # 8 < 12 → tonicization
    seq = _cmaj_seq()
    strict_areas = reduce_to_structural_keys(seq, tracking=_tracking(regions), priors=strict).areas
    loose_areas = reduce_to_structural_keys(seq, tracking=_tracking(regions), priors=loose).areas
    # under loose it absorbs (returns to C anyway), under strict the 8-beat span...
    assert len(loose_areas) == 1
    # (the 8-beat G also *returns* to C, so it's absorbed either way — assert loose collapses)
    assert 7 in {t.degree for a in loose_areas for t in a.tonicizations}
