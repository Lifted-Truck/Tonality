"""Phase 3.5: minimal voice-leading distance (identity level)."""

import json
from itertools import combinations, permutations, product

import pytest

from mts.analysis import POLICY_DOUBLING_V1, voice_leading
from mts.analysis.voice_leading import _circular_distance


# --- known values ---------------------------------------------------------------

def test_classic_progressions():
    assert voice_leading([0, 4, 7], [5, 9, 0]).distance == 3   # C -> F
    assert voice_leading([0, 4, 7], [7, 11, 2]).distance == 3  # C -> G
    assert voice_leading([0, 4, 7], [9, 0, 4]).distance == 2   # C -> Am (relative)
    assert voice_leading([0, 4, 7], [0, 3, 7]).distance == 1   # C -> Cm (parallel)


def test_identity_is_zero_with_identity_mapping():
    result = voice_leading([0, 4, 7], [0, 4, 7])
    assert result.distance == 0
    assert all(a == b for a, b in result.mapping)


def test_triad_to_seventh_doubles_a_tone():
    result = voice_leading([0, 4, 7], [0, 4, 7, 10])
    assert result.distance == 2  # C doubles; one voice moves C -> Bb
    sources = [a for a, _ in result.mapping]
    targets = sorted(b for _, b in result.mapping)
    assert sources.count(0) == 2
    assert targets == [0, 4, 7, 10]


def test_maximally_distant_transposition():
    # Tritone transposition of a triad: every voice moves, total is large.
    result = voice_leading([0, 4, 7], [6, 10, 1])
    assert result.distance == 6  # each voice moves by tritone-or-better paths


def test_dim7_is_close_to_everything_dominant():
    # Co7 shares three tones with each of four dominant sevenths (resolution lore).
    assert voice_leading([0, 3, 6, 9], [11, 2, 5, 8]).distance <= 4


# --- result contract ---------------------------------------------------------------

def test_result_shape_and_serialization():
    result = voice_leading([0, 4, 7], [5, 9, 0])
    assert result.policy == POLICY_DOUBLING_V1
    assert result.source_pcs == [0, 4, 7]
    assert result.target_pcs == [0, 5, 9]
    # Every pc of both sets participates (doubling policy).
    assert {a for a, _ in result.mapping} == set(result.source_pcs)
    assert {b for _, b in result.mapping} == set(result.target_pcs)
    assert result.distance == sum(_circular_distance(a, b) for a, b in result.mapping)
    json.dumps(result.to_dict())


def test_unknown_policy_and_empty_inputs_raise():
    with pytest.raises(ValueError, match="Unknown voice-leading policy"):
        voice_leading([0], [7], policy="omission.99")
    with pytest.raises(ValueError, match="at least one pitch class"):
        voice_leading([], [0, 4, 7])


def test_symmetry():
    cases = [([0, 4, 7], [2, 5, 9, 11]), ([0, 1, 2], [6, 7]), ([0, 3, 6, 9], [0, 4, 7])]
    for a, b in cases:
        assert voice_leading(a, b).distance == voice_leading(b, a).distance


# --- exactness: cross-validate the non-crossing shortcut against brute force --------

def _brute_force_bijection(source, target):
    return min(
        sum(_circular_distance(a, b) for a, b in zip(source, perm))
        for perm in permutations(target)
    )


def _brute_force_surjection(larger, smaller):
    best = None
    for assignment in product(range(len(smaller)), repeat=len(larger)):
        if set(assignment) != set(range(len(smaller))):
            continue  # not surjective: some smaller pc unused
        cost = sum(_circular_distance(pc, smaller[i]) for pc, i in zip(larger, assignment))
        best = cost if best is None or cost < best else best
    return best


def test_equal_cardinality_matches_brute_force_exhaustively():
    """All pairs of trichords: rotation method == brute force over bijections."""
    trichords = list(combinations(range(12), 3))
    for a in trichords[::7]:  # stride keeps it fast; still ~32 x 220 pairs
        for b in trichords:
            assert voice_leading(a, b).distance == _brute_force_bijection(list(a), list(b))


def test_equal_cardinality_matches_brute_force_larger_sets():
    cases = [
        ((0, 2, 4, 5, 7, 9, 11), (0, 1, 3, 5, 6, 8, 10)),  # major vs its inversion
        ((0, 2, 4, 6, 8, 10), (1, 3, 5, 7, 9, 11)),        # the two whole-tone sets
        ((0, 1, 4, 6), (0, 1, 3, 7)),                      # Z-pair tetrachords
        ((0, 4, 7, 10), (1, 5, 8, 11)),
    ]
    for a, b in cases:
        assert voice_leading(a, b).distance == _brute_force_bijection(list(a), list(b))


def test_unequal_cardinality_matches_brute_force():
    cases = [
        ((0, 4, 7), (0, 4, 7, 10)),
        ((0, 4, 7), (2, 5, 7, 11)),
        ((0, 3, 6, 9), (0, 4, 7)),
        ((0,), (0, 4, 7)),
        ((0, 2, 4, 5, 7, 9, 11), (0, 4, 7)),  # scale onto triad
        ((1, 5, 8), (0, 2, 4, 6, 8, 10)),
    ]
    for a, b in cases:
        larger, smaller = (list(a), list(b)) if len(a) >= len(b) else (list(b), list(a))
        expected = _brute_force_surjection(larger, smaller)
        assert voice_leading(a, b).distance == expected
        assert voice_leading(b, a).distance == expected
