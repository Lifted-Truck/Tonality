"""Phase 5: the chord-network (voice-leading parsimony graph) descriptor."""

from __future__ import annotations

import json

import pytest

from mts.io.loaders import load_chord_qualities
from mts.representation import chord_network_descriptor

_Q = load_chord_qualities()


def _vocab(*pairs):
    return [(root, _Q[q]) for root, q in pairs]


# --- nodes + symmetry (the hub signal) ----------------------------------------------------


def test_nodes_carry_pcs_and_symmetry_order():
    net = chord_network_descriptor(_vocab((0, "maj"), (0, "aug")))
    assert net.spec_level == "identity_only"
    c, c_aug = net.nodes
    assert c.pcs == [0, 4, 7] and c.symmetry_order == 12
    # the augmented triad is a symmetric hub (maps to itself every 4 semitones)
    assert c_aug.pcs == [0, 4, 8] and c_aug.symmetry_order == 4


# --- edges == the voice-leading relation --------------------------------------------------


def test_parsimonious_edges_match_voice_leading_distance():
    from mts.analysis import voice_leading

    net = chord_network_descriptor(
        _vocab((0, "maj"), (0, "aug"), (0, "min"), (4, "min"), (9, "min")),
        max_distance=1,
    )
    # at threshold 1, C major connects to C+, Cm, Em (all distance 1) but NOT
    # Am (distance 2) — exactly the voice-leading neighbourhood
    by_pcs = {n.index: tuple(n.pcs) for n in net.nodes}
    c_index = next(i for i, p in by_pcs.items() if p == (0, 4, 7))
    neighbours = {
        (e.target if e.source == c_index else e.source)
        for e in net.edges
        if c_index in (e.source, e.target)
    }
    neighbour_pcs = {by_pcs[i] for i in neighbours}
    assert (0, 4, 8) in neighbour_pcs   # C+
    assert (0, 3, 7) in neighbour_pcs   # Cm
    assert (4, 7, 11) in neighbour_pcs  # Em
    assert (9, 0, 4) not in neighbour_pcs  # Am is distance 2 — excluded
    # every edge's distance really is the VL distance
    for e in net.edges:
        d = voice_leading(net.nodes[e.source].pcs, net.nodes[e.target].pcs).distance
        assert e.distance == d <= 1


def test_threshold_widens_the_graph():
    vocab = _vocab((0, "maj"), (9, "min"), (3, "maj"))  # C, Am, Eb
    sparse = chord_network_descriptor(vocab, max_distance=1)
    dense = chord_network_descriptor(vocab, max_distance=2)
    assert len(dense.edges) >= len(sparse.edges)
    # C–Am is distance 2: absent at 1, present at 2
    assert len(sparse.edges) == 0
    assert any(e.distance == 2 for e in dense.edges)


def test_edges_carry_common_tones_and_root_interval():
    net = chord_network_descriptor(_vocab((0, "maj"), (4, "min")), max_distance=1)
    [edge] = net.edges  # C major – E minor share E and G
    assert edge.common_tones == 2
    assert edge.root_interval == 4  # C -> E


# --- the diagram as acceptance: augmented triads are hubs ---------------------------------


def test_augmented_triads_are_high_degree_hubs():
    # the diagram's structural claim: aug triads connect many consonant triads.
    vocab = _vocab(
        (0, "aug"),  # C+ = {C, E, G#}
        *[(r, "maj") for r in range(12)],
        *[(r, "min") for r in range(12)],
    )
    net = chord_network_descriptor(vocab, max_distance=1)
    degree: dict[int, int] = {}
    for e in net.edges:
        degree[e.source] = degree.get(e.source, 0) + 1
        degree[e.target] = degree.get(e.target, 0) + 1
    aug_index = 0  # C+ is first
    aug_degree = degree.get(aug_index, 0)
    # the augmented triad outranks the median consonant-triad degree
    triad_degrees = sorted(degree.get(i, 0) for i in range(1, len(net.nodes)))
    median = triad_degrees[len(triad_degrees) // 2]
    assert aug_degree > median


# --- validation + shape -------------------------------------------------------------------


def test_validation():
    with pytest.raises(ValueError, match="at least one chord"):
        chord_network_descriptor([])
    with pytest.raises(ValueError, match="max_distance must be"):
        chord_network_descriptor(_vocab((0, "maj")), max_distance=0)


def test_to_dict_is_json_ready():
    payload = json.loads(json.dumps(
        chord_network_descriptor(_vocab((0, "maj"), (0, "aug")), max_distance=1).to_dict()
    ))
    assert payload["max_distance"] == 1
    assert payload["nodes"][1]["symmetry_order"] == 4
    assert payload["edges"][0]["distance"] == 1
