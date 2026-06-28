"""Meter estimation (gap 11): infer the time signature from note content.

`infer_key` for meter — bar-period autocorrelation × metric-profile correlation,
ranked candidates + margin, and a declared-vs-estimated disagreement signal that
never overrides the file's meter.
"""

from __future__ import annotations

import json

import pytest

from mts.analysis import infer_meter
from mts.core.pitch import Pitch
from mts.io.loaders import load_meter_profiles
from mts.temporal import Event, Sequence


def _seq(accented, *, declared=(4, 4), bpm=120.0):
    """accented: list of (onset_beats, weight). Weight → velocity (the accent)."""
    events = [
        Event(float(t), 0.5, Pitch.from_midi(60, velocity=int(w * 25)))
        for t, w in accented
    ]
    return Sequence.from_events(events, bpm=bpm, time_signature=declared)


def _pattern(per_bar, bar_beats, bars=8):
    """Repeat a per-bar accent pattern [(offset, weight), ...] over `bars` bars."""
    return [(b * bar_beats + o, w) for b in range(bars) for o, w in per_bar]


# bar patterns with a strong downbeat (the accent that reveals the meter)
P_44 = _pattern([(0, 4), (1, 1), (2, 2), (3, 1)], 4)
P_34 = _pattern([(0, 3), (1, 1), (2, 1)], 3)
P_68 = _pattern([(0, 3), (0.5, 1), (1.0, 1), (1.5, 2), (2.0, 1), (2.5, 1)], 3)


# --- recovery -----------------------------------------------------------------------------


def test_recovers_common_time():
    result = infer_meter(_seq(P_44))
    assert (result.best.numerator, result.best.denominator) == (4, 4)
    assert result.margin > 0.0
    assert result.agrees_with_declared is True


def test_distinguishes_three_four_from_six_eight():
    # Both fold to a 3-beat bar; only the within-bar accent profile separates them.
    three = infer_meter(_seq(P_34, declared=(3, 4)))
    six = infer_meter(_seq(P_68, declared=(6, 8)))
    assert (three.best.numerator, three.best.denominator) == (3, 4)
    assert (six.best.numerator, six.best.denominator) == (6, 8)
    # each ranks its true meter above the other 3-beat candidate
    rank3 = {(c.numerator, c.denominator): i for i, c in enumerate(three.candidates)}
    assert rank3[(3, 4)] < rank3[(6, 8)]
    rank6 = {(c.numerator, c.denominator): i for i, c in enumerate(six.candidates)}
    assert rank6[(6, 8)] < rank6[(3, 4)]


# --- the disagreement signal (never overrides) --------------------------------------------


def test_disagreement_is_flagged_not_overridden():
    seq = _seq(P_34, declared=(4, 4))  # 3/4 content tagged 4/4
    result = infer_meter(seq)
    assert (result.best.numerator, result.best.denominator) == (3, 4)
    assert (result.declared_numerator, result.declared_denominator) == (4, 4)
    assert result.agrees_with_declared is False
    # the engine evidences against the file's claim — it does NOT mutate the meter
    assert seq.meter.changes[0].signature.numerator == 4


def test_agreement_when_content_matches_declared():
    result = infer_meter(_seq(P_44, declared=(4, 4)))
    assert result.agrees_with_declared is True


# --- evidence, honesty, determinism -------------------------------------------------------


def test_candidates_carry_both_subscores():
    result = infer_meter(_seq(P_44))
    best = result.best
    # score = period_score × max(profile_score, 0)
    assert best.score == pytest.approx(best.period_score * max(best.profile_score, 0.0), abs=1e-6)
    assert all(-1.0 <= c.profile_score <= 1.0 for c in result.candidates)


def test_result_shape_and_version():
    result = infer_meter(_seq(P_44))
    assert result.profile_version == load_meter_profiles().version == "meter-grid.1"
    assert result.margin == pytest.approx(result.candidates[0].score - result.candidates[1].score)
    json.dumps(result.to_dict())


def test_deterministic():
    a = infer_meter(_seq(P_34, declared=(4, 4))).to_dict()
    b = infer_meter(_seq(P_34, declared=(4, 4))).to_dict()
    assert a == b


# --- phase search / downbeat offset (anacrusis estimation) --------------------------------


def test_phase_off_reports_no_offset():
    # The default phase-0 path makes no phase claim — the field is None and the
    # numeric ranking is otherwise unchanged.
    result = infer_meter(_seq(P_44))
    assert result.downbeat_offset_beats is None


def test_phase_search_recovers_zero_offset_when_aligned():
    # Content whose downbeat already sits at beat 0: offset is 0.0, not None.
    result = infer_meter(_seq(P_44), phase_search=True)
    assert (result.best.numerator, result.best.denominator) == (4, 4)
    assert result.downbeat_offset_beats == pytest.approx(0.0)


@pytest.mark.parametrize("shift", [1.0, 2.0, 3.0])
def test_phase_search_recovers_anacrusis_offset(shift):
    # Displace a 4/4 accent pattern by `shift` beats: the downbeat is no longer at
    # beat 0, and phase search reports the true displacement as the offset.
    shifted = [(t + shift, w) for t, w in P_44]
    result = infer_meter(_seq(shifted), phase_search=True)
    assert (result.best.numerator, result.best.denominator) == (4, 4)
    assert result.downbeat_offset_beats == pytest.approx(shift)


def test_phase_search_offset_is_deterministic():
    shifted = [(t + 1.0, w) for t, w in P_44]
    a = infer_meter(_seq(shifted), phase_search=True).to_dict()
    b = infer_meter(_seq(shifted), phase_search=True).to_dict()
    assert a == b
    assert a["downbeat_offset_beats"] == pytest.approx(1.0)


def test_too_few_onsets_raises():
    with pytest.raises(ValueError, match="at least"):
        infer_meter(_seq([(0, 1), (1, 1)]))


def test_no_metric_information_raises():
    # All onsets stacked at one position → a flat (single-spike) salience signal
    # with no metric structure to fit. Evidence, don't guess.
    seq = Sequence.from_events([Event(0.0, 0.5, Pitch.from_midi(60)) for _ in range(8)])
    with pytest.raises(ValueError, match="no metric information"):
        infer_meter(seq)
