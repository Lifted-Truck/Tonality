"""gap 28 — GM percussion roles + named drum-pattern matching.

The engine maps channel-10 notes to drum ROLES through a versioned prior and
matches named rhythmic patterns as exact per-bar predicates, reported as a
coverage RATE with the matching bars itemized. These tests pin the mapping, the
required-only matching semantics, the meter scoping, the honest-unmapped and
channel-detection behavior, and — the doctrinal one — that no genre verdict is
ever emitted.
"""

from __future__ import annotations

import pytest

from mts.io.loaders import load_gm_percussion, load_named_drum_pattern, list_named_drum_patterns
from mts.mcp.tools import _canonical_sequence
from mts.temporal import drum_pattern_analysis

KICK, SNARE, HAT, OPEN_HAT, TOM = 36, 38, 42, 46, 45


def _bars(n=4, *, kick=(0, 1, 2, 3), snare=(1, 3), hat=(0.5, 1.5, 2.5, 3.5), voice="t1c9"):
    ev = []
    for bar in range(n):
        b0 = bar * 4
        ev += [[b0 + b, 0.1, KICK, 110, voice] for b in kick]
        ev += [[b0 + b, 0.1, SNARE, 100, voice] for b in snare]
        ev += [[b0 + b, 0.1, HAT, 70, voice] for b in hat]
    return _canonical_sequence(ev)


def _match(result, name):
    for m in result.matches:
        if m.name == name:
            return m
    return None


# --- the GM map (the unblocker) --------------------------------------------------

def test_gm_map_is_a_cited_versioned_prior():
    gm = load_gm_percussion()
    assert gm.version == "gm-percussion.1"
    assert gm.source and gm.license          # provenance stamped, per house style
    assert gm.role_of(36) == "kick"
    assert gm.role_of(38) == "snare" and gm.role_of(40) == "snare"   # both snares
    assert gm.role_of(42) == "hihat_closed" and gm.role_of(46) == "hihat_open"
    assert gm.role_of(45) == "tom" and gm.role_of(50) == "tom"       # toms collapse
    assert gm.name_of(36) == "Bass Drum 1"


def test_pitches_outside_the_gm_range_have_no_drum_meaning():
    gm = load_gm_percussion()
    assert gm.role_of(20) is None and gm.role_of(100) is None


# --- role extraction -------------------------------------------------------------

def test_roles_and_channel_10_detection():
    r = drum_pattern_analysis(_bars())
    assert r.channel_10_detected is True
    assert r.map_version == "gm-percussion.1"
    assert {x.role for x in r.roles} == {"kick", "snare", "hihat_closed"}
    assert {x.role: x.count for x in r.roles}["kick"] == 16   # 4 bars x 4


def test_unmapped_pitches_are_reported_not_guessed():
    ev = [[0, 0.1, KICK, 100, "t1c9"], [0.5, 0.1, 20, 100, "t1c9"]]  # 20 = not GM percussion
    r = drum_pattern_analysis(_canonical_sequence(ev))
    assert r.unmapped_pitches == [20]
    assert {x.role for x in r.roles} == {"kick"}


def test_non_channel_10_is_flagged_not_silently_mapped():
    r = drum_pattern_analysis(_bars(voice="t0c0"))
    assert r.channel_10_detected is False     # the map is being applied speculatively
    assert r.roles                            # still analyzed, but the caller can see why


# --- named-pattern matching ------------------------------------------------------

def test_house_beat_matches_the_expected_three():
    r = drum_pattern_analysis(_bars())
    for name in ("four-on-the-floor", "backbeat", "offbeat-hats"):
        m = _match(r, name)
        assert m is not None and m.coverage == 1.0, name
        assert m.bars_matched == m.bars_considered == 4
        assert m.matched_bars == [0, 1, 2, 3]


def test_matching_is_required_only_extra_hits_do_not_disqualify():
    # a four-on-the-floor bar with an extra offbeat kick is still four-on-the-floor
    r = drum_pattern_analysis(_bars(kick=(0, 1, 2, 2.5, 3)))
    assert _match(r, "four-on-the-floor").coverage == 1.0


