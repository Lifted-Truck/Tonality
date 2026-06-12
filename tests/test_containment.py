"""Catalog containment query (gap 8): which catalog identities contain a pc set."""

from __future__ import annotations

import json

import pytest

from mts.analysis import find_containers
from mts.analysis.pcset_math import containing_roots
from mts.core.scale import Scale


def _roots(containers, name):
    return {c.root_pc for c in containers if c.name == name}


# --- the math ------------------------------------------------------------------------


def test_containing_roots_major_triad_in_ionian():
    ionian = Scale.from_degrees("Ionian", [0, 2, 4, 5, 7, 9, 11])
    # C E G fits the major scales of C, F, and G — and no others.
    assert containing_roots(ionian.mask, 0b000010010001) == (0, 5, 7)


def test_containing_roots_is_the_reverse_of_compatibility():
    # The container moves, the query stays absolute: a single pc is contained
    # at exactly one root per scale degree.
    ionian = Scale.from_degrees("Ionian", [0, 2, 4, 5, 7, 9, 11])
    assert len(containing_roots(ionian.mask, 0b1)) == 7


# --- the query -----------------------------------------------------------------------


def test_major_triad_scale_containers():
    result = find_containers([0, 4, 7])
    assert _roots(result.scales, "Ionian") == {0, 5, 7}


def test_major_triad_quality_containers_include_exact_and_supersets():
    result = find_containers([0, 4, 7])
    exact = [q for q in result.qualities if q.is_exact]
    assert ("maj", 0) in {(q.name, q.root_pc) for q in exact}
    assert ("maj7", 0) in {(q.name, q.root_pc) for q in result.qualities}
    # maj7 at root 0 is a proper superset, not an exact match
    maj7_at_0 = next(
        q for q in result.qualities if q.name == "maj7" and q.root_pc == 0
    )
    assert maj7_at_0.is_exact is False
    assert maj7_at_0.cardinality == 4


def test_symmetric_container_reports_every_valid_root():
    # The augmented triad sits inside the whole-tone scale at all six of its
    # transpositions; dim7 contains itself exactly at its four roots.
    result = find_containers([0, 4, 8])
    assert _roots(result.scales, "Whole Tone") == {0, 2, 4, 6, 8, 10}
    dim = find_containers([0, 3, 6, 9])
    dim7 = [q for q in dim.qualities if q.name == "dim7"]
    assert {q.root_pc for q in dim7} == {0, 3, 6, 9}
    assert all(q.is_exact for q in dim7)


def test_exact_scale_match_includes_every_mode_spelling():
    # The C-major collection IS Ionian-at-0 and Dorian-at-2 (etc.) — modal
    # spellings of one mask are distinct catalog answers, all exact.
    result = find_containers([0, 2, 4, 5, 7, 9, 11])
    exact = {(s.name, s.root_pc) for s in result.scales if s.is_exact}
    assert ("Ionian", 0) in exact
    assert ("Dorian", 2) in exact


def test_rooted_masks_are_absolute():
    result = find_containers([0, 4, 7])
    for container in result.scales + result.qualities:
        # every reported container actually contains the query, as claimed
        assert container.mask & result.query_mask == result.query_mask


def test_containers_sorted_tightest_first():
    result = find_containers([0, 4, 7])
    keys = [(s.cardinality, s.name, s.root_pc) for s in result.scales]
    assert keys == sorted(keys)
    assert result.qualities[0].cardinality <= result.qualities[-1].cardinality


def test_aliases_deduplicate_catalog_entries():
    result = find_containers([0, 4, 7])
    pairs = [(s.name, s.root_pc) for s in result.scales]
    assert len(pairs) == len(set(pairs))  # alias keys must not double-report


def test_explicit_catalogs_override_the_bundled_ones():
    pentatonic = Scale.from_degrees("Custom Pent", [0, 2, 4, 7, 9])
    result = find_containers(
        [0, 4, 7], catalog_scales={"Custom Pent": pentatonic}, catalog_qualities={}
    )
    assert {s.name for s in result.scales} == {"Custom Pent"}
    assert result.qualities == []


def test_pcs_normalize_mod_12():
    assert find_containers([12, 16, 19]).query_pcs == [0, 4, 7]


def test_empty_query_raises():
    with pytest.raises(ValueError):
        find_containers([])


def test_result_is_json_ready():
    payload = json.dumps(find_containers([0, 4, 7]).to_dict())
    decoded = json.loads(payload)
    assert decoded["query_mask"] == 0b000010010001
    assert decoded["scales"][0]["name"]
