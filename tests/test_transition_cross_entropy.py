"""Held-out cross-entropy of a transition distribution (gap 14, the boundary metric).

Oracle: a matrix trained on C-major V->I progressions, scored on held-out material.
Covers the metric itself, the smoothing consequence (Laplace stays finite where raw
goes infinite on an unseen in-vocab transition — the reason Laplace is the default),
out-of-vocabulary counting, and determinism.
"""

import math

import pytest

from mts.rules import build_transition_matrix

CMAJ = (0, "major")
TRAIN = [
    ([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], CMAJ),  # degrees 1 4 5 1
    ([(0, "maj"), (2, "min"), (7, "maj"), (0, "maj")], CMAJ),  # 1 2 5 1
    ([(0, "maj"), (9, "min"), (7, "maj"), (0, "maj")], CMAJ),  # 1 6 5 1
]
HELD_SAME = [([(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], CMAJ)]  # 1 4 5 1, all seen


def test_finite_fit_on_same_idiom():
    m = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")
    r = m.cross_entropy(HELD_SAME)
    assert r.has_zero_probability is False and r.oov_transitions == 0
    assert r.scored_transitions == 3 and r.n_pieces == 1
    assert r.cross_entropy_bits is not None and r.perplexity is not None
    assert r.perplexity == pytest.approx(2.0 ** r.cross_entropy_bits)
    assert r.perplexity >= 1.0


def test_laplace_stays_finite_where_raw_goes_infinite():
    # held-out has degree transition 1->5, which never occurs in TRAIN (1 goes to
    # 4/2/6 there). Under raw that transition has probability 0 -> infinite
    # surprise; under Laplace it keeps a small floor -> finite. This is the whole
    # reason Laplace is the default for a scoreable distribution.
    held_unseen = [([(0, "maj"), (7, "maj"), (0, "maj")], CMAJ)]  # degrees 1 5 1
    raw = build_transition_matrix(TRAIN, state="degree", smoothing="none")
    lap = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")

    r_raw = raw.cross_entropy(held_unseen)
    assert r_raw.has_zero_probability is True
    assert r_raw.cross_entropy_bits is None and r_raw.perplexity is None

    r_lap = lap.cross_entropy(held_unseen)
    assert r_lap.has_zero_probability is False
    assert r_lap.cross_entropy_bits is not None and math.isfinite(r_lap.perplexity)


def test_out_of_vocabulary_states_are_counted_not_scored():
    # degree 3 (iii = Em in C) never appears in TRAIN's vocabulary {1,2,4,5,6}.
    held_oov = [([(0, "maj"), (4, "min"), (0, "maj")], CMAJ)]  # degrees 1 3 1
    m = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")
    r = m.cross_entropy(held_oov)
    assert r.oov_transitions == 2 and r.scored_transitions == 0
    assert r.cross_entropy_bits is None  # nothing in-vocabulary to score


def test_better_model_has_lower_perplexity():
    # a model trained on the same idiom predicts held-out V->I better (lower
    # perplexity) than a flat/uniform-ish model trained on a contradictory corpus.
    contrary = [([(0, "maj"), (5, "maj"), (2, "min"), (0, "maj")], CMAJ)]  # 1 4 2 1, no V->I
    focused = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")
    other = build_transition_matrix(TRAIN + contrary * 3, state="degree", smoothing="laplace")
    held = [([(0, "maj"), (9, "min"), (7, "maj"), (0, "maj")], CMAJ)]  # 1 6 5 1
    assert focused.cross_entropy(held).perplexity <= other.cross_entropy(held).perplexity


def test_deterministic():
    m = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")
    assert m.cross_entropy(HELD_SAME).to_dict() == m.cross_entropy(HELD_SAME).to_dict()


def test_mcp_transition_cross_entropy_matches_engine():
    from mts.mcp import tools

    m = build_transition_matrix(TRAIN, state="degree", smoothing="laplace")
    engine = m.cross_entropy(HELD_SAME).to_dict()
    mcp_held = [[[[r, q] for r, q in chords], [k[0], k[1]]] for chords, k in HELD_SAME]
    tool = tools.transition_cross_entropy(m.to_dict(), mcp_held)
    assert tool == engine