def test_a_missing_beat_drops_coverage_proportionally():
    ev = []
    for bar in range(4):
        b0 = bar * 4
        beats = (0, 1, 2, 3) if bar < 3 else (0, 1, 2)   # last bar drops beat 4
        ev += [[b0 + b, 0.1, KICK, 110, "t1c9"] for b in beats]
    r = drum_pattern_analysis(_canonical_sequence(ev))
    m = _match(r, "four-on-the-floor")
    assert m.bars_matched == 3 and m.bars_considered == 4
    assert m.coverage == 0.75 and m.matched_bars == [0, 1, 2]


def test_absent_role_makes_no_claim_rather_than_scoring_zero():
    # kick only: the snare/hat patterns must be ABSENT from matches, not 0.0 —
    # a role that never sounds yields no evidence either way.
    r = drum_pattern_analysis(_bars(snare=(), hat=()))
    assert _match(r, "four-on-the-floor").coverage == 1.0
    assert _match(r, "backbeat") is None
    assert _match(r, "offbeat-hats") is None


def test_overlapping_patterns_both_report():
    # continuous eighth hats necessarily also satisfy offbeat hats — both appear,
    # and the pair is what distinguishes them.
    r = drum_pattern_analysis(_bars(hat=(0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5)))
    assert _match(r, "eighth-note-hats").coverage == 1.0
    assert _match(r, "offbeat-hats").coverage == 1.0


def test_half_time_distinguishes_from_full_backbeat():
    full = drum_pattern_analysis(_bars(snare=(1, 3)))
    half = drum_pattern_analysis(_bars(snare=(2,)))
    assert _match(full, "backbeat").coverage == 1.0
    assert _match(half, "backbeat").coverage == 0.0      # not a full backbeat
    assert _match(half, "half-time-backbeat").coverage == 1.0


def test_tresillo():
    r = drum_pattern_analysis(_bars(kick=(0, 1.5, 3), snare=(), hat=()))
    assert _match(r, "tresillo-kick").coverage == 1.0
    assert _match(r, "four-on-the-floor").coverage == 0.0


def test_patterns_are_scoped_to_their_declared_meter():
    # 3/4 bars: a 4/4-declared pattern must make NO claim about them.
    from mts.temporal import MeterMap
    ev = []
    for bar in range(4):
        ev += [[bar * 3 + b, 0.1, KICK, 110, "t1c9"] for b in range(3)]
    seq = _canonical_sequence(ev)
    seq = type(seq)(events=seq.events, tempo=seq.tempo, meter=MeterMap.constant(3, 4))
    r = drum_pattern_analysis(seq)
    assert _match(r, "four-on-the-floor") is None   # 4/4 pattern, 3/4 material


# --- honesty / doctrine ----------------------------------------------------------

def test_no_genre_verdict_is_ever_emitted():
    r = drum_pattern_analysis(_bars()).to_dict()
    blob = repr(r).lower()
    for forbidden in ("genre", "house", "techno", "disco", "style", "is_a"):
        assert forbidden not in blob, f"analysis leaked a {forbidden!r} verdict"


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="non-empty"):
        drum_pattern_analysis(_canonical_sequence([]))


def test_deterministic():
    a = drum_pattern_analysis(_bars()).to_dict()
    b = drum_pattern_analysis(_bars()).to_dict()
    assert a == b


# --- library + MCP ----------------------------------------------------------------

def test_named_library_loads_and_is_traversal_guarded():
    assert "four-on-the-floor" in list_named_drum_patterns()
    assert load_named_drum_pattern("four-on-the-floor")["required_beats"] == [0.0, 1.0, 2.0, 3.0]
    with pytest.raises(ValueError):
        load_named_drum_pattern("../../../port/pin")     # the #237 guard applies here too


def test_mcp_parity():
    from mts.mcp import tools

    events = [[b, 0.1, KICK, 110, "t1c9"] for b in range(4)]
    out = tools.drum_pattern_analysis(events=events)
    assert out["map_version"] == "gm-percussion.1"
    assert any(m["name"] == "four-on-the-floor" for m in out["matches"])
