"""Tests for segmentation + harmonic rhythm (the identity stream over time)."""

from mts.core.bitmask import mask_from_pcs
from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, harmonic_rhythm, segment


def _ev(midi, onset, dur):
    return Event(onset, dur, Pitch.from_midi(midi))


def _progression() -> Sequence:
    # C (0-4), F (4-8), G7 (8-12), 4/4 @ 120
    return Sequence.from_events(
        [
            _ev(60, 0, 4), _ev(64, 0, 4), _ev(67, 0, 4),          # C E G
            _ev(65, 4, 4), _ev(69, 4, 4), _ev(72, 4, 4),          # F A C
            _ev(67, 8, 4), _ev(71, 8, 4), _ev(74, 8, 4), _ev(77, 8, 4),  # G B D F
        ],
        bpm=120,
    )


def test_segments_track_the_chord_stream():
    segs = segment(_progression())
    assert [s.pcs for s in segs] == [(0, 4, 7), (0, 5, 9), (2, 5, 7, 11)]
    assert [(s.start, s.end) for s in segs] == [(0, 4), (4, 8), (8, 12)]
    assert segs[0].mask == mask_from_pcs([0, 4, 7])


def test_segment_interprets_to_chord_names():
    segs = segment(_progression())
    names = [(s.interpret().interpretations[0].root_name, s.interpret().interpretations[0].quality) for s in segs]
    assert names == [("C", "maj"), ("F", "maj"), ("G", "7")]


def test_octave_doubling_does_not_split_a_segment():
    seq = Sequence.from_events(
        [_ev(60, 0, 4), _ev(64, 0, 4), _ev(67, 0, 4), _ev(72, 2, 2)],  # +C an octave up
    )
    segs = segment(seq)
    assert len(segs) == 1
    assert segs[0].pcs == (0, 4, 7)


def test_new_pitch_class_splits_a_segment():
    seq = Sequence.from_events(
        [_ev(60, 0, 4), _ev(64, 0, 4), _ev(67, 0, 4), _ev(69, 2, 2)],  # +A (pc 9) mid-span
    )
    segs = segment(seq)
    assert [(s.start, s.end, s.pcs) for s in segs] == [
        (0, 2, (0, 4, 7)),
        (2, 4, (0, 4, 7, 9)),
    ]


def test_silence_is_dropped():
    seq = Sequence.from_events([_ev(60, 0, 1), _ev(64, 4, 1)])  # gap between beats 1 and 4
    segs = segment(seq)
    assert [(s.start, s.end) for s in segs] == [(0, 1), (4, 5)]  # no segment for the rest


def test_empty_sequence_has_no_segments():
    assert segment(Sequence.from_events([])) == []


def test_harmonic_rhythm_metrics():
    hr = harmonic_rhythm(_progression())
    assert hr.segment_count == 3
    assert hr.mean_duration_beats == 4.0
    assert hr.changes_per_bar == 1.0  # 12 beats / 4 (4/4) = 3 bars, 3 changes
    assert hr.mean_duration_seconds == 2.0  # 4 beats @ 120bpm
