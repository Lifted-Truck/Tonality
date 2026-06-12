"""Local key tracking: windowed key induction → key regions (3.5b extension)."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, track_keys


def _chord(midi_notes, onset, duration):
    return [Event(onset, duration, Pitch.from_midi(m)) for m in midi_notes]


def _progression(tonic_midi, start, cycles=1):
    """I–IV–V–I over a tonic pedal in the major key of tonic_midi.

    The pedal keeps every sub-window decisive: a bare V–I window genuinely
    correlates better with the dominant key (surfaced, not smoothed — v1 has
    no hysteresis), so key-defining material must actually define the key.
    """
    events = []
    t = tonic_midi
    for c in range(cycles):
        base = start + 8 * c
        events.append(Event(base, 8, Pitch.from_midi(t - 12)))  # tonic pedal
        events += _chord([t, t + 4, t + 7], base, 2)
        events += _chord([t + 5, t + 9, t + 12], base + 2, 2)
        events += _chord([t + 7, t + 11, t + 14], base + 4, 2)
        events += _chord([t, t + 4, t + 7], base + 6, 2)
    return events


# --- windowed pc weights (the Sequence extension) -------------------------------------


def test_windowed_pc_weights_count_only_the_overlap():
    seq = Sequence.from_events([Event(0, 4, Pitch.from_midi(60))])
    assert seq.pc_weights(2, 6)[0] == pytest.approx(2.0)
    assert seq.pc_weights(2, 6)[1:] == (0.0,) * 11
    assert seq.pc_weights() == seq.pc_weights(None, None)  # default unchanged


# --- single key ------------------------------------------------------------------------


def test_single_key_yields_one_region_matching_global_induction():
    from mts.analysis import infer_key

    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    result = track_keys(seq)
    assert len(result.regions) == 1
    region = result.regions[0]
    assert (region.tonic_pc, region.mode) == (0, "major")
    assert region.start_beats == pytest.approx(0.0)
    assert region.end_beats == pytest.approx(seq.duration_beats)
    best = infer_key(seq).candidates[0]
    assert (best.tonic_pc, best.mode) == (region.tonic_pc, region.mode)


def test_result_cites_parameters_and_profile_version():
    seq = Sequence.from_events(_progression(60, 0, cycles=2))
    result = track_keys(seq, window_beats=4.0, hop_beats=1.0)
    assert result.window_beats == 4.0
    assert result.hop_beats == 1.0
    assert result.profile_version  # same versioned prior as infer_key


# --- modulation ------------------------------------------------------------------------


def test_modulation_splits_into_regions_at_the_key_change():
    # 16 beats of C major, then 16 beats of F# major (a tritone apart).
    events = _progression(60, 0, cycles=2) + _progression(66, 16, cycles=2)
    result = track_keys(Sequence.from_events(events))
    assert (result.regions[0].tonic_pc, result.regions[0].mode) == (0, "major")
    assert (result.regions[-1].tonic_pc, result.regions[-1].mode) == (6, "major")
    # the boundary lands at the change within window resolution
    assert result.regions[0].end_beats == pytest.approx(16.0, abs=4.0)
    assert result.regions[-1].start_beats == pytest.approx(16.0, abs=4.0)
    # regions tile the tracked span without overlap
    for left, right in zip(result.regions, result.regions[1:]):
        assert left.end_beats == pytest.approx(right.start_beats)


def test_regions_carry_seconds_via_the_tempo_map():
    events = _progression(60, 0, cycles=2)
    seq = Sequence.from_events(events, bpm=60.0)  # 1 beat = 1 second
    region = track_keys(seq).regions[0]
    assert region.start_seconds == pytest.approx(region.start_beats)
    assert region.end_seconds == pytest.approx(region.end_beats)


# --- the honesty contract --------------------------------------------------------------


def test_silence_does_not_split_a_key_region():
    # same key on both sides of an 8-beat silence: no evidence != a key change
    events = _progression(60, 0) + _progression(60, 16)
    result = track_keys(Sequence.from_events(events))
    assert len(result.regions) == 1
    assert (result.regions[0].tonic_pc, result.regions[0].mode) == (0, "major")
    # ...but the silent windows are recorded as uninformative evidence
    assert any(not w.is_informative for w in result.windows)


def test_uninformative_everywhere_raises():
    # full chromatic, equal weight: uniform pc content in every window
    events = [Event(0, 4, Pitch.from_midi(60 + i)) for i in range(12)]
    with pytest.raises(ValueError):
        track_keys(Sequence.from_events(events))


def test_empty_sequence_and_bad_geometry_raise():
    seq = Sequence.from_events(_progression(60, 0))
    with pytest.raises(ValueError):
        track_keys(Sequence.from_events([]))
    with pytest.raises(ValueError):
        track_keys(seq, window_beats=0.0)
    with pytest.raises(ValueError):
        track_keys(seq, hop_beats=-1.0)


# --- output shape ----------------------------------------------------------------------


def test_to_dict_is_json_ready_with_window_evidence():
    result = track_keys(Sequence.from_events(_progression(60, 0, cycles=2)))
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["regions"][0]["tonic_pc"] == 0
    assert payload["regions"][0]["window_count"] >= 1
    assert payload["windows"]  # per-window evidence ships with the answer
    assert payload["profile_version"]
