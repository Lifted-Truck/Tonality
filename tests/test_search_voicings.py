"""Tests for bounded voicing enumeration (search_voicings, gap 17 slice 1).

The central oracle is independent brute-force construction: a voicing search
over a window must equal itertools.product over the per-pc candidates with the
same filters applied by hand. Small hand cases pin the semantics (window
inclusivity, mod-12 intervals-over-bass, template searches, VL ranking).
"""

from itertools import product

import pytest

from mts.analysis.voice_leading import voice_leading_realized
from mts.core.realization import Realization
from mts.search import search_voicings
from mts.search.identities import SearchConstraintError

CMAJ7 = [0, 4, 7, 11]


def _brute(pcs, lo, hi):
    """All register assignments of pcs in [lo, hi], as sorted midi tuples."""
    cands = [[m for m in range(lo, hi + 1) if m % 12 == pc] for pc in sorted(set(pcs))]
    return {tuple(sorted(combo)) for combo in product(*cands)}


# --- the space ----------------------------------------------------------------

def test_single_octave_window_has_exactly_one_voicing():
    result = search_voicings(CMAJ7, root=0, constraints={"register": [60, 71]})
    assert result.space == 1
    assert result.count == 1
    assert result.matches[0].midi == (60, 64, 67, 71)
    assert result.matches[0].voicing_type == "closed"


def test_enumeration_equals_independent_brute_force():
    result = search_voicings(CMAJ7, root=0, constraints={"register": [48, 71]})
    expected = _brute(CMAJ7, 48, 71)
    assert result.space == 16  # 2 candidates per pc, 2^4
    assert {m.midi for m in result.matches} == expected
    assert result.count == len(expected)


def test_window_is_inclusive_both_ends():
    # pc 0 at both edges: exactly midi 60 and 72 in [60, 72].
    result = search_voicings([0], root=0, constraints={"register": [60, 72]})
    assert {m.midi for m in result.matches} == {(60,), (72,)}


def test_empty_window_for_a_pc_yields_zero_matches_not_an_error():
    # pc 1 (C#) has no representative in [60, 60].
    result = search_voicings([0, 1], root=0, constraints={"register": [60, 60]})
    assert result.space == 0
    assert result.count == 0


def test_space_guard_raises_with_actionable_message():
    with pytest.raises(SearchConstraintError) as exc:
        search_voicings(list(range(12)), root=0, constraints={"register": [0, 127]})
    assert any("Narrow the window" in e for e in exc.value.errors)


# --- filters ------------------------------------------------------------------

def test_spread_filter_matches_hand_filtered_brute_force():
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [48, 71], "spread": {"lte": 12}}
    )
    expected = {v for v in _brute(CMAJ7, 48, 71) if v[-1] - v[0] <= 12}
    assert {m.midi for m in result.matches} == expected


def test_bass_pc_and_top_pc():
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [48, 71], "bass_pc": 0, "top_pc": 11}
    )
    assert result.count >= 1
    assert all(m.midi[0] % 12 == 0 and m.midi[-1] % 12 == 11 for m in result.matches)


def test_no_interval_over_bass_is_mod_12():
    # With bass B (59), the C above (60 or 72) is a directed pc-interval of 1 —
    # forbidding [1] must reject every bass-B voicing that has any C above it,
    # in ANY octave (mod-12 semantics, not literal semitone count).
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [59, 72], "no_interval_over_bass": [1]}
    )
    for m in result.matches:
        assert not (m.midi[0] % 12 == 11 and any(x % 12 == 0 for x in m.midi[1:]))
        assert 1 not in m.intervals_over_bass


def test_voicing_type_filters_to_named_shapes():
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [48, 83], "voicing_type": "drop2"}
    )
    assert result.count >= 1
    # drop2 of [0,4,7,11] drops the 2nd-from-top (7) an octave: shape (0,9,16,23)...
    # trust the registry: every match's spacing equals the drop2 fingerprint.
    from mts.analysis.voicings import voicing_shapes

    fingerprint = voicing_shapes([0, 4, 7, 11])["drop2"]
    assert all(tuple(x - m.midi[0] for x in m.midi) == fingerprint for m in result.matches)


# --- smoothness / ranking (fork D + gap 17's ranking half) ---------------------

def test_vl_from_matches_voice_leading_realized_exactly():
    ref = [60, 64, 67, 71]
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [55, 76]}, from_voicing=ref
    )
    source = Realization.from_midi(ref)
    for m in result.matches:
        expected = voice_leading_realized(source, Realization.from_midi(m.midi)).distance
        assert m.vl_from == expected


