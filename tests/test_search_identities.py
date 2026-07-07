"""Tests for constraint search over the identity universe (search_identities).

Oracles are exact and independently justified: the set-class cardinality
distribution is the standard one (Forte counts), the whole-tone scale is the
unique period-2 set class, subset enumerations are hand-checkable, and the
diatonic scale's membership in a containment query is a known fact. Exhaustive
counts that aren't hand-derivable are pinned as regression stability checks.
"""

import pytest

from mts.core.bitmask import mask_from_pcs, pcs_from_mask
from mts.core.setclass import prime_form_mask
from mts.search import search_identities
from mts.search.identities import SearchConstraintError


def _prime_pcs(pcs):
    return tuple(pcs_from_mask(prime_form_mask(mask_from_pcs(pcs))))


# --- universe & cardinality --------------------------------------------------

def test_cardinality_distribution_matches_forte_counts():
    # The canonical number of set classes per cardinality (Forte / Rahn).
    expected = {1: 1, 2: 6, 3: 12, 4: 29, 5: 38, 6: 50, 7: 38, 8: 29, 9: 12, 10: 6, 11: 1, 12: 1}
    for card, n in expected.items():
        result = search_identities({"cardinality": card})
        assert result.count == n, f"cardinality {card}: got {result.count}, want {n}"
        assert result.universe == "set_classes"
        assert all(m.cardinality == card for m in result.matches)


def test_total_set_classes_is_223():
    total = sum(search_identities({"cardinality": c}).count for c in range(1, 13))
    assert total == 223  # 224 including the empty set, which mask 0 (excluded) would be


def test_expand_transpositions_counts_rooted_images():
    # The full chromatic (cardinality 12) has exactly one rooted image.
    assert search_identities({"cardinality": 12}, expand_transpositions=True).count == 1
    # A set class with no transpositional symmetry (period 12) has 12 rooted
    # images per inversion; assert the universe label flips and count grows.
    sc = search_identities({"cardinality": 3})
    allm = search_identities({"cardinality": 3}, expand_transpositions=True)
    assert allm.universe == "all_masks"
    assert allm.count > sc.count


# --- scalar predicates -------------------------------------------------------

def test_rotational_period_two_is_only_whole_tone():
    result = search_identities({"rotational_period": 2})
    assert result.count == 1
    assert result.matches[0].pcs == (0, 2, 4, 6, 8, 10)


def test_interval_vector_op_conditions():
    # ic6 (tritones): the diminished-7th prime form [0,3,6,9] has ic6 == 2.
    result = search_identities({"cardinality": 4, "ic6": {"gte": 2}})
    assert result.count >= 1
    assert all(m.interval_vector[5] >= 2 for m in result.matches)
    assert _prime_pcs([0, 3, 6, 9]) in {m.pcs for m in result.matches}


def test_in_condition_on_cardinality():
    result = search_identities({"cardinality": {"in": [3, 12]}})
    cards = {m.cardinality for m in result.matches}
    assert cards == {3, 12}
    assert result.count == 12 + 1


def test_no_consecutive_semitones_is_step_pattern_not_ic1():
    # The melodic-minor prime form contains semitones (ic1 > 0) but has no two
    # semitone steps in a row — so it passes no_consecutive_semitones.
    mel_minor = _prime_pcs([0, 2, 3, 5, 7, 9, 11])
    hits = {m.pcs for m in search_identities(
        {"cardinality": 7, "no_consecutive_semitones": True}).matches}
    assert mel_minor in hits
    # The chromatic-heptachord [0,1,2,3,4,5,6] has runs and must be excluded.
    assert _prime_pcs([0, 1, 2, 3, 4, 5, 6]) not in hits


def test_is_achiral_matches_chirality():
    from mts.core.setclass import chirality_sign

    result = search_identities({"is_achiral": True})
    assert all(chirality_sign(m.mask) == 0 for m in result.matches)
    # The major triad's set class is chiral, so it must be absent.
    assert _prime_pcs([0, 4, 7]) not in {m.pcs for m in result.matches}


# --- structural containment --------------------------------------------------

def test_contains_is_set_class_containment_and_reports_roots():
    # 7-note scales holding a major-triad set class, with no chromatic run — the
    # marquee query. The diatonic scale must be among them.
    result = search_identities(
        {"cardinality": 7, "contains": [0, 4, 7], "no_consecutive_semitones": True}
    )
    diatonic = _prime_pcs([0, 2, 4, 5, 7, 9, 11])
    by_pcs = {m.pcs: m for m in result.matches}
    assert diatonic in by_pcs
    # Set-class containment folds inversions: the diatonic holds the triad's set
    # class at six roots (three major + three minor placements).
    assert len(by_pcs[diatonic].contains_roots) == 6
    assert result.count == 4  # exact enumeration — regression pin


