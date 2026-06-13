"""Phase 5 slice 3: bracelet (pc clock) + Tonnetz descriptors."""

from __future__ import annotations

import json

import pytest

from mts.io.loaders import load_scales
from mts.representation import bracelet_descriptor, tonnetz_descriptor


# --- bracelet -----------------------------------------------------------------------------


def test_bracelet_ring_positions_and_active_set():
    result = bracelet_descriptor([0, 4, 7])
    assert result.spec_level == "identity_only"
    assert result.active_pcs == [0, 4, 7]
    assert result.cardinality == 3
    assert len(result.positions) == 12
    active = [p.pc for p in result.positions if p.is_active]
    assert active == [0, 4, 7]
    assert all(p.in_scale is None for p in result.positions)  # no backdrop


def test_bracelet_interval_vector_and_rotational_order():
    # augmented triad: interval vector <0,0,3,0,0,0>, rotational order 4
    aug = bracelet_descriptor([0, 4, 8])
    assert aug.interval_vector == [0, 0, 0, 3, 0, 0]
    assert aug.rotational_order == 4  # maps to itself every 4 semitones
    # major triad is asymmetric under rotation
    assert bracelet_descriptor([0, 4, 7]).rotational_order == 12


def test_bracelet_reflection_axes():
    # the major triad is chiral (its reflection is the minor triad) — no axis;
    # the engine says so honestly rather than inventing one
    assert bracelet_descriptor([0, 4, 7]).reflection_axes == []
    # a diminished triad {0,3,6} is symmetric: axes through pc 3 and its tritone
    axes = bracelet_descriptor([0, 3, 6]).reflection_axes
    assert {(a.type, a.center) for a in axes} == {("pitch", 3.0), ("pitch", 9.0)}
    # the whole-tone scale is highly symmetric — many axes
    assert len(bracelet_descriptor([0, 2, 4, 6, 8, 10]).reflection_axes) == 12


def test_bracelet_scale_backdrop():
    result = bracelet_descriptor([0, 4, 7], tonic_pc=0, scale=load_scales()["Ionian"])
    by_pc = {p.pc: p for p in result.positions}
    assert by_pc[0].in_scale and by_pc[0].is_active
    assert by_pc[2].in_scale and not by_pc[2].is_active  # D: in scale, not in chord
    assert by_pc[1].in_scale is False  # C#: out of C major
    assert result.scale_name == "Ionian"


def test_bracelet_validation():
    with pytest.raises(ValueError, match="at least one"):
        bracelet_descriptor([])
    with pytest.raises(ValueError, match="both or neither"):
        bracelet_descriptor([0, 4, 7], tonic_pc=0)


# --- Tonnetz ------------------------------------------------------------------------------


def test_tonnetz_nodes_cover_all_twelve_with_active_flagged():
    result = tonnetz_descriptor([0, 4, 7])
    assert result.spec_level == "identity_only"
    assert len(result.nodes) == 12
    assert {n.pc for n in result.nodes if n.is_active} == {0, 4, 7}
    c_node = next(n for n in result.nodes if n.pc == 0)
    assert c_node.coordinate == (0, 0, 0)  # C at the origin


def test_tonnetz_coordinates_match_chord_analysis():
    # the descriptor shares the lattice with chord analysis — same coords
    from mts.analysis import ChordAnalysisRequest, analyze_chord
    from mts.core.chord import Chord
    from mts.io.loaders import load_chord_qualities

    chord = Chord.from_quality(0, load_chord_qualities()["maj"])
    analysis = analyze_chord(ChordAnalysisRequest(chord=chord))
    desc = tonnetz_descriptor([0, 4, 7])
    desc_coords = {n.pc: n.coordinate for n in desc.nodes}
    for pc, coord in analysis.tonnetz.coordinates.items():
        assert desc_coords[pc] == coord


def test_tonnetz_major_triad_edges_are_one_of_each_axis():
    # C major {0,4,7}: C-G is P5, C-E is M3, E-G is m3 — the triad triangle
    edges = {(e.pc_a, e.pc_b, e.axis) for e in tonnetz_descriptor([0, 4, 7]).edges}
    assert edges == {(0, 7, "P5"), (0, 4, "M3"), (4, 7, "m3")}


def test_tonnetz_edges_use_complement_intervals():
    # a bare perfect fourth {0,5}: interval 5 is the P5 axis (octave complement)
    edges = tonnetz_descriptor([0, 5]).edges
    assert len(edges) == 1
    assert (edges[0].pc_a, edges[0].pc_b, edges[0].axis) == (0, 5, "P5")
    # a tritone {0,6} shares no axis — no edge
    assert tonnetz_descriptor([0, 6]).edges == []


def test_tonnetz_centroid_and_validation():
    result = tonnetz_descriptor([0, 7])  # C + G
    # C=(0,0,0), G=(1,0,0) -> centroid (0.5, 0, 0)
    assert result.centroid == pytest.approx((0.5, 0.0, 0.0))
    with pytest.raises(ValueError, match="at least one"):
        tonnetz_descriptor([])


# --- output shape -------------------------------------------------------------------------


def test_descriptors_are_json_ready():
    bracelet = json.loads(json.dumps(bracelet_descriptor([0, 4, 7]).to_dict()))
    assert bracelet["interval_vector"] == [0, 0, 1, 1, 1, 0]
    tonnetz = json.loads(json.dumps(tonnetz_descriptor([0, 4, 7]).to_dict()))
    assert tonnetz["edges"][0]["axis"] in {"P5", "M3", "m3"}
    assert len(tonnetz["nodes"]) == 12
