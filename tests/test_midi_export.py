"""Phase 2 addendum: MIDI export (Sequence → SMF) and the round-trip invariant."""

import pytest

mido = pytest.importorskip("mido")

from mts.core.pitch import Pitch  # noqa: E402
from mts.io.midi import (  # noqa: E402
    midi_file_from_sequence,
    read_midi_file,
    sequence_from_midi_file,
    sequence_to_midi_file,
)
from mts.temporal import (  # noqa: E402
    Event,
    MeterChange,
    MeterMap,
    Sequence,
    TempoChange,
    TempoMap,
    TimeSignature,
)


def _progression_sequence() -> Sequence:
    """Two bars: C major then F major, with velocity/channel metadata."""
    events = []
    for onset, midis in ((0.0, (60, 64, 67)), (4.0, (53, 65, 69, 72))):
        for m in midis:
            events.append(
                Event(
                    onset=onset,
                    duration=2.0,
                    pitch=Pitch.from_midi(m, velocity=90, channel=1),
                )
            )
    return Sequence.from_events(events, bpm=96.0, time_signature=(4, 4))


def _events_key(sequence: Sequence):
    return [
        (e.onset, e.duration, e.pitch.midi, e.pitch.velocity, e.pitch.channel)
        for e in sequence.events
    ]


def test_round_trip_preserves_events_exactly(tmp_path):
    original = _progression_sequence()
    path = tmp_path / "out.mid"
    sequence_to_midi_file(original, str(path))
    reloaded = sequence_from_midi_file(str(path))
    assert _events_key(reloaded) == _events_key(original)


def test_round_trip_preserves_tempo_and_meter(tmp_path):
    original = Sequence.from_events(
        [Event(onset=float(i), duration=1.0, pitch=Pitch.from_midi(60 + i)) for i in range(8)],
        tempo=TempoMap((TempoChange(0.0, 120.0), TempoChange(4.0, 90.0))),
        meter=MeterMap(
            (MeterChange(0, TimeSignature(4, 4)), MeterChange(1, TimeSignature(3, 4)))
        ),
    )
    path = tmp_path / "maps.mid"
    sequence_to_midi_file(original, str(path))
    reloaded = sequence_from_midi_file(str(path))

    # MIDI stores tempo as integer microseconds per beat, so bpm round-trips
    # to within that quantization (90 -> 666667 µs -> 89.999955 bpm).
    assert [c.beat for c in reloaded.tempo.changes] == [0.0, 4.0]
    assert [c.bpm for c in reloaded.tempo.changes] == pytest.approx([120.0, 90.0], abs=1e-3)
    assert [
        (c.bar, c.signature.numerator, c.signature.denominator)
        for c in reloaded.meter.changes
    ] == [(0, 4, 4), (1, 3, 4)]


def test_default_velocity_and_channel_when_unset(tmp_path):
    original = Sequence.from_events(
        [Event(onset=0.0, duration=1.0, pitch=Pitch.from_midi(60))]
    )
    path = tmp_path / "defaults.mid"
    sequence_to_midi_file(original, str(path))
    event = sequence_from_midi_file(str(path)).events[0]
    assert event.pitch.velocity == 64
    assert event.pitch.channel == 0


def test_restruck_note_at_boundary_round_trips(tmp_path):
    """note_off sorts before note_on at the same tick, so re-struck notes survive."""
    original = Sequence.from_events(
        [
            Event(onset=0.0, duration=1.0, pitch=Pitch.from_midi(60)),
            Event(onset=1.0, duration=1.0, pitch=Pitch.from_midi(60)),
        ]
    )
    path = tmp_path / "restruck.mid"
    sequence_to_midi_file(original, str(path))
    reloaded = sequence_from_midi_file(str(path))
    assert [(e.onset, e.duration) for e in reloaded.events] == [(0.0, 1.0), (1.0, 1.0)]


def test_empty_sequence_writes_and_reads(tmp_path):
    path = tmp_path / "empty.mid"
    sequence_to_midi_file(Sequence.from_events([]), str(path))
    reloaded = sequence_from_midi_file(str(path))
    assert reloaded.events == ()


def test_in_memory_file_has_single_track():
    midi = midi_file_from_sequence(_progression_sequence())
    assert len(midi.tracks) == 1
    assert midi.ticks_per_beat == 480


def test_full_loop_write_analyze(tmp_path):
    """The A2 loop: a Sequence written to disk feeds the analysis pipeline."""
    from mts.mcp.tools import midi_file_analysis

    path = tmp_path / "loop.mid"
    sequence_to_midi_file(_progression_sequence(), str(path))
    result = midi_file_analysis(str(path))
    assert len(result["dataset"]["records"]) == 2
    first = result["dataset"]["records"][0]["analysis"]["naming"]["chosen"]["interpretation"]
    assert (first["root_pc"], first["quality"]) == (0, "maj")


def test_subtick_duration_note_survives_round_trip(tmp_path):
    """#204: a note whose duration quantizes below one tick used to write its own
    note_off before its note_on (invalid SMF) and read back as a dropped, mis-
    classified dangling_note_on. It is now floored to one tick and round-trips."""
    seq = Sequence.from_events([Event(onset=0.0, duration=0.001, pitch=Pitch.from_midi(60))])

    # the emitted bytes: note_on must precede note_off
    midi = midi_file_from_sequence(seq)
    kinds = [m.type for m in midi.tracks[0] if m.type in ("note_on", "note_off")]
    assert kinds == ["note_on", "note_off"]

    path = tmp_path / "subtick.mid"
    sequence_to_midi_file(seq, str(path))
    result = read_midi_file(str(path))
    assert list(result.losses) == []        # no dangling_note_on misclassification
    assert len(result.sequence.events) == 1  # the note is not dropped
    assert result.sequence.events[0].pitch.midi == 60
    assert result.sequence.events[0].duration == pytest.approx(1 / 480)  # floored to one tick


def test_subtick_note_beside_normal_sibling_in_a_chord(tmp_path):
    """The sub-tick note is preserved without corrupting a normal-length sibling
    struck at the same onset (the sibling round-trips exactly; both survive)."""
    seq = Sequence.from_events([
        Event(onset=0.0, duration=0.0005, pitch=Pitch.from_midi(60)),
        Event(onset=0.0, duration=2.0, pitch=Pitch.from_midi(64)),
    ])
    path = tmp_path / "chord.mid"
    sequence_to_midi_file(seq, str(path))
    result = read_midi_file(str(path))
    assert list(result.losses) == []
    durs = {e.pitch.midi: e.duration for e in result.sequence.events}
    assert durs[64] == pytest.approx(2.0)          # normal sibling unchanged
    assert durs[60] == pytest.approx(1 / 480)      # sub-tick floored, still present
