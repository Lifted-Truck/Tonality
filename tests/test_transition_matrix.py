"""Degree-transition distributions (Phase 4.5, gap 14 slice 1).

Oracle: hand-built C-major progressions where the dominant always resolves to
the tonic. Covers the aggregation, the two smoothing modes (raw hard-zeros vs
Laplace no-zeros, identical counts), row-normalization, seeded sampling/walk
determinism, JSON round-trip, provenance, and the end-to-end feed from
segmentation.
"""

import pytest

from mts.mcp.tools import _canonical_sequence
from mts.rules import TransitionMatrix, build_transition_matrix
from mts.temporal import segment_to_chords

CMAJ = (0, "major")
# I -> {IV, ii, vi} -> V -> I : the dominant (degree 5) always resolves to I.
CORPUS = [
    ([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], CMAJ),  # 1 4 5 1
    ([(0, "maj"), (2, "min"), (7, "maj"), (0, "maj")], CMAJ),  # 1 2 5 1
    ([(0, "maj"), (9, "min"), (7, "maj"), (0, "maj")], CMAJ),  # 1 6 5 1
    ([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], CMAJ),
]


# --- aggregation + the two smoothing modes ------------------------------------

def test_captures_dominant_to_tonic():
    m = build_transition_matrix(CORPUS, state="degree")
    assert m.counts["5"] == {"1": 4}                 # every V went to I
    assert m.row("5")["1"] == max(m.row("5").values())


def test_raw_empirical_has_hard_zeros():
    m = build_transition_matrix(CORPUS, state="degree", smoothing="none")
    assert m.alpha == 0.0
    assert m.row("5") == {"1": 1.0, "2": 0.0, "4": 0.0, "5": 0.0, "6": 0.0}


def test_laplace_has_no_hard_zeros():
    m = build_transition_matrix(CORPUS, state="degree", smoothing="laplace")
    assert all(p > 0.0 for p in m.row("5").values())  # every transition samplable
    assert m.row("5")["1"] > m.row("5")["2"]          # but I still dominates


def test_counts_identical_across_smoothing():
    raw = build_transition_matrix(CORPUS, state="degree", smoothing="none")
    lap = build_transition_matrix(CORPUS, state="degree", smoothing="laplace")
    assert raw.counts == lap.counts                   # smoothing never touches counts


def test_rows_sum_to_one():
    for smoothing in ("laplace", "none"):
        m = build_transition_matrix(CORPUS, state="degree", smoothing=smoothing)
        for src in m.states:
            row = m.row(src)
            if row:  # a never-source state under 'none' has an empty row
                assert sum(row.values()) == pytest.approx(1.0)


# --- storage + determinism ----------------------------------------------------

def test_json_round_trip():
    m = build_transition_matrix(CORPUS, state="degree", source="test-corpus")
    assert TransitionMatrix.from_dict(m.to_dict()).to_dict() == m.to_dict()


def test_deterministic():
    assert (
        build_transition_matrix(CORPUS, state="degree").to_dict()
        == build_transition_matrix(CORPUS, state="degree").to_dict()
    )


def test_provenance_and_prior_cited():
    m = build_transition_matrix(CORPUS, state="degree", source="mycorpus")
    assert m.source == "mycorpus"
    assert m.prior_version == "distribution.1"
    assert m.n_transitions == 12 and m.n_pieces == 4


# --- seeded sampling / walk ---------------------------------------------------

def test_seeded_sample_is_deterministic():
    m = build_transition_matrix(CORPUS, state="degree")
    assert m.sample("5", seed=7) == m.sample("5", seed=7)


def test_walk_is_deterministic_and_right_length():
    m = build_transition_matrix(CORPUS, state="degree")
    w = m.walk("1", 8, seed=42)
    assert len(w) == 8 and w[0] == "1"
    assert w == m.walk("1", 8, seed=42)


def test_raw_walk_follows_hard_zeros():
    # under raw empirical, from "5" the ONLY option is "1" — a walk from 5 must
    # go 5 -> 1 every step it's at 5.
    m = build_transition_matrix(CORPUS, state="degree", smoothing="none")
    assert m.sample("5", seed=0) == "1"


# --- alternate state keyings --------------------------------------------------

def test_state_role_keying():
    m = build_transition_matrix(CORPUS, state="role")
    assert set(m.states) == {"tonic", "predominant", "dominant"}
    assert m.row("dominant")["tonic"] == max(m.row("dominant").values())


# --- error, not guess ---------------------------------------------------------

def test_unknown_state_raises():
    with pytest.raises(ValueError, match="state must be one of"):
        build_transition_matrix(CORPUS, state="bogus")


def test_unknown_smoothing_raises():
    with pytest.raises(ValueError, match="smoothing must be"):
        build_transition_matrix(CORPUS, smoothing="bogus")


def test_negative_alpha_raises():
    with pytest.raises(ValueError, match="alpha must be"):
        build_transition_matrix(CORPUS, alpha=-1.0)


def test_unknown_quality_raises():
    with pytest.raises(ValueError, match="Unknown chord quality"):
        build_transition_matrix([([(0, "maj"), (7, "bogus")], CMAJ)])


def test_sample_unknown_state_raises():
    m = build_transition_matrix(CORPUS, state="degree")
    with pytest.raises(ValueError, match="unknown from-state"):
        m.sample("nope", seed=0)


def test_walk_length_validation():
    m = build_transition_matrix(CORPUS, state="degree")
    with pytest.raises(ValueError, match="length must be"):
        m.walk("1", 0, seed=0)


# --- end to end: segmentation feeds the distribution --------------------------

def test_segmented_corpus_builds_matrix():
    def barchord(bar, pcs):
        return [[bar * 4.0, 4.0, 60 + p] for p in pcs]

    corpus = []
    for prog in ([[0, 4, 7], [7, 11, 14], [0, 4, 7]], [[0, 4, 7], [5, 9, 12], [0, 4, 7]]):
        events = [ev for bar, pcs in enumerate(prog) for ev in barchord(bar, pcs)]
        seg = segment_to_chords(_canonical_sequence(events))
        corpus.append((seg.chords, seg.key))
    m = build_transition_matrix(corpus, state="degree")
    assert m.n_pieces == 2 and m.n_transitions > 0   # built from raw MIDI, no hand annotation


def test_mcp_transition_matrix_matches_engine():
    from mts.mcp import tools

    engine = build_transition_matrix(CORPUS, state="degree", source="c").to_dict()
    mcp_corpus = [
        [[[root, quality] for root, quality in chords], [key[0], key[1]]]
        for chords, key in CORPUS
    ]
    assert tools.transition_matrix(mcp_corpus, state="degree", source="c") == engine
