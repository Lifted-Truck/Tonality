"""Swing-feel estimation: two-way beat divisions → straight/swung/reversed/mixed."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.io.loaders import load_swing_priors
from mts.temporal import Event, Sequence, analyze_swing


def _seq(onsets_durations, *, time_signature=(4, 4)):
    events = [Event(o, d, Pitch.from_midi(60)) for o, d in onsets_durations]
    return Sequence.from_events(events, time_signature=time_signature)


def _eighth_pairs(fraction, beats=4):
    """One two-way division per beat, interior onset at `fraction` of the beat."""
    notes = []
    for b in range(beats):
        notes.append((float(b), fraction))
        notes.append((b + fraction, 1.0 - fraction))
    return notes


# --- the feel classes -------------------------------------------------------------------


def test_triplet_swing_two_to_one():
    result = analyze_swing(_seq(_eighth_pairs(2 / 3)))
    assert result.feel == "swung"
    assert result.mean_fraction == pytest.approx(2 / 3)
    assert result.swing_ratio == pytest.approx(2.0)
    assert result.eligible_divisions == 4
    assert result.prior_version == "swing-feel.1"


def test_straight_eighths():
    result = analyze_swing(_seq(_eighth_pairs(0.5)))
    assert result.feel == "straight"
    assert result.swing_ratio == pytest.approx(1.0)


def test_dotted_shuffle_three_to_one():
    result = analyze_swing(_seq(_eighth_pairs(0.75)))
    assert result.feel == "swung"
    assert result.swing_ratio == pytest.approx(3.0)


def test_reversed_short_long():
    result = analyze_swing(_seq(_eighth_pairs(1 / 3)))
    assert result.feel == "reversed"
    assert result.swing_ratio == pytest.approx(0.5)


def test_inconsistent_fractions_are_mixed_not_averaged_away():
    notes = []
    for b, frac in enumerate([0.5, 0.75, 0.5, 0.75]):
        notes.append((float(b), frac))
        notes.append((b + frac, 1.0 - frac))
    result = analyze_swing(_seq(notes))
    assert result.feel == "mixed"
    assert result.fraction_stddev > 0.08


# --- evidence discipline ------------------------------------------------------------------


def test_too_few_divisions_raises():
    with pytest.raises(ValueError, match="too little evidence"):
        analyze_swing(_seq(_eighth_pairs(2 / 3, beats=2)))  # 2 < min_divisions 3


def test_three_way_divisions_are_not_swing_pairs():
    # Full triplets: two interior onsets per beat — counted as divided,
    # never as eligible swing evidence.
    notes = []
    for b in range(4):
        for k in range(3):
            notes.append((b + k / 3, 1 / 3))
    with pytest.raises(ValueError, match="too little evidence"):
        analyze_swing(_seq(notes))


def test_divided_vs_eligible_counts_are_evidence():
    notes = _eighth_pairs(2 / 3)  # 4 eligible swing pairs...
    notes += [(4.0, 0.25), (4.25, 0.25), (4.5, 0.5)]  # ...plus one 16th-divided beat
    result = analyze_swing(_seq(notes))
    assert result.eligible_divisions == 4
    assert result.divided_beats == 5
    assert [round(d.fraction, 3) for d in result.divisions] == [0.667] * 4


def test_compound_meter_divisions_measure_against_the_felt_beat():
    # 6/8: beat unit 1.5; interior onsets at 1.0 within each dotted-quarter
    # beat → fraction 2/3 → swung (the lilt *within* the compound beat).
    notes = []
    for start in (0.0, 1.5, 3.0):
        notes.append((start, 1.0))
        notes.append((start + 1.0, 0.5))
    result = analyze_swing(_seq(notes, time_signature=(6, 8)))
    assert result.feel == "swung"
    assert result.mean_fraction == pytest.approx(2 / 3)


def test_multi_voice_requires_an_explicit_voice():
    events = [
        Event(0, 1, Pitch.from_midi(60), voice="a"),
        Event(0, 1, Pitch.from_midi(67), voice="b"),
    ]
    with pytest.raises(ValueError, match="pass voice="):
        analyze_swing(Sequence.from_events(events))


# --- prior plumbing ------------------------------------------------------------------------


def test_priors_load_and_unknown_version_raises():
    priors = load_swing_priors()
    assert priors.version == "swing-feel.1"
    assert priors.min_divisions == 3
    with pytest.raises(ValueError, match="Unknown swing-feel version"):
        load_swing_priors("nope.99")


def test_to_dict_is_json_ready():
    payload = json.loads(json.dumps(analyze_swing(_seq(_eighth_pairs(2 / 3))).to_dict()))
    assert payload["feel"] == "swung"
    assert payload["prior_version"] == "swing-feel.1"
    assert payload["divisions"][0]["fraction"] == pytest.approx(2 / 3)
