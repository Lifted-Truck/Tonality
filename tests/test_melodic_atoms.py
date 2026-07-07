"""Melodic atoms (Phase 4.6 WS0): intervals, contour, approach/departure, NHT typing."""

from __future__ import annotations

import json

import pytest

from mts.core.pitch import Pitch
from mts.temporal import Event, Sequence, analyze_melody
from mts.temporal.melodic import interval_class_name


def _line(midis, *, start=0.0, duration=1.0, voice=None):
    events = [
        Event(start + i * duration, duration, Pitch.from_midi(m), voice=voice)
        for i, m in enumerate(midis)
    ]
    return Sequence.from_events(events)


C_TRIAD = (0.0, 100.0, (0, 4, 7))  # one long C-major-chord span


# --- interval vocabulary ---------------------------------------------------------------


def test_interval_classes_use_the_counterpoint_mapping():
    assert interval_class_name(0) == "unison"
    assert interval_class_name(1) == interval_class_name(-2) == "step"
    assert interval_class_name(3) == interval_class_name(-4) == "skip"
    assert interval_class_name(5) == interval_class_name(-12) == "leap"


def test_intervals_classes_contour_and_ambitus():
    result = analyze_melody(_line([60, 62, 64, 67, 67, 60]))
    assert result.intervals == (2, 2, 3, 0, -7)
    assert result.interval_classes == ("step", "step", "skip", "unison", "leap")
    assert result.parsons_code == "*uuurd"
    assert (result.lowest_midi, result.highest_midi) == (60, 67)
    assert result.ambitus_semitones == 7


def test_approach_and_departure_per_note():
    result = analyze_melody(_line([60, 62, 64]))
    first, middle, last = result.notes
    assert (first.approach_interval, first.departure_interval) == (None, 2)
    assert (middle.approach_class, middle.departure_class) == ("step", "step")
    assert (last.approach_interval, last.departure_interval) == (2, None)


# --- line extraction honesty -----------------------------------------------------------


def test_multi_voice_requires_an_explicit_voice():
    events = [
        Event(0, 1, Pitch.from_midi(60), voice="a"),
        Event(0, 1, Pitch.from_midi(67), voice="b"),
    ]
    seq = Sequence.from_events(events)
    with pytest.raises(ValueError, match="pass voice="):
        analyze_melody(seq)
    solo = analyze_melody(seq, voice="a")
    assert [n.midi for n in solo.notes] == [60]
    with pytest.raises(ValueError, match="not present"):
        analyze_melody(seq, voice="soprano")


def test_overlapping_notes_are_not_a_line():
    seq = Sequence.from_events(
        [Event(0, 2, Pitch.from_midi(60)), Event(1, 2, Pitch.from_midi(62))]
    )
    with pytest.raises(ValueError, match="monophonic"):
        analyze_melody(seq)


def test_empty_sequence_raises():
    with pytest.raises(ValueError, match="at least one event"):
        analyze_melody(Sequence.from_events([]))


# --- NHT typing (harmony-relative, never guessed) ---------------------------------------


def test_no_harmony_means_no_chord_tone_claims():
    result = analyze_melody(_line([60, 62, 64]))
    assert result.harmony_provided is False
    assert all(n.is_chord_tone is None and n.nht_type is None for n in result.notes)


def test_passing_tone():
    result = analyze_melody(_line([60, 62, 64]), harmony=[C_TRIAD])
    types = [(n.is_chord_tone, n.nht_type) for n in result.notes]
    assert types == [(True, None), (False, "passing"), (True, None)]


def test_neighbor_tone():
    result = analyze_melody(_line([60, 62, 60]), harmony=[C_TRIAD])
    assert result.notes[1].nht_type == "neighbor"


def test_appoggiatura_and_escape():
    leap_then_step = analyze_melody(_line([60, 65, 64]), harmony=[C_TRIAD])
    assert leap_then_step.notes[1].nht_type == "appoggiatura"
    step_then_leap = analyze_melody(_line([60, 62, 55]), harmony=[C_TRIAD])
    assert step_then_leap.notes[1].nht_type == "escape"


def test_suspension_anticipation_and_pedal():
    suspension = analyze_melody(_line([62, 62, 60]), harmony=[C_TRIAD])
    assert suspension.notes[1].nht_type == "suspension"
    anticipation = analyze_melody(_line([60, 62, 62]), harmony=[C_TRIAD])
    assert anticipation.notes[1].nht_type == "anticipation"
    pedal = analyze_melody(_line([62, 62, 62]), harmony=[C_TRIAD])
    assert pedal.notes[1].nht_type == "pedal"


def test_edge_notes_without_pattern_are_free():
    result = analyze_melody(_line([62, 64]), harmony=[C_TRIAD])
    assert result.notes[0].nht_type == "free"  # non-chord tone, no approach


def test_note_outside_all_spans_makes_no_claim():
    result = analyze_melody(
        _line([60, 62, 64]), harmony=[(0.0, 1.5, (0, 4, 7))]
    )
    assert result.notes[0].is_chord_tone is True
    assert result.notes[2].is_chord_tone is None  # onset 2.0 is uncovered
    assert result.notes[2].nht_type is None


def test_typing_follows_the_span_under_the_onset():
    # D is a chord tone of G major in the second span, not an NHT of C.
    result = analyze_melody(
        _line([60, 62, 64]),
        harmony=[(0.0, 1.0, (0, 4, 7)), (1.0, 2.0, (7, 11, 2)), (2.0, 3.0, (0, 4, 7))],
    )
    assert [n.is_chord_tone for n in result.notes] == [True, True, True]


def test_bad_harmony_spans_raise():
    with pytest.raises(ValueError, match="no extent"):
        analyze_melody(_line([60]), harmony=[(1.0, 1.0, (0,))])
    with pytest.raises(ValueError, match="no pitch classes"):
        analyze_melody(_line([60]), harmony=[(0.0, 1.0, ())])


# --- output shape ------------------------------------------------------------------------


def test_to_dict_is_json_ready():
    result = analyze_melody(_line([60, 62, 64]), harmony=[C_TRIAD])
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["parsons_code"] == "*uu"
    assert payload["notes"][1]["nht_type"] == "passing"
    assert payload["harmony_provided"] is True