def test_contains_is_rooted_in_all_masks_universe():
    # Granularity follows universe: in all_masks a shape is rooted, so [0,4,7]
    # means the major triad specifically — its 12 transpositions, no minor.
    result = search_identities(
        {"cardinality": 3, "contains": [0, 4, 7]}, expand_transpositions=True
    )
    assert result.count == 12
    # In the set-class universe the same query folds to one class (maj = min).
    assert search_identities({"cardinality": 3, "contains": [0, 4, 7]}).count == 1


def test_contains_roots_absent_without_contains_constraint():
    result = search_identities({"cardinality": 3})
    assert all(m.contains_roots is None for m in result.matches)


def test_contained_in_enumerates_subsets():
    # 3-note set classes that fit inside the chromatic tetrachord {0,1,2,3}.
    result = search_identities({"cardinality": 3, "contained_in": [0, 1, 2, 3]})
    assert {m.pcs for m in result.matches} == {(0, 1, 2), (0, 1, 3)}


def test_contained_in_rooted_is_literal_not_transposed():
    # R1 (Wend brief-2): in all_masks the enumerated identity is a rooted literal,
    # so contained_in must be a literal subset test — every reported match must
    # ACTUALLY be a subset of the outer set, not merely transposable into it.
    c_major = [0, 2, 4, 5, 7, 9, 11]
    c_set = set(c_major)
    result = search_identities(
        {"cardinality": 3, "contained_in": c_major}, expand_transpositions=True
    )
    # C(7,3) = 35 literal 3-note subsets; the pre-fix bug returned 180.
    assert result.count == 35
    # No match may contradict its own echo (the blind-agent contract).
    assert all(set(m.pcs) <= c_set for m in result.matches)


def test_contained_in_rooted_counts_are_binomial():
    from math import comb

    c_major = [0, 2, 4, 5, 7, 9, 11]
    for k in range(1, 8):
        got = search_identities(
            {"cardinality": k, "contained_in": c_major}, expand_transpositions=True
        ).count
        assert got == comb(7, k), f"cardinality {k}: {got} != C(7,{k})"


# --- limit / truncation ------------------------------------------------------

def test_limit_truncates_but_count_stays_total():
    result = search_identities({"cardinality": 4}, limit=5)
    assert result.count == 29
    assert len(result.matches) == 5
    assert result.truncated is True


def test_no_limit_reports_all():
    result = search_identities({"cardinality": 4})
    assert len(result.matches) == result.count == 29
    assert result.truncated is False


# --- validation (strict + total) ---------------------------------------------

def test_unknown_field_is_reported():
    with pytest.raises(SearchConstraintError) as exc:
        search_identities({"cardnality": 7})
    assert any("unknown field" in e for e in exc.value.errors)


def test_all_errors_collected_at_once():
    with pytest.raises(SearchConstraintError) as exc:
        search_identities({"cardnality": 7, "ic1": {"bogus": 1}, "contains": [13]})
    assert len(exc.value.errors) == 3


def test_empty_constraints_rejected():
    with pytest.raises(SearchConstraintError):
        search_identities({})


def test_gte_on_bool_field_rejected():
    with pytest.raises(SearchConstraintError) as exc:
        search_identities({"is_achiral": {"gte": 1}})
    assert any("not numeric" in e for e in exc.value.errors)


def test_bad_limit_rejected():
    with pytest.raises(SearchConstraintError):
        search_identities({"cardinality": 3}, limit=-1)


# --- result serialization ----------------------------------------------------

def test_to_dict_round_trips_and_echoes_constraints():
    result = search_identities({"cardinality": 4, "contains": [0, 4, 7]}, limit=2)
    data = result.to_dict()
    assert data["universe"] == "set_classes"
    assert data["count"] >= 2
    assert data["constraints"]["cardinality"] == 4
    assert data["constraints"]["contains"] == [0, 4, 7]
    assert len(data["matches"]) == 2
    assert "contains_roots" in data["matches"][0]


def test_mcp_tool_matches_engine():
    from mts.mcp import tools

    engine = search_identities({"cardinality": 7, "contains": [0, 4, 7]}).to_dict()
    tool = tools.search_identities({"cardinality": 7, "contains": [0, 4, 7]})
    assert tool == engine
    assert tools.search_identities in tools.TOOLS
