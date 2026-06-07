"""Tests for the temporal core: events, sequences, tempo, meter."""

import pytest

from mts.core.bitmask import mask_from_pcs
from mts.core.pitch import Pitch
from mts.temporal import (
    Event,
    MeterChange,
    MeterMap,
    Sequence,
    TempoChange,
    TempoMap,
    TimeSignature,
)


def _ev(midi, onset, dur):
    return Event(onset, dur, Pitch.from_midi(midi))


def _cmaj_then_fmaj() -> Sequence:
    return Sequence.from_events(
        [
            _ev(60, 0, 4), _ev(64, 0, 4), _ev(67, 0, 4),   # C E G, beats 0-4
            _ev(65, 4, 4), _ev(69, 4, 4), _ev(72, 4, 4),   # F A C, beats 4-8
        ],
        bpm=120,
        time_signature=(4, 4),
    )


# --- Event ------------------------------------------------------------------

def test_event_validation():
    with pytest.raises(ValueError):
        Event(-1.0, 1.0, Pitch.from_midi(60))
    with pytest.raises(ValueError):
        Event(0.0, 0.0, Pitch.from_midi(60))


def test_event_half_open_sounding():
    e = _ev(60, 0, 4)
    assert e.sounds_at(0.0)
    assert e.sounds_at(3.99)
    assert not e.sounds_at(4.0)  # offset is exclusive


# --- Sequence ---------------------------------------------------------------

def test_sounding_and_realization_reduce_to_key():
    seq = _cmaj_then_fmaj()
    sounding = seq.sounding_at(2.0)
    assert [e.pitch.midi for e in sounding] == [60, 64, 67]  # low to high
    real = seq.realization_at(2.0)
    assert real is not None
    assert not real.is_rooted  # rootless voicing template
    assert real.reduce_to_key() == mask_from_pcs([0, 4, 7])


def test_realization_is_none_during_silence():
    seq = _cmaj_then_fmaj()
    assert seq.realization_at(8.0) is None


def test_from_events_sorts_by_onset_then_pitch():
    seq = Sequence.from_events([_ev(67, 4, 1), _ev(60, 0, 1), _ev(64, 0, 1)])
    assert [(e.onset, e.pitch.midi) for e in seq.events] == [(0, 60), (0, 64), (4, 67)]


def test_duration_beats_and_seconds():
    seq = _cmaj_then_fmaj()
    assert seq.duration_beats == 8
    assert seq.duration_seconds == 4.0  # 8 quarter beats @ 120bpm = 4s


def test_sequence_is_hashable():
    a = _cmaj_then_fmaj()
    b = _cmaj_then_fmaj()
    assert a == b and hash(a) == hash(b)


# --- Tempo ------------------------------------------------------------------

def test_constant_tempo_seconds():
    tm = TempoMap.constant(120)
    assert tm.seconds_at(0.0) == 0.0
    assert tm.seconds_at(4.0) == 2.0


def test_tempo_change_integrates_piecewise():
    tm = TempoMap((TempoChange(0, 120), TempoChange(4, 60)))
    # 4 beats @120 (2s) + 4 beats @60 (4s) = 6s
    assert tm.seconds_at(8.0) == 6.0
    assert tm.bpm_at(2.0) == 120
    assert tm.bpm_at(5.0) == 60


def test_tempo_map_requires_beat_zero():
    with pytest.raises(ValueError):
        TempoMap((TempoChange(1.0, 120),))


# --- Meter ------------------------------------------------------------------

def test_beats_per_bar():
    assert TimeSignature(4, 4).beats_per_bar == 4.0
    assert TimeSignature(6, 8).beats_per_bar == 3.0
    assert TimeSignature(3, 4).beats_per_bar == 3.0


def test_metric_position_common_time():
    mm = MeterMap.constant(4, 4)
    assert mm.metric_position(0.0).is_downbeat
    p4 = mm.metric_position(4.0)
    assert (p4.bar, p4.beat_in_bar, p4.is_downbeat) == (1, 0.0, True)
    p = mm.metric_position(5.5)
    assert p.bar == 1 and p.beat_in_bar == 1.5 and not p.is_downbeat


def test_metric_position_triple_meter():
    mm = MeterMap.constant(3, 4)
    assert mm.metric_position(3.0).bar == 1  # bar boundary at 3 quarter beats
    assert mm.metric_position(3.0).is_downbeat


def test_meter_change():
    # 2 bars of 4/4 (8 beats), then 3/4
    mm = MeterMap((MeterChange(0, TimeSignature(4, 4)), MeterChange(2, TimeSignature(3, 4))))
    assert mm.metric_position(8.0).bar == 2     # start of the 3/4 section
    assert mm.metric_position(8.0).signature == TimeSignature(3, 4)
    assert mm.metric_position(11.0).bar == 3    # next 3/4 bar (8 + 3)