def test_matches_ranked_by_vl_when_reference_given():
    result = search_voicings(
        CMAJ7, root=0, constraints={"register": [48, 84]}, from_voicing=[60, 64, 67, 71]
    )
    vls = [m.vl_from for m in result.matches]
    assert vls == sorted(vls)
    assert result.matches[0].midi == (60, 64, 67, 71)  # the reference itself, vl 0
    assert result.matches[0].vl_from == 0


def test_max_voice_leading_is_a_ceiling():
    result = search_voicings(
        CMAJ7, root=0,
        constraints={"register": [48, 84], "max_voice_leading": 4},
        from_voicing=[60, 64, 67, 71],
    )
    assert result.count >= 1
    assert all(m.vl_from <= 4 for m in result.matches)


def test_unequal_cardinality_reference_works():
    # 4-voice reference against 5-note Cmaj9 candidates (surjection path).
    result = search_voicings(
        [0, 4, 7, 11, 2], root=0,
        constraints={"register": [55, 76], "max_voice_leading": 10},
        from_voicing=[60, 64, 67, 71],
    )
    assert result.count >= 1
    assert all(m.vl_from is not None for m in result.matches)


# --- templates (the registered+rootless corner) --------------------------------

def test_rootless_template_search_works_and_is_unlabeled():
    result = search_voicings(CMAJ7, constraints={"register": [60, 71]})
    assert result.root is None
    assert result.count == 1
    assert result.matches[0].voicing_type is None


def test_voicing_type_requires_root():
    with pytest.raises(SearchConstraintError) as exc:
        search_voicings(CMAJ7, constraints={"register": [60, 71], "voicing_type": "closed"})
    assert any("requires a root" in e for e in exc.value.errors)


# --- honesty: limit / count / space --------------------------------------------

def test_limit_cuts_reported_but_count_stays_total():
    result = search_voicings(CMAJ7, root=0, constraints={"register": [48, 71]}, limit=3)
    assert result.count == 16
    assert len(result.matches) == 3
    assert result.truncated is True


def test_deterministic_order_without_reference_is_spread_then_pitches():
    result = search_voicings(CMAJ7, root=0, constraints={"register": [48, 71]})
    keys = [(m.spread, m.midi) for m in result.matches]
    assert keys == sorted(keys)


# --- validation (strict + total) ------------------------------------------------

def test_register_is_required_with_cardinal_rule_message():
    with pytest.raises(SearchConstraintError) as exc:
        search_voicings(CMAJ7, root=0, constraints={"spread": {"lte": 12}})
    assert any("never invents a default register" in e for e in exc.value.errors)


def test_all_errors_collected_at_once():
    with pytest.raises(SearchConstraintError) as exc:
        search_voicings(
            [0, 4, 99], root=0,
            constraints={"sprd": 1, "no_interval_over_bass": [0], "max_voice_leading": 3},
        )
    assert len(exc.value.errors) == 5  # bad pc, unknown field, bad interval, no register, vl-without-ref


def test_center_is_float_range_only():
    ok = search_voicings(
        CMAJ7, root=0, constraints={"register": [48, 71], "center": {"lte": 62.0}}
    )
    assert all(m.center <= 62.0 for m in ok.matches)
    with pytest.raises(SearchConstraintError):
        search_voicings(CMAJ7, root=0, constraints={"register": [48, 71], "center": 62.0})


def test_unknown_voicing_type_label_rejected():
    with pytest.raises(SearchConstraintError) as exc:
        search_voicings(
            CMAJ7, root=0, constraints={"register": [48, 71], "voicing_type": "drop9"}
        )
    assert any("not one of" in e for e in exc.value.errors)


# --- MCP parity -----------------------------------------------------------------

def test_mcp_tool_matches_engine():
    from mts.mcp import tools

    kwargs = dict(
        pcs=[0, 4, 7, 11, 2], root=0,
        constraints={"register": [48, 84], "spread": {"lte": 19}},
        from_voicing=[60, 64, 67, 71], limit=5,
    )
    engine = search_voicings(
        kwargs["pcs"], root=0, constraints=kwargs["constraints"],
        from_voicing=kwargs["from_voicing"], limit=5,
    ).to_dict()
    assert tools.search_voicings(**kwargs) == engine
    assert tools.search_voicings in tools.TOOLS
