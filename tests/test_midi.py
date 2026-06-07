"""Tests for MIDI ingestion (io/midi.py) via mido round-trips."""

import pytest

mido = pytest.importorskip("mido")

from mts.io.midi import (  # noqa: E402
    events_from_live_midi,
    events_from_midi_file,
    sequence_from_midi_file,
)


def _write_cmaj(path, *, bpm=120, numerator=4, denominator=4, ticks_per_beat=480):
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    track.append(
        mido.MetaMessage("time_signature", numerator=numerator, denominator=denominator, time=0)
    )
    # C major triad, one beat long (ticks_per_beat ticks).
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_on", note=64, velocity=64, time=0))
    track.append(mido.Message("note_on", note=67, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=ticks_per_beat))
    track.append(mido.Message("note_off", note=64, velocity=0, time=0))
    track.append(mido.Message("note_off", note=67, velocity=0, time=0))
    mid.save(str(path))
    return path


def test_parses_notes_into_events(tmp_path):
    path = _write_cmaj(tmp_path / "c.mid")
    events = events_from_midi_file(path)
    assert sorted(e.pitch.midi for e in events) == [60, 64, 67]
    assert all(e.onset == 0.0 for e in events)
    assert all(e.duration == 1.0 for e in events)  # one beat
    assert all(e.pitch.velocity == 64 for e in events)


def test_reads_tempo_and_meter(tmp_path):
    path = _write_cmaj(tmp_path / "c.mid", bpm=90, numerator=3, denominator=4)
    seq = sequence_from_midi_file(path)
    assert round(seq.tempo.bpm_at(0.0)) == 90
    assert seq.meter.changes[0].signature.beats_per_bar == 3.0


def test_ingested_sequence_reduces_to_identity(tmp_path):
    # The ingested window reduces to the C-major identity (event -> realization
    # -> key). Uses only the temporal core, so this slice stays independent of
    # segmentation.
    path = _write_cmaj(tmp_path / "c.mid")
    seq = sequence_from_midi_file(path)
    real = seq.realization_at(0.5)
    assert real is not None
    assert real.distinct_pcs == (0, 4, 7)


def test_note_on_velocity_zero_counts_as_note_off(tmp_path):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=100, time=0))
    track.append(mido.Message("note_on", note=60, velocity=0, time=480))  # = note_off
    path = tmp_path / "v0.mid"
    mid.save(str(path))
    events = events_from_midi_file(path)
    assert len(events) == 1
    assert events[0].duration == 1.0


def test_tempo_change_is_captured(tmp_path):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(60), time=960))  # at beat 2
    track.append(mido.Message("note_off", note=60, velocity=0, time=0))
    path = tmp_path / "tc.mid"
    mid.save(str(path))
    seq = sequence_from_midi_file(path)
    assert round(seq.tempo.bpm_at(0.0)) == 120
    assert round(seq.tempo.bpm_at(2.0)) == 60


def test_live_midi_not_implemented():
    with pytest.raises(NotImplementedError):
        list(events_from_live_midi(object()))
