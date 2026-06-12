"""Voice identity (Phase 4.6 Workstream 0): Event.voice, MIDI seeding, pair motion."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, voice_motion


def _ev(midi, onset, duration, voice=None):
    return Event(onset, duration, Pitch.from_midi(midi), voice=voice)


def _two_voices(a_notes, b_notes):
    """Each notes list: (midi, onset, duration)."""
    events = [_ev(m, o, d, "a") for m, o, d in a_notes]
    events += [_ev(m, o, d, "b") for m, o, d in b_notes]
    return Sequence.from_events(events)


def _motions(sequence):
    return [(t.motion, t.interval_class_from, t.interval_class_to)
            for t in voice_motion(sequence).transitions]


# --- the voice field -------------------------------------------------------------------


def test_voice_defaults_to_none_for_back_compat():
    event = Event(0.0, 1.0, Pitch.from_midi(60))
    assert event.voice is None


def test_sequence_voices_and_filter():
    seq = _two_voices([(60, 0, 1)], [(67, 0, 1)])
    seq = Sequence.from_events(seq.events + (_ev(72, 0, 1),))  # unvoiced extra
    assert seq.voices() == ("a", "b")  # sorted; unvoiced excluded
    just_a = seq.filter_voice("a")
    assert [e.pitch.midi for e in just_a.events] == [60]
    assert just_a.tempo == seq.tempo and just_a.meter == seq.meter


# --- pair motion classification --------------------------------------------------------


def test_parallel_motion_preserves_interval_class():
    seq = _two_voices([(60, 0, 1), (62, 1, 1)], [(67, 0, 1), (69, 1, 1)])
    assert _motions(seq) == [("parallel", 7, 7)]


def test_compound_intervals_are_parallel_mod_12():
    # P12 → P12: still parallel fifths to the ear and to the rule
    seq = _two_voices([(60, 0, 1), (62, 1, 1)], [(79, 0, 1), (81, 1, 1)])
    assert _motions(seq) == [("parallel", 7, 7)]


def test_similar_contrary_and_oblique():
    similar = _two_voices([(60, 0, 1), (62, 1, 1)], [(67, 0, 1), (72, 1, 1)])
    assert _motions(similar) == [("similar", 7, 10)]
    contrary = _two_voices([(60, 0, 1), (59, 1, 1)], [(67, 0, 1), (69, 1, 1)])
    assert _motions(contrary) == [("contrary", 7, 10)]
    oblique = _two_voices([(60, 0, 2)], [(67, 0, 1), (69, 1, 1)])  # held vs moving
    assert _motions(oblique) == [("oblique", 7, 9)]


def test_static_pairs_make_no_transition():
    seq = _two_voices([(60, 0, 1), (60, 1, 1)], [(67, 0, 1), (67, 1, 1)])
    assert voice_motion(seq).transitions == []


def test_ambiguous_double_stop_makes_no_claim():
    seq = _two_voices([(60, 0, 1), (62, 1, 1)], [(67, 0, 1), (69, 1, 1)])
    seq = Sequence.from_events(seq.events + (_ev(76, 0, 1, "b"),))  # b sounds 2 notes
    assert voice_motion(seq).transitions == []  # b has no single position at beat 0


def test_fewer_than_two_voices_raises():
    with pytest.raises(ValueError, match="two voiced parts"):
        voice_motion(Sequence.from_events([_ev(60, 0, 1, "a"), _ev(67, 0, 1)]))


def test_parallel_fifths_are_a_one_line_filter():
    # The rule itself belongs to the Phase 4.6 DSL; the primitive makes it trivial.
    seq = _two_voices(
        [(60, 0, 1), (62, 1, 1), (64, 2, 1)],
        [(67, 0, 1), (69, 1, 1), (76, 2, 1)],
    )
    result = voice_motion(seq)
    fifths = [t for t in result.transitions
              if t.motion == "parallel" and t.interval_class_to == 7]
    assert [(t.from_beat, t.to_beat) for t in fifths] == [(0.0, 1.0)]


def test_result_is_json_ready():
    seq = _two_voices([(60, 0, 1), (62, 1, 1)], [(67, 0, 1), (69, 1, 1)])
    payload = json.loads(json.dumps(voice_motion(seq).to_dict()))
    assert payload["voices"] == ["a", "b"]
    assert payload["transitions"][0]["motion"] == "parallel"
    assert payload["transitions"][0]["a_from_midi"] == 60


# --- MIDI seeding -----------------------------------------------------------------------


def test_midi_tracks_and_channels_seed_voices(tmp_path):
    mido = pytest.importorskip("mido")
    mid = mido.MidiFile(ticks_per_beat=480)
    for channel, note in ((0, 60), (1, 67)):
        track = mido.MidiTrack()
        track.append(mido.Message("note_on", note=note, velocity=80, channel=channel, time=0))
        track.append(mido.Message("note_off", note=note, velocity=0, channel=channel, time=960))
        mid.tracks.append(track)
    path = tmp_path / "voiced.mid"
    mid.save(path)

    from mts.io.midi import sequence_from_midi_file

    seq = sequence_from_midi_file(str(path))
    assert seq.voices() == ("t0c0", "t1c1")
    assert {e.pitch.midi: e.voice for e in seq.events} == {60: "t0c0", 67: "t1c1"}


def test_note_pairing_stays_within_its_track(tmp_path):
    mido = pytest.importorskip("mido")
    mid = mido.MidiFile(ticks_per_beat=480)
    track0 = mido.MidiTrack()
    track0.append(mido.Message("note_on", note=60, velocity=80, channel=0, time=0))
    track0.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=960))
    track1 = mido.MidiTrack()  # an orphan note_off for the same (channel, note)
    track1.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
    mid.tracks.extend([track0, track1])
    path = tmp_path / "orphan.mid"
    mid.save(path)

    from mts.io.midi import sequence_from_midi_file

    events = sequence_from_midi_file(str(path)).events
    assert len(events) == 1
    assert events[0].duration == pytest.approx(2.0)  # not cut short at beat 1
